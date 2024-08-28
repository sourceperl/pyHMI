import queue
from threading import Event, Thread
import time
from typing import Any, Dict, List, Optional, Union
import redis
from . import logger
from .Tag import Tag, Device, DataSource
from .Misc import SafeObject


KEY_TYPE = Union[bool, int, float, str, bytes]
KEY_TYPE_CLASS = Union[type(bool), type(int), type(float), type(str), type(bytes)]


def _normalized_for_redis(value: Union[bytes, str]) -> bytes:
    return value.encode() if isinstance(value, str) else value


def _decode_from_redis(raw_data: bytes, type: KEY_TYPE_CLASS) -> KEY_TYPE:
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


def _encode_to_redis(data: KEY_TYPE, type: KEY_TYPE_CLASS) -> bytes:
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
        self.done_evt = Event()
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
        if self.redis_pub.device.connected or (self.redis_pub.device.publish_thread.request_q.qsize() == 0):
            # set an expiration stamp (avoid thread process outdated request)
            self._run_expire = time.monotonic() + self.redis_pub.device.request_cancel_delay
            try:
                self.redis_pub.device.publish_thread.request_q.put_nowait(self)
                self.done_evt.clear()
                return True
            except queue.Full:
                logger.warning(f'redis publish queue full, drop a publish on channel "{self.redis_pub.channel}"')
        # error reporting
        return False


class RedisPublish(DataSource):
    def __init__(self, device: "RedisDevice", channel: Union[bytes, str], type: KEY_TYPE_CLASS) -> None:
        # args
        self.device = device
        self.channel = _normalized_for_redis(channel)
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
        return None

    def set(self, value: KEY_TYPE) -> None:
        try:
            value = _encode_to_redis(value, type=self.type)
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
    def __init__(self, device: "RedisDevice", channel: Union[bytes, str], type: KEY_TYPE_CLASS) -> None:
        # args
        self.device = device
        self.channel = _normalized_for_redis(channel)
        self.type = type
        # public
        self.value: Any = None
        self.last_request: Optional[_PublishRequest] = None
        self.io_error = False
        self.fmt_error = False
        # register RedisSubscribe at device level
        self.subscribe()

    def __repr__(self):
        return f'RedisSubscribe(device={self.device!r}, channel={self.channel!r}, type={self.type.__name__})'

    @property
    def is_subscribe(self) -> bool:
        with self.device.subscribe_thread.safe_subs_d as subs_d:
            return self.channel in subs_d

    def subscribe(self) -> None:
        # register at device level
        with self.device.subscribe_thread.safe_subs_d as subs_d:
            subs_d[self.channel] = self

    def unsubscribe(self) -> None:
        # unregister at device level
        with self.device.subscribe_thread.safe_subs_d as subs_d:
            del subs_d[self.channel]

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
        self.done_evt = Event()
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
        if self.redis_key.device.connected or (self.redis_key.device.key_request_thread.request_q.qsize() == 0):
            # set an expiration stamp (avoid single-update-key thread process outdated request)
            self._run_expire = time.monotonic() + self.redis_key.device.request_cancel_delay
            try:
                self.redis_key.device.key_request_thread.request_q.put_nowait(self)
                self.done_evt.clear()
                return True
            except queue.Full:
                io_op = 'set' if isinstance(self.redis_key, RedisGetKey) else 'get'
                logger.warning(f'redis request key queue full, drop a {io_op} on key "{self.redis_key.name}"')
        # error reporting
        return False


