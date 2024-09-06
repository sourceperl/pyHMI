import logging
import queue
import time
from threading import Event, Lock, Thread
from typing import Any, Optional, Set, Union
from weakref import WeakValueDictionary

import redis

from .Misc import TTL, SafeObject
from .Tag import DataSource, Device, Tag

logger = logging.getLogger(__name__)


# some constants
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


class RedisDS(DataSource):
    pass


class RedisPublish(RedisDS):
    class Message:
        """ A message data container for publish with io thread queue. """

        def __init__(self, redis_pub: "RedisPublish", message: bytes) -> None:
            # args
            self.redis_pub = redis_pub
            self.message = message
            # public
            self.ttl = TTL(self.redis_pub.device.cancel_delay)
            self.send_evt = Event()
            self.delivery_count = 0

    def __init__(self, device: "RedisDevice", channel: Union[bytes, str], type: KEY_TYPE_CLASS) -> None:
        # args
        self.device = device
        self.channel = _normalized_for_redis(channel)
        self.type = type
        # public
        self.last_message: Optional[RedisPublish.Message] = None
        self.io_error = False

    def __repr__(self):
        return f'RedisPublish(device={self.device!r}, channel={self.channel!r}, type={self.type.__name__})'

    def _send_msg(self, message: bytes) -> bool:
        """ Attempt to publish message on redis.

        Any pending execution will be canceled after the delay specified at device level in
        cancel_delay (defaults to 5.0 seconds).

        Return True if the query is queued.
        """
        # accept this request when device is actually connected or if the queue is empty
        if self.device.connected or (self.device.publish_thread.msg_q.qsize() == 0):
            try:
                pub_message = RedisPublish.Message(self, message)
                self.device.publish_thread.msg_q.put_nowait(pub_message)
                self.last_message = pub_message
                return True
            except queue.Full:
                logger.warning(f'message queue full: drop publish on channel "{self.channel}"')
        self.last_message = None
        self.io_error = True
        # error reporting
        return False

    def add_tag(self, tag: Tag) -> None:
        # warn user of type mismatch between initial tag value and this datasource
        if not isinstance(tag.init_value, self.type):
            raise TypeError(f'init_value must be a {self.type.__name__}')

    def get(self) -> None:
        return None

    def set(self, value: KEY_TYPE) -> None:
        try:
            self._send_msg(_encode_to_redis(value, type=self.type))
        except TypeError:
            raise TypeError(f'unsupported type for value {self!r}')

    def error(self) -> bool:
        return self.io_error


class RedisSubscribe(RedisDS):
    def __init__(self, device: "RedisDevice", channel: Union[bytes, str], type: KEY_TYPE_CLASS) -> None:
        # args
        self.device = device
        self.channel = _normalized_for_redis(channel)
        self.type = type
        # public
        self.value: Any = None
        self.io_error = False
        self.fmt_error = False
        self.subscribe_evt = Event()
        self.receive_evt = Event()
        # reference this in I/O thread
        self.device.subscribe_thread.add_subscribe(self)

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


class RedisGetKey(RedisDS):
    class SyncReq:
        """ A get request data container for io thread queue. """

        def __init__(self, redis_key: "RedisGetKey") -> None:
            # args
            self.redis_key = redis_key
            # public
            self.ttl = TTL(self.redis_key.device.cancel_delay)

    def __init__(self, device: "RedisDevice", name: Union[bytes, str], type: KEY_TYPE_CLASS,
                 cyclic: bool = False) -> None:
        # args
        self.device = device
        self.name = _normalized_for_redis(name)
        self.type = type
        self.cyclic = cyclic
        # public
        self.is_sync_evt = Event()
        self.raw_value: Optional[bytes] = None
        self.value: Any = None
        self.io_error = True
        self.fmt_error = False
        # reference this in thread I/O
        self.device.key_cyclic_thread.add_key(self)

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
        """ Try to sync key value with redis.

        Any pending execution will be canceled after the delay specified at device level in
        cancel_delay (defaults to 5.0 seconds).

        Return True if the sync request is queued.
        """
        # accept this request when device is actually connected or if the key-update-queue is empty
        if self.device.connected or (self.device.key_sync_thread.sync_req_q.qsize() == 0):
            # set an expiration stamp (avoid single-update-key thread process outdated request)
            try:
                self.device.key_sync_thread.sync_req_q.put_nowait(RedisGetKey.SyncReq(self))
                self.is_sync_evt.clear()
                return True
            except queue.Full:
                logger.warning(f'sync request key queue full: drop a get on key "{self.name}"')
        # error reporting
        return False


