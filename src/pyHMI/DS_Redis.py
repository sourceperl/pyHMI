import queue
import threading
import time
from typing import Any, List, Optional, Union
import redis
from . import logger
from .Tag import Tag, Device, DataSource
from .Misc import SafeObject


class RedisPub(DataSource):
    class Request:
        """ A publish request data container for publish io thread queue. """

        def __init__(self, redis_pub: "RedisPub", message: Union[str, bytes]) -> None:
            # args
            self.redis_pub = redis_pub
            self.message = message
            # public
            self.expire = time.monotonic() + self.redis_pub.device.request_cancel_delay
            # clear event
            self.redis_pub.request_done_evt.clear()

        @property
        def is_expired(self) -> bool:
            return time.monotonic() > self.expire

        @property
        def is_ready(self) -> bool:
            # thread process fresh request exclusively
            return not self.is_expired

    def __init__(self, device: "RedisDevice", channel: str) -> None:
        # args
        self.device = device
        self.channel = channel
        # error flags
        self.io_error = False
        # event
        self.request_done_evt = threading.Event()

    def __repr__(self):
        return f'RedisPub(device={self.device!r}, channel={self.channel!r})'

    def get(self) -> None:
        raise ValueError(f'cannot read write-only {self!r}')

    def set(self, value: Union[str, bytes]) -> None:
        try:
            self.device.publish_request_q.put(RedisPub.Request(self, value), block=False)
        except queue.Full:
            self.io_error = True

    def error(self) -> bool:
        return self.io_error


class RedisKey(DataSource):
    KEY_TYPE = Union[bool, int, float, str, bytes]

    class Request:
        """ A get/set request data container for io thread queue. """

        def __init__(self, redis_key: "RedisKey") -> None:
            # args
            self.redis_key = redis_key
            # public
            self.expire = time.monotonic() + self.redis_key.device.request_cancel_delay
            # clear event
            self.redis_key.request_done_evt.clear()

        @property
        def is_expired(self) -> bool:
            return time.monotonic() > self.expire

        @property
        def is_ready(self) -> bool:
            # thread process fresh request exclusively
            return not self.is_expired

    def __init__(self, device: "RedisDevice", name: str, type: type[bool | int | float | str | bytes],
                 write: bool = False, update_cyclic: bool = False, update_on_set: bool = False,
                 ttl: Optional[float] = None) -> None:
        # args
        self.device = device
        self.name = name
        self.type = type
        self.write = write
        self.update_cyclic = update_cyclic
        self.update_on_set = update_on_set
        self.ttl = ttl
        # public
        self.raw_value: Optional[bytes] = None
        self.value: Any = None
        self.io_error = True
        self.fmt_error = False
        self.request_done_evt = threading.Event()
        # register RedisKey at device level
        with self.device.keys_l as l:
            l.append(self)

    def __repr__(self):
        return f'RedisKey(device={self.device!r}, name={self.name!r}, type={self.type.__name__}, ' \
               f'ttl={self.ttl}, writable={self.write})'

    def add_tag(self, tag: Tag) -> None:
        # warn user of type mismatch between initial tag value and this datasource
        if type(tag.init_value) is not self.type:
            raise TypeError(f'init_value must be a {self.type.__name__}')

    def get(self) -> Optional[KEY_TYPE]:
        # check read-only
        if self.write:
            raise ValueError(f'cannot read write-only {self!r}')
        return self.value

    def set(self, value: KEY_TYPE) -> None:
        # check write-only
        if not self.write:
            raise ValueError(f'cannot write read-only {self!r}')
        # check type
        try:
            # format raw for redis
            if self.type is bytes:
                if isinstance(value, bytes):
                    self.raw_value = value
                else:
                    raise TypeError
            else:
                self.raw_value = str(self.type.__call__(value)).encode()
            # write query executed on set
            if self.update_on_set:
                self.update()
        except (TypeError, ValueError):
            raise ValueError(f'cannot set redis key {self.name!r} of type {self.type.__name__} to {value!r}')

    def error(self) -> bool:
        return self.io_error or self.fmt_error

    def update(self) -> bool:
        """ Attempt immediate update of the key on redis db using the single-update-key thread.

        Any pending execution will be canceled after the delay specified at device level in
        request_cancel_delay (defaults to 5.0 seconds).

        Return True if the request is queued.
        """
        # accept this request when device is actually connected or if the key-update-queue is empty
        if self.device.connected or (self.device.key_request_q.qsize() == 0):
            # set an expiration stamp (avoid single-update-key thread process outdated request)
            self._update_request_expire = time.monotonic() + self.device.request_cancel_delay
            try:
                self.device.key_request_q.put_nowait(RedisKey.Request(self))
                self.request_done_evt.clear()
                return True
            except queue.Full:
                io_op = 'write' if self.write else 'read'
                logger.warning(f'redis single-update key queue full, drop {io_op} on key "{self.name}"')
        # error reporting
        return False