class RedisGetKey(DataSource):
    def __init__(self, device: "RedisDevice", name: Union[bytes, str], type: KEY_TYPE_CLASS,
                 request_cyclic: bool = False) -> None:
        # args
        self.device = device
        self.name = _normalized_for_redis(name)
        self.type = type
        # public
        self.request = _KeyRequest(self, is_cyclic=request_cyclic)
        self.raw_value: Optional[bytes] = None
        self.value: Any = None
        self.io_error = True
        self.fmt_error = False
        # register RedisKey at device level
        with self.device.key_cyclic_thread.safe_keys_l as l:
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
    def __init__(self, device: "RedisDevice", name: Union[bytes, str], type: KEY_TYPE_CLASS,
                 request_cyclic: bool = False, request_on_set: bool = False,
                 ex: Optional[int] = None) -> None:
        # args
        self.device = device
        self.name = _normalized_for_redis(name)
        self.type = type
        self.ex = ex
        # public
        self.request = _KeyRequest(self, is_cyclic=request_cyclic, is_on_set=request_on_set)
        self.raw_value: Optional[bytes] = None
        self.value: Any = None
        self.io_error = True
        # register RedisKey at device level
        with self.device.key_cyclic_thread.safe_keys_l as l:
            l.append(self)

    def __repr__(self):
        return f'RedisSetKey(device={self.device!r}, name={self.name!r}, type={self.type.__name__}, ' \
               f'ex={self.ex})'

    def add_tag(self, tag: Tag) -> None:
        # warn user of type mismatch between initial tag value and this datasource
        if type(tag.init_value) is not self.type:
            raise TypeError(f'init_value must be a {self.type.__name__}')

    def get(self) -> None:
        return None

    def set(self, value: KEY_TYPE) -> None:
        # check type
        try:
            # format raw for redis
            self.raw_value = _encode_to_redis(value, type=self.type)
            # write query executed on set
            if self.request.is_on_set:
                self.request.run()
        except (TypeError, ValueError):
            raise ValueError(f'cannot set redis key {self.name!r} of type {self.type.__name__} to {value!r}')

    def error(self) -> bool:
        return self.io_error

    def sync(self) -> bool:
        return self.request.run()


class _KeyCyclicThread(Thread):
    """ This thread process every I/O for keys on redis DB. """

    def __init__(self, redis_device: "RedisDevice") -> None:
        super().__init__(daemon=True)
        # args
        self.redis_device = redis_device
        # public
        __keys_l: List[Union[RedisGetKey, RedisSetKey]] = list()
        self.safe_keys_l = SafeObject(__keys_l)
        # private
        self._redis_cli = self.redis_device.redis_cli

    def run(self):
        while True:
            # do thread safe copy for this cycle
            with self.safe_keys_l as l:
                keys_l = l.copy()
            # redis i/o keys part
            for key in keys_l:
                if key.request.is_cyclic:
                    try:
                        self.redis_device._set_key(key)
                        self.redis_device._get_key(key)
                    except redis.RedisError as e:
                        logger.warning(f'redis error: {e}')
                        key.io_error = True
            # set connected flag
            try:
                self._connected = self.redis_device.redis_cli.ping()
            except redis.RedisError as e:
                logger.warning(f'redis error: {e}')
                self._connected = False
            # wait before next polling (or not if a write trig wait event)
            time.sleep(self.redis_device.refresh)


class _KeyRequestThread(Thread):
    """ This thread executes all keys get/set from the request queue. """

    def __init__(self, redis_device: "RedisDevice") -> None:
        super().__init__(daemon=True)
        # args
        self.redis_device = redis_device
        # public
        self.request_q: queue.Queue[_KeyRequest] = queue.Queue(maxsize=255)
        # private
        self._redis_cli = self.redis_device.redis_cli

    def run(self):
        while True:
            # wait next request from queue
            key_request = self.request_q.get()
            # process it
            if key_request.is_ready:
                try:
                    self.redis_device._get_key(key_request.redis_key)
                    self.redis_device._set_key(key_request.redis_key)
                except redis.RedisError as e:
                    logger.warning(f'redis error: {e}')
                    key_request.redis_key.io_error = True
            # mark queue task as done
            self.request_q.task_done()


class _PublishThread(Thread):
    """ This thread process every I/O for publish on redis DB. """

    def __init__(self, redis_device: "RedisDevice") -> None:
        super().__init__(daemon=True)
        # args
        self.redis_device = redis_device
        # public
        self.request_q: queue.Queue[_PublishRequest] = queue.Queue(maxsize=255)
        # private
        self._redis_cli = self.redis_device.redis_cli

    def run(self):
        while True:
            # get next publish request from publish io thread queue
            pub_req = self.request_q.get()
            # publish it on redis
            if pub_req.is_ready:
                try:
                    pub_req.msg_delivery_count = self._redis_cli.publish(pub_req.redis_pub.channel, pub_req.message)
                    pub_req.redis_pub.io_error = False
                    pub_req.done_evt.set()
                except redis.RedisError as e:
                    logger.warning(f'redis error: {e}')
                    pub_req.redis_pub.io_error = True
            # mark as done
            self.request_q.task_done()