class RedisSetKey(RedisDS):
    class SyncReq:
        """ A set request data container for io thread queue. """

        def __init__(self, redis_key: "RedisSetKey") -> None:
            # args
            self.redis_key = redis_key
            # public
            self.ttl = TTL(self.redis_key.device.cancel_delay)

    def __init__(self, device: "RedisDevice", name: Union[bytes, str], type: KEY_TYPE_CLASS,
                 cyclic: bool = False, on_set: bool = False,
                 ex: Optional[int] = None) -> None:
        # args
        self.device = device
        self.name = _normalized_for_redis(name)
        self.type = type
        self.cyclic = cyclic
        self.on_set = on_set
        self.ex = ex
        # public
        self.is_sync_evt = Event()
        self.raw_value: Optional[bytes] = None
        self.value: Any = None
        self.io_error = True
        # reference this in I/O thread
        self.device.key_cyclic_thread.add_key(self)

    def __repr__(self):
        return f'RedisSetKey(device={self.device!r}, name={self.name!r}, type={self.type.__name__}, ' \
               f'ex={self.ex})'

    def add_tag(self, tag: Tag) -> None:
        # warn user of type mismatch between initial tag value and this datasource
        if type(tag.init_value) is not self.type:
            raise TypeError(f'init_value must be a {self.type.__name__}')

    def get(self) -> None:
        # the tag will return the last valid value
        return None

    def set(self, value: KEY_TYPE) -> None:
        # check type
        try:
            # format raw for redis
            self.raw_value = _encode_to_redis(value, type=self.type)
            # write query executed on set
            if self.on_set:
                self.sync()
        except (TypeError, ValueError):
            raise ValueError(f'cannot set redis key {self.name!r} of type {self.type.__name__} to {value!r}')

    def error(self) -> bool:
        return self.io_error

    def sync(self) -> bool:
        """ Attempt immediate update of the key on redis db using the request key thread.

        Any pending execution will be canceled after the delay specified at device level in
        cancel_delay (defaults to 5.0 seconds).

        Return True if the request is queued.
        """
        # accept this request when device is actually connected or if the key-update-queue is empty
        if self.device.connected or (self.device.key_sync_thread.sync_req_q.qsize() == 0):
            try:
                self.device.key_sync_thread.sync_req_q.put_nowait(RedisSetKey.SyncReq(self))
                self.is_sync_evt.clear()
                return True
            except queue.Full:
                logger.warning(f'sync request key queue full: drop a set on key "{self.name}"')
        # error reporting
        return False


class _KeyCyclicThread(Thread):
    """ This thread process every I/O for keys on redis DB. """

    def __init__(self, redis_device: "RedisDevice") -> None:
        super().__init__(daemon=True)
        # args
        self.redis_device = redis_device
        # private
        self._key_d_lock = Lock()
        self._key_d: WeakValueDictionary[int, Union[RedisGetKey, RedisSetKey]] = WeakValueDictionary()
        self._key_d_pos = 0

    def add_key(self, redis_key: Union[RedisGetKey, RedisSetKey]):
        with self._key_d_lock:
            self._key_d[self._key_d_pos] = redis_key
            self._key_d_pos += 1

    def run(self):
        # thread loop
        while True:
            # prevent request dictionnary change during iteration
            with self._key_d_lock:
                cp_key_d = self._key_d.copy()
            # iterate over all keys
            for redis_key in cp_key_d.values():
                if redis_key.cyclic:
                    try:
                        self.redis_device._get_key(redis_key)
                        self.redis_device._set_key(redis_key)
                    except redis.RedisError:
                        redis_key.io_error = True
            # set connected flag
            try:
                self._connected = self.redis_device.redis_cli.ping()
            except redis.RedisError as e:
                self._connected = False
                logger.warning(f'redis error: {e}')
                time.sleep(1.0)


