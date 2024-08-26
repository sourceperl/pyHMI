import queue
import threading
import time
from typing import Any, Dict, List, Optional, Union
import redis
from . import logger
from .Tag import Tag, Device, DataSource


KEY_TYPE = Union[bool, int, float, str, bytes]


def _decode_redis_raw(raw_data: bytes, type: type[KEY_TYPE]) -> KEY_TYPE:
    try:
        if type is bool:
            return {b'False': False, b'True': True}[raw_data]
        elif type is bytes:
            return raw_data
        elif type is str:
            return raw_data.decode()
        else:
            return type(raw_data)
    except (KeyError, TypeError, ValueError, UnicodeDecodeError):
        raise TypeError


def _encode_redis_value(data: KEY_TYPE, type: type[KEY_TYPE]) -> bytes:
    if type is bool and isinstance(data, (bool, int)):
        return {False: b'False', True: b'True'}[bool(data)]
    elif type is int and isinstance(data, int):
        return str(data).encode()
    elif type is float and isinstance(data, (int, float)):
        return str(float(data)).encode()
    elif type is str and isinstance(data, str):
        return data.encode()
    elif type is bytes and isinstance(data, str):
        return data.encode()
    elif type is bytes and isinstance(data, bytes):
        return data
    raise TypeError


class _PublishRequest:
    """ A publish request data container for publish io thread queue. """

    def __init__(self, redis_pub: "RedisPublish", message: bytes) -> None:
        # args
        self.redis_pub = redis_pub
        self.message = message
        # public
        self.done_evt = threading.Event()
        self.msg_delivery_count = 0
        # private
        self._run_expire = 0.0

    @property
    def is_expired(self) -> bool:
        return time.monotonic() > self._run_expire

    @property
    def is_ready(self) -> bool:
        # thread process fresh request exclusively
        return not self.is_expired

    def run(self) -> bool:
        """ Attempt immediate update of the key on redis db using the single-update-key thread.

        Any pending execution will be canceled after the delay specified at device level in
        request_cancel_delay (defaults to 5.0 seconds).

        Return True if the request is queued.
        """
        # accept this request when device is actually connected or if the queue is empty
        if self.redis_pub.device.connected or (self.redis_pub.device.publish_request_q.qsize() == 0):
            # set an expiration stamp (avoid thread process outdated request)
            self._run_expire = time.monotonic() + self.redis_pub.device.run_cancel_delay
            try:
                self.redis_pub.device.publish_request_q.put_nowait(self)
                self.done_evt.clear()
                return True
            except queue.Full:
                logger.warning(f'redis publish queue full, drop a publish on channel "{self.redis_pub.channel}"')
        # error reporting
        return False


class RedisPublish(DataSource):
    def __init__(self, device: "RedisDevice", channel: str, type: type[KEY_TYPE]) -> None:
        # args
        self.device = device
        self.channel = channel
        self.type = type
        # public
        self.last_request: Optional[_PublishRequest] = None
        self.io_error = False

    def __repr__(self):
        return f'RedisPublish(device={self.device!r}, channel={self.channel!r}, type={self.type.__name__})'

    def add_tag(self, tag: Tag) -> None:
        # warn user of type mismatch between initial tag value and this datasource
        if not isinstance(tag.init_value, self.type):
            raise TypeError(f'init_value must be a {self.type.__name__}')

    def get(self) -> None:
        raise ValueError(f'cannot read write-only {self!r}')

    def set(self, value: KEY_TYPE) -> None:
        try:
            value = _encode_redis_value(value, type=self.type)
            pub_request = _PublishRequest(self, value)
            if pub_request.run():
                self.last_request = pub_request
            else:
                self.last_request = None
                self.io_error = True
        except TypeError:
            raise TypeError(f'unsupported type for value {self!r}')

    def error(self) -> bool:
        return self.io_error