class _SubscribeThread(Thread):
    """ This thread process every I/O for subscribe on redis DB. """

    def __init__(self, redis_device: "RedisDevice") -> None:
        super().__init__(daemon=True)
        # args
        self.redis_device = redis_device
        # public
        __subscribes_d: Dict[bytes, RedisSubscribe] = {}
        self.safe_subs_d = SafeObject(__subscribes_d)
        # private
        self._redis_cli = self.redis_device.redis_cli
        self._pubsub = self._redis_cli.pubsub()
        self._want_channels_l = []

    def _get_msg_loop(self):
        while True:
            msg_d = self._pubsub.get_message()
            if not msg_d:
                break
            if msg_d['type'] == 'message':
                try:
                    with self.safe_subs_d as subs_d:
                        redis_subscribe = subs_d[msg_d['channel']]
                    redis_subscribe.io_error = False
                    try:
                        redis_subscribe.value = _decode_from_redis(msg_d['data'], type=redis_subscribe.type)
                        redis_subscribe.fmt_error = False
                    except TypeError:
                        redis_subscribe.fmt_error = True
                except KeyError:
                    pass

    def _do_subscribe(self):
        for want_channel in self.want_channels_l:
            if want_channel not in self._pubsub.channels:
                self._pubsub.subscribe(want_channel)

    def _do_unsubscribe(self):
        for subscribed_channel in self._pubsub.channels:
            if subscribed_channel not in self.want_channels_l:
                self._pubsub.unsubscribe(subscribed_channel)

    def run(self):
        # main loop
        while True:
            # load channels list
            with self.safe_subs_d as subs_d:
                self.want_channels_l = subs_d.keys()
            # redis I/O error try
            try:
                # renew the subscriptions if necessary
                if set(self.want_channels_l) != set(self._pubsub.channels):
                    self._do_subscribe()
                    self._do_unsubscribe()
                # get message
                self._get_msg_loop()
            except redis.RedisError as e:
                logger.warning(f'redis error: {e}')
                # set error flags of all RedisSubscribe
                with self.safe_subs_d as subs_d:
                    for redis_subscribe in subs_d.values():
                        redis_subscribe.io_error = True
            # wait next loop
            time.sleep(0.5)


class RedisDevice(Device):
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0,
                 refresh: float = 1.0, request_cancel_delay=5.0,
                 timeout: float = 1.0, client_adv_args: Optional[dict] = None):
        super().__init__()
        # args
        self.host = host
        self.port = port
        self.db = db
        self.refresh = refresh
        self.request_cancel_delay = request_cancel_delay
        self.timeout = timeout
        self.client_adv_args = client_adv_args
        # private
        self._connected = False
        # redis client
        args_d = {} if self.client_adv_args is None else self.client_adv_args
        self.redis_cli = redis.Redis(host=self.host, port=self.port, db=self.db,
                                     socket_timeout=self.timeout, socket_keepalive=True,
                                     decode_responses=False, **args_d)
        # initialize I/O threads
        # keys I/O (cyclic)
        self.key_cyclic_thread = _KeyCyclicThread(self)
        self.key_cyclic_thread.start()
        # keys I/O (request)
        self.key_request_thread = _KeyRequestThread(self)
        self.key_request_thread.start()
        # publish I/O
        self.publish_thread = _PublishThread(self)
        self.publish_thread.start()
        # subscribe I/O
        self.subscribe_thread = _SubscribeThread(self)
        self.subscribe_thread.start()

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
        key.raw_value = self.redis_cli.get(key.name)
        # I/O status
        key.io_error = key.raw_value is None
        # decode RAW value
        if key.raw_value is not None:
            try:
                key.value = _decode_from_redis(key.raw_value, key.type)
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
            set_ret = self.redis_cli.set(key.name, key.raw_value, ex=key.ex)
            key.io_error = set_ret is not True
        # mark request update as done
        key.request.done_evt.set()