class RedisDevice(Device):
    class KeyList:
        def __init__(self):
            self._keys_l: List[RedisKey] = list()
            self._lock = threading.Lock()

        def __enter__(self):
            self._lock.acquire()
            return self._keys_l

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
        self.request_cancel_delay = request_cancel_delay
        self.timeout = timeout
        self.client_adv_args = client_adv_args
        # privates vars
        self.keys_l = RedisDevice.KeyList()
        self.publish_request_q: queue.Queue[RedisPub.Request] = queue.Queue(maxsize=255)
        self.key_request_q: queue.Queue[RedisKey.Request] = queue.Queue(maxsize=255)
        # redis client
        args_d = {} if self.client_adv_args is None else self.client_adv_args
        self.safe_cli = SafeObject(redis.Redis(host=self.host, port=self.port, db=self.db,
                                               socket_timeout=self.timeout, socket_keepalive=True,
                                               decode_responses=False, **args_d))
        self._connected = False
        # start threads
        self._key_cyclic_th = threading.Thread(target=self._cyclic_update_key_thread, daemon=True)
        self._key_single_th = threading.Thread(target=self._single_update_key_thread, daemon=True)
        self._publish_th = threading.Thread(target=self._publish_thread, daemon=True)
        self._key_cyclic_th.start()
        self._key_single_th.start()
        self._publish_th.start()

    def __repr__(self):
        return f'RedisDevice(host={self.host!r}, port={self.port}, db={self.db}, refresh={self.refresh:.1f}, ' \
               f'timeout={self.timeout:.1f}, client_adv_args={self.client_adv_args})'

    @property
    def connected(self):
        return self._connected

    def _get_key(self, key: RedisKey) -> None:
        # skip write key
        if key.write:
            return
        # redis I/O
        with self.safe_cli as cli:
            key.raw_value = cli.get(key.name)
        # I/O status
        key.io_error = key.raw_value is None
        # decode RAW value
        if key.raw_value is not None:
            if key.type is bool:
                try:
                    key.value = {b'False': False, b'True': True}[key.raw_value]
                    key.fmt_error = False
                except KeyError:
                    key.fmt_error = True
            elif key.type is str:
                try:
                    key.value = key.raw_value.decode()
                    key.fmt_error = False
                except UnicodeDecodeError:
                    key.fmt_error = True
            else:
                try:
                    key.value = key.type(key.raw_value)
                    key.fmt_error = False
                except:
                    key.fmt_error = True
        # mark request update as done
        key.request_done_evt.set()

    def _set_key(self, key: RedisKey) -> None:
        # skip read key
        if not key.write:
            return
        # redis I/O
        if key.raw_value is not None:
            with self.safe_cli as cli:
                set_ret = cli.set(key.name, key.raw_value, ex=key.ttl)
            key.io_error = set_ret is True
        # mark request update as done
        key.request_done_evt.set()

    def _cyclic_update_key_thread(self):
        """ Process every I/O for keys on redis DB. """
        while True:
            # do thread safe copy for this cycle
            with self.keys_l as l:
                keys_l = l.copy()
            # redis i/o keys part
            for key in keys_l:
                if key.update_cyclic:
                    try:
                        self._set_key(key)
                        self._get_key(key)
                    except redis.RedisError:
                        key.io_error = True
            # set connected flag
            try:
                with self.safe_cli as cli:
                    self._connected = cli.ping()
            except redis.RedisError:
                self._connected = False
            # wait before next polling (or not if a write trig wait event)
            time.sleep(self.refresh)

    def _single_update_key_thread(self):
        """ This thread executes all keys get/set from the single-update queue. """
        while True:
            # wait next request from queue
            key_request = self.key_request_q.get()
            # log it
            logger.debug(f'{threading.current_thread().name} receive {key_request}')
            # process it
            if key_request.is_ready:
                try:
                    self._get_key(key_request.redis_key)
                    self._set_key(key_request.redis_key)
                except redis.RedisError:
                    key_request.redis_key.io_error = True
            # mark queue task as done
            self.key_request_q.task_done()

    def _publish_thread(self):
        """ Process every I/O for publish on redis DB. """
        while True:
            # get next publish request from publish io thread queue
            pub_request = self.publish_request_q.get()
            # publish it on redis
            if pub_request.is_ready:
                try:
                    with self.safe_cli as cli:
                        cli.publish(pub_request.redis_pub.channel, pub_request.message)
                    pub_request.redis_pub.io_error = False
                    pub_request.redis_pub.request_done_evt.set()
                except redis.RedisError:
                    pub_request.redis_pub.io_error = True
            # mark as done
            self.publish_request_q.task_done()