class RedisSubscribe(DataSource):
    def __init__(self, device: "RedisDevice", channel: str, type: type[KEY_TYPE]) -> None:
        # args
        self.device = device
        self.channel = channel
        self.type = type
        # public
        self.value: Any = None
        self.last_request: Optional[_PublishRequest] = None
        self.io_error = False
        self.fmt_error = False
        # register RedisSubscribe at device level
        self.device.subscribes_add_q.put_nowait(self)

    def __del__(self):
        # unregister RedisSubscribe at device level
        self.device.subscribes_remove_q.put_nowait(self)

    def __repr__(self):
        return f'RedisSubscribe(device={self.device!r}, channel={self.channel!r}, type={self.type.__name__})'

    def add_tag(self, tag: Tag) -> None:
        # warn user of type mismatch between initial tag value and this datasource
        if not isinstance(tag.init_value, self.type):
            raise TypeError(f'init_value must be a {self.type.__name__}')

    def get(self) -> Optional[KEY_TYPE]:
        return self.value

    def set(self, value) -> None:
        raise ValueError(f'cannot write on read-only {self!r}')

    def error(self) -> bool:
        return self.io_error or self.fmt_error


class _KeyRequest:
    """ A get/set request data container for io thread queue. """

    def __init__(self, redis_key: Union["RedisGetKey", "RedisSetKey"], is_cyclic: bool,
                 is_on_set: bool = False) -> None:
        # args
        self.redis_key = redis_key
        self.is_cyclic = is_cyclic
        self.is_on_set = is_on_set
        # public
        self.done_evt = threading.Event()
        # private
        self._run_expire = 0.0

    @property
    def is_expired(self) -> bool:
        return time.monotonic() > self._run_expire

    @property
    def is_ready(self) -> bool:
        # thread process fresh request exclusively
        return not self.is_expired

    def run(self) -> bool:
        """ Attempt immediate update of the key on redis db using the single-update-key thread.

        Any pending execution will be canceled after the delay specified at device level in
        request_cancel_delay (defaults to 5.0 seconds).

        Return True if the request is queued.
        """
        # accept this request when device is actually connected or if the key-update-queue is empty
        if self.redis_key.device.connected or (self.redis_key.device.key_single_request_q.qsize() == 0):
            # set an expiration stamp (avoid single-update-key thread process outdated request)
            self._run_expire = time.monotonic() + self.redis_key.device.run_cancel_delay
            try:
                self.redis_key.device.key_single_request_q.put_nowait(self)
                self.done_evt.clear()
                return True
            except queue.Full:
                io_op = 'set' if isinstance(self.redis_key, RedisGetKey) else 'get'
                logger.warning(f'redis single-update key queue full, drop a {io_op} on key "{self.redis_key.name}"')
        # error reporting
        return False


class RedisGetKey(DataSource):
    def __init__(self, device: "RedisDevice", name: str, type: type[KEY_TYPE],
                 request_cyclic: bool = False) -> None:
        # args
        self.device = device
        self.name = name
        self.type = type
        # public
        self.request = _KeyRequest(self, is_cyclic=request_cyclic)
        self.raw_value: Optional[bytes] = None
        self.value: Any = None
        self.io_error = True
        self.fmt_error = False
        # register RedisKey at device level
        with self.device.keys_l as l:
            l.append(self)

    def __repr__(self):
        return f'RedisGetKey(device={self.device!r}, name={self.name!r}, type={self.type.__name__})'

    def add_tag(self, tag: Tag) -> None:
        # warn user of type mismatch between initial tag value and this datasource
        if not isinstance(tag.init_value, self.type):
            raise TypeError(f'init_value must be a {self.type.__name__}')

    def get(self) -> Optional[KEY_TYPE]:
        return self.value

    def set(self, value) -> None:
        raise ValueError(f'cannot write read-only {self!r}')

    def error(self) -> bool:
        return self.io_error or self.fmt_error

    def sync(self) -> bool:
        return self.request.run()