class _KeySyncReqThread(Thread):
    """ This thread executes all keys get/set from the sync request queue. """

    def __init__(self, redis_device: "RedisDevice") -> None:
        super().__init__(daemon=True)
        # args
        self.redis_device = redis_device
        # public
        self.sync_req_q: queue.Queue[Union[RedisGetKey.SyncReq, RedisSetKey.SyncReq]] = queue.Queue(maxsize=255)
        # private
        self._redis_cli = self.redis_device.redis_cli

    def run(self):
        while True:
            # wait next request from queue
            sync_req = self.sync_req_q.get()
            # process it (reject an outdated request)
            if sync_req.ttl.is_not_expired:
                try:
                    self.redis_device._get_key(sync_req.redis_key)
                    self.redis_device._set_key(sync_req.redis_key)
                except redis.RedisError as e:
                    sync_req.redis_key.io_error = True
            else:
                sync_req.redis_key.io_error = True
            # mark sync as done
            sync_req.redis_key.is_sync_evt.set()
            # mark queue task as done
            self.sync_req_q.task_done()


class _PublishThread(Thread):
    """ This thread process every I/O for publish on redis DB. """

    def __init__(self, redis_device: "RedisDevice") -> None:
        super().__init__(daemon=True)
        # args
        self.redis_device = redis_device
        # public
        self.msg_q: queue.Queue[RedisPublish.Message] = queue.Queue(maxsize=255)
        # private
        self._redis_cli = self.redis_device.redis_cli

    def run(self):
        while True:
            # get next publish request from publish io thread queue
            msg = self.msg_q.get()
            # publish it on redis
            if not msg.ttl.is_expired:
                try:
                    msg.delivery_count = self._redis_cli.publish(msg.redis_pub.channel, msg.message)
                    msg.redis_pub.io_error = False
                    msg.send_evt.set()
                except redis.RedisError as e:
                    msg.redis_pub.io_error = True
                    logger.warning(f'redis error: {e}')
                    time.sleep(1.0)
            # mark as done
            self.msg_q.task_done()