class RedisSetKey(DataSource):
    def __init__(self, device: "RedisDevice", name: str, type: type[KEY_TYPE],
                 request_cyclic: bool = False, request_on_set: bool = False,
                 ttl: Optional[float] = None) -> None:
        # args
        self.device = device
        self.name = name
        self.type = type
        self.ttl = ttl
        # public
        self.request = _KeyRequest(self, is_cyclic=request_cyclic, is_on_set=request_on_set)
        self.raw_value: Optional[bytes] = None
        self.value: Any = None
        self.io_error = True
        # register RedisKey at device level
        with self.device.keys_l as l:
            l.append(self)

    def __repr__(self):
        return f'RedisSetKey(device={self.device!r}, name={self.name!r}, type={self.type.__name__}, ' \
               f'ttl={self.ttl})'

    def add_tag(self, tag: Tag) -> None:
        # warn user of type mismatch between initial tag value and this datasource
        if type(tag.init_value) is not self.type:
            raise TypeError(f'init_value must be a {self.type.__name__}')

    def get(self) -> Optional[KEY_TYPE]:
        raise ValueError(f'cannot read write-only {self!r}')

    def set(self, value: KEY_TYPE) -> None:
        # check type
        try:
            # format raw for redis
            self.raw_value = _encode_redis_value(value, type=self.type)
            # write query executed on set
            if self.request.is_on_set:
                self.request.run()
        except (TypeError, ValueError):
            raise ValueError(f'cannot set redis key {self.name!r} of type {self.type.__name__} to {value!r}')

    def error(self) -> bool:
        return self.io_error

    def sync(self) -> bool:
        return self.request.run()


class RedisDevice(Device):
    class KeysList:
        def __init__(self):
            self._keys_l: List[Union[RedisGetKey, RedisSetKey]] = list()
            self._lock = threading.Lock()

        def __enter__(self):
            self._lock.acquire()
            return self._keys_l

        def __exit__(self, *args):
            self._lock.release()

    class SubsDict:
        def __init__(self):
            self._subs_d: Dict[str, RedisSubscribe] = dict()
            self._lock = threading.Lock()

        def __enter__(self):
            self._lock.acquire()
            return self._subs_d

        def __exit__(self, *args):
            self._lock.release()

    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0,
                 refresh: float = 1.0, request_cancel_delay=5.0,
                 timeout: float = 1.0, client_adv_args: Optional[dict] = None):
        super().__init__()
        # public vars
        self.host = host
        self.port = port
        self.db = db
        self.refresh = refresh
        self.run_cancel_delay = request_cancel_delay
        self.timeout = timeout
        self.client_adv_args = client_adv_args
        # privates vars
        self.keys_l = RedisDevice.KeysList()
        self.key_single_request_q: queue.Queue[_KeyRequest] = queue.Queue(maxsize=255)
        self.publish_request_q: queue.Queue[_PublishRequest] = queue.Queue(maxsize=255)
        self.subscribes_add_q: queue.Queue[RedisSubscribe] = queue.Queue()
        self.subscribes_remove_q: queue.Queue[RedisSubscribe] = queue.Queue()
        # redis client
        args_d = {} if self.client_adv_args is None else self.client_adv_args
        self.cli = redis.Redis(host=self.host, port=self.port, db=self.db,
                               socket_timeout=self.timeout, socket_keepalive=True,
                               decode_responses=False, **args_d)
        self._connected = False
        # start threads
        self._key_cyclic_th = threading.Thread(target=self._cyclic_update_key_thread, daemon=True)
        self._key_single_th = threading.Thread(target=self._single_update_key_thread, daemon=True)
        self._publish_th = threading.Thread(target=self._publish_thread, daemon=True)
        self._subscribe_th = threading.Thread(target=self._subscribe_thread, daemon=True)
        self._key_cyclic_th.start()
        self._key_single_th.start()
        self._publish_th.start()
        self._subscribe_th.start()

    def __repr__(self):
        return f'RedisDevice(host={self.host!r}, port={self.port}, db={self.db}, refresh={self.refresh:.1f}, ' \
               f'timeout={self.timeout:.1f}, client_adv_args={self.client_adv_args})'

    @property
    def connected(self):
        return self._connected

    def _get_key(self, key: Union[RedisGetKey, RedisSetKey]) -> None:
        # skip other keys
        if not isinstance(key, RedisGetKey):
            return
        # redis I/O
        key.raw_value = self.cli.get(key.name)
        # I/O status
        key.io_error = key.raw_value is None
        # decode RAW value
        if key.raw_value is not None:
            try:
                key.value = _decode_redis_raw(key.raw_value, key.type)
                key.fmt_error = False
            except TypeError:
                key.fmt_error = True
        # mark request update as done
        key.request.done_evt.set()

    def _set_key(self, key: Union[RedisGetKey, RedisSetKey]) -> None:
        # skip other keys
        if not isinstance(key, RedisSetKey):
            return
        # redis I/O
        if key.raw_value is not None:
            set_ret = self.cli.set(key.name, key.raw_value, ex=key.ttl)
            key.io_error = set_ret is True
        # mark request update as done
        key.request.done_evt.set()

    def _cyclic_update_key_thread(self):
        """ Process every I/O for keys on redis DB. """
        while True:
            # do thread safe copy for this cycle
            with self.keys_l as l:
                keys_l = l.copy()
            # redis i/o keys part
            for key in keys_l:
                if key.request.is_cyclic:
                    try:
                        self._set_key(key)
                        self._get_key(key)
                    except redis.RedisError:
                        key.io_error = True
            # set connected flag
            try:
                self._connected = self.cli.ping()
            except redis.RedisError:
                self._connected = False
            # wait before next polling (or not if a write trig wait event)
            time.sleep(self.refresh)

    def _single_update_key_thread(self):
        """ This thread executes all keys get/set from the single-update queue. """
        while True:
            # wait next request from queue
            key_request = self.key_single_request_q.get()
            # process it
            if key_request.is_ready:
                try:
                    self._get_key(key_request.redis_key)
                    self._set_key(key_request.redis_key)
                except redis.RedisError:
                    key_request.redis_key.io_error = True
            # mark queue task as done
            self.key_single_request_q.task_done()

    def _publish_thread(self):
        """ Process every I/O for publish on redis DB. """
        while True:
            # get next publish request from publish io thread queue
            pub_req = self.publish_request_q.get()
            # publish it on redis
            if pub_req.is_ready:
                try:
                    pub_req.msg_delivery_count = self.cli.publish(pub_req.redis_pub.channel, pub_req.message)
                    pub_req.redis_pub.io_error = False
                    pub_req.done_evt.set()
                except redis.RedisError:
                    pub_req.redis_pub.io_error = True
            # mark as done
            self.publish_request_q.task_done()

    def _subscribe_thread(self):
        """ Process every I/O for subscribe on redis DB. """
        # init thread vars
        subscribe_l: List[str] = []
        unsubscribe_l: List[str] = []
        redis_subscribe_d: Dict[str, RedisSubscribe] = {}
        # create a PubSub object to subscribe to channel(s)
        pubsub = self.cli.pubsub()
        # main loop
        while True:
            # process subscription request
            try:
                redis_subscribe = self.subscribes_add_q.get_nowait()
                redis_subscribe_d[redis_subscribe.channel] = redis_subscribe
                subscribe_l.append(redis_subscribe.channel)
                self.subscribes_add_q.task_done()
            except queue.Empty:
                pass
            # process unsubscription request
            try:
                redis_subscribe = self.subscribes_remove_q.get_nowait()
                del redis_subscribe_d[redis_subscribe.channel]
                unsubscribe_l.append(redis_subscribe.channel)
                self.subscribes_remove_q.task_done()
            except queue.Empty:
                pass
            # redis I/O error try
            try:
                # subscribe
                for channel in subscribe_l:
                    pubsub.subscribe(channel)
                    subscribe_l.remove(channel)
                # unsubscribe
                for channel in unsubscribe_l:
                    pubsub.unsubscribe(channel)
                    unsubscribe_l.remove(channel)
                # get_message loop
                while True:
                    msg_d = pubsub.get_message()
                    if not msg_d:
                        break
                    if msg_d['type'] == 'message':
                        try:
                            redis_subscribe = redis_subscribe_d[msg_d['channel'].decode()]
                            redis_subscribe.io_error = False
                            try:
                                redis_subscribe.value = _decode_redis_raw(msg_d['data'], type=redis_subscribe.type)
                                redis_subscribe.fmt_error = False
                            except TypeError:
                                redis_subscribe.fmt_error = True
                        except (KeyError, UnicodeDecodeError):
                            pass
                time.sleep(0.5)
            except redis.RedisError as e:
                # set error flag
                for _, redis_subscribe in redis_subscribe_d.items():
                    redis_subscribe.io_error = True
                # wait before reconnect
                time.sleep(1.0)