class _SubscribeThread(Thread):
    """ This thread process every I/O for subscribe on redis DB. """

    def __init__(self, redis_device: "RedisDevice") -> None:
        super().__init__(daemon=True)
        # args
        self.redis_device = redis_device
        # private
        self._reload_evt = Event()
        _subscribes_d: WeakValueDictionary[bytes, RedisSubscribe] = WeakValueDictionary()
        self._safe_subs_d = SafeObject(_subscribes_d)
        self._pubsub = self.redis_device.redis_cli.pubsub()

    def add_subscribe(self, redis_subscribe: RedisSubscribe):
        with self._safe_subs_d as subs_d:
            subs_d[redis_subscribe.channel] = redis_subscribe
        self._reload_evt.set()

    def _do_subscribe(self, channel: bytes) -> None:
        # debug
        logger.debug(f'subscribe to {channel}')
        # send subscribe to redis server
        self._pubsub.subscribe(channel)
        # notify RedisSubscribe
        try:
            with self._safe_subs_d as subs_d:
                subs_d[channel].subscribe_evt.set()
        except KeyError:
            pass

    def _do_unsubscribe(self, channel: bytes) -> None:
        # debug
        logger.debug(f'unsubscribe from {channel}')
        # send unsubscribe to redis server
        self._pubsub.unsubscribe(channel)

    def _process_pending_msg(self, wait_s: float = 0.0) -> None:
        # get message from inbox
        msg_d = self._pubsub.get_message(timeout=wait_s)
        # skip when inbox is clear
        if not msg_d:
            return
        # process new message
        if msg_d['type'] == 'message':
            # debug
            logger.debug(f'rx pub message: {msg_d}')
            # update RedisSubcribe with new rx data
            try:
                with self._safe_subs_d as subs_d:
                    redis_subscribe = subs_d[msg_d['channel']]
                redis_subscribe.io_error = False
                redis_subscribe.receive_evt.set()
                # decode payload
                try:
                    redis_subscribe.value = _decode_from_redis(msg_d['data'], type=redis_subscribe.type)
                    redis_subscribe.fmt_error = False
                except TypeError:
                    redis_subscribe.fmt_error = True
            except KeyError:
                pass

    def run(self):
        # init thread var(s)
        want_channels_s: Set[bytes] = set()
        # thread loop
        while True:
            #  thread will block here until a first (or another one) subscribe is set
            if self._reload_evt.wait():
                # reset reload event
                self._reload_evt.clear()
                # do a thread safe copy of wanted channels
                with self._safe_subs_d as subs_d:
                    want_channels_s = set(subs_d.keys())
            # redis I/O jobs (on redis error: restart here)
            while not self._reload_evt.is_set():
                try:
                    # subscribe/unsubscribe
                    sub_channels_s = set(self._pubsub.channels)
                    for channel in want_channels_s.difference(sub_channels_s):
                        self._do_subscribe(channel)
                    for channel in sub_channels_s.difference(want_channels_s):
                        self._do_unsubscribe(channel)
                    # process all pending messages (exit on reload event)
                    while not self._reload_evt.is_set():
                        self._process_pending_msg(wait_s=0.2)
                except redis.RedisError as e:
                    # set error flags of all RedisSubscribe
                    with self._safe_subs_d as subs_d:
                        for redis_subscribe in subs_d.values():
                            redis_subscribe.io_error = True
                    # warn user
                    logger.warning(f'redis error: {e}')
                    # wait before next db try
                    time.sleep(1.0)


class RedisDevice(Device):
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0,
                 refresh: float = 1.0, cancel_delay=5.0, timeout: float = 1.0,
                 client_adv_args: Optional[dict] = None):
        super().__init__()
        # args
        self.host = host
        self.port = port
        self.db = db
        self.refresh = refresh
        self.cancel_delay = cancel_delay
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
        self.key_sync_thread = _KeySyncReqThread(self)
        self.key_sync_thread.start()
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

    def _get_key(self, redis_key: Union[RedisGetKey, RedisSetKey]) -> None:
        # skip other keys
        if not isinstance(redis_key, RedisGetKey):
            return
        # redis I/O
        redis_key.raw_value = self.redis_cli.get(redis_key.name)
        redis_key.io_error = redis_key.raw_value is None
        # debug
        logger.debug(f'get key {redis_key.name}')
        # decode RAW value
        if redis_key.raw_value is not None:
            try:
                redis_key.value = _decode_from_redis(redis_key.raw_value, redis_key.type)
                redis_key.fmt_error = False
            except TypeError:
                redis_key.fmt_error = True

    def _set_key(self, redis_key: Union[RedisGetKey, RedisSetKey]) -> None:
        # skip other keys
        if not isinstance(redis_key, RedisSetKey):
            return
        # skip null value
        if redis_key.raw_value is None:
            return
        # redis I/O
        set_ret = self.redis_cli.set(redis_key.name, redis_key.raw_value, ex=redis_key.ex)
        redis_key.io_error = set_ret is not True
        # debug
        logger.debug(f'set key {redis_key.name} to {redis_key.raw_value}')
