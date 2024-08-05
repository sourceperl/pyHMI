import threading
from typing import Any, Dict, Optional
from .Tag import Tag, DS, TagRef
import redis


class _LockRedisCli:
    """ Allow thread safe access to redis client.

    Essential to share access between internal IO thread and direct user acess.

    Usage:
        lock_redis_cli = _LockRedisCli(redis.StrictRedis())

        with lock_redis_cli as cli:
            cli.get('foo')
    """

    def __init__(self, client: redis.StrictRedis):
        self._client = client
        self._thread_lock = threading.Lock()

    def __enter__(self):
        self._thread_lock.acquire()
        return self._client

    def __exit__(self, *_args):
        self._thread_lock.release()


class RedisKey(TagRef):
    _uid: int = 0

    def __init__(self, name: str, type: type, ttl: Optional[float] = None, writable: bool = False) -> None:
        # args
        self.name = name
        self.type = type
        self.ttl = ttl
        self.writable = writable
        # unique id
        self.uid = RedisKey._uid
        RedisKey._uid += 1
        # error flags
        self.io_error = True
        self.fmt_error = True
        # private
        self.write_flag = False
        self._read_value = self.type()
        self._write_raw = b''

    def __repr__(self):
        return f'RedisKey({self.name!r}, type={self.type.__name__}, ttl={self.ttl}, writable={self.writable})'

    def parse_raw(self, redis_raw: bytes) -> Any:
        if self.type is bool:
            if redis_raw == b'True':
                return True
            elif redis_raw == b'False':
                return False
            else:
                raise ValueError
        elif self.type is str:
            return redis_raw.decode()
        else:
            return self.type(redis_raw)

    @property
    def error(self):
        return self.io_error or self.fmt_error

    @property
    def value(self):
        # check read-only
        if self.writable:
            raise ValueError(f'cannot read write-only {self!r}')
        if not self.error:
            return self._read_value
        else:
            return

    @value.setter
    def value(self, value):
        # check read-only
        if not self.writable:
            raise ValueError(f'cannot write read-only {self!r}')
        # check type
        try:
            # format raw for redis
            if self.type is bytes:
                if isinstance(value, bytes):
                    self._write_raw = value
                else:
                    raise TypeError
            else:
                self._write_raw = str(self.type(value)).encode()
            # mark as to write
            self.write_flag = True
        except (TypeError, ValueError):
            raise ValueError(f'unable to set {self!r} to {value!r}')


class RedisDevice(DS):
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0, refresh: float = 1.0,
                 timeout: float = 1.0, client_adv_args: Optional[dict] = None):
        super().__init__()
        # public vars
        self.host = host
        self.port = port
        self.db = db
        self.refresh = refresh
        self.timeout = timeout
        self.client_adv_args = client_adv_args
        # privates vars
        self._keys_d: Dict[int, RedisKey] = {}
        self._keys_d_lock = threading.Lock()
        self._wait_evt = threading.Event()
        # redis client
        args_d = {} if self.client_adv_args is None else self.client_adv_args
        self.lock_cli = _LockRedisCli(redis.Redis(host=self.host, port=self.port, db=self.db,
                                                  socket_timeout=self.timeout, socket_keepalive=True, **args_d))
        self._poll_cycle = 0
        self._connected = False
        # start thread
        self._th = threading.Thread(target=self._io_thread)
        self._th.daemon = True
        self._th.start()

    def __repr__(self):
        return 'RedisDevice(host=%s, port=%i, refresh=%.1f, timeout=%.1f, client_adv_args=%s)' \
               % (self.host, self.port, self.refresh, self.timeout, self.client_adv_args)

    @property
    def connected(self):
        return self._connected

    @property
    def poll_cycle(self):
        return self._poll_cycle

    # tag_add, get, err and set are mandatory function to be a valid tag source
    def tag_add(self, tag: Tag):
        if isinstance(tag.ref, RedisKey):
            # add tag to keys dict
            with self._keys_d_lock:
                self._keys_d[tag.ref.uid] = tag.ref
        else:
            raise ValueError(f'bad type for ref in tag {Tag} it must be a RedisKey instance')

    def get(self, ref: RedisKey):
        with self._keys_d_lock:
            return self._keys_d[ref.uid].value

    def err(self, ref: RedisKey):
        with self._keys_d_lock:
            return self._keys_d[ref.uid].error

    def set(self, ref: RedisKey, value):
        with self._keys_d_lock:
            self._keys_d[ref.uid].value = value

    def _io_thread(self):
        """ Process every I/O with redis DB. """
        while True:
            # do thread safe copy of read/write buffer for this cycle
            with self._keys_d_lock:
                keys_d_copy = self._keys_d.copy()
            # do redis i/o
            for _uid, redis_key in keys_d_copy.items():
                try:
                    # write
                    if redis_key.writable:
                        if redis_key.write_flag:
                            redis_key.write_flag = False
                            with self.lock_cli as cli:
                                cli.set(redis_key.name, redis_key._write_raw, ex=redis_key.ttl)
                            redis_key.io_error = False
                    # read
                    if not redis_key.writable:
                        with self.lock_cli as cli:
                            read_raw = cli.get(redis_key.name)
                        # status of reading
                        if read_raw is None:
                            redis_key.io_error = True
                        else:
                            redis_key.io_error = False
                            try:
                                redis_key._read_value = redis_key.parse_raw(read_raw)
                                redis_key.fmt_error = False
                            except ValueError as e:
                                redis_key.fmt_error = True
                except redis.RedisError:
                    redis_key.io_error = True
            # update keys dict
            with self._keys_d_lock:
                self._keys_d.update(keys_d_copy)
            # loop counter
            self._poll_cycle += 1
            # set connected flag
            try:
                with self.lock_cli as cli:
                    self._connected = cli.ping()
            except redis.RedisError:
                self._connected = False
            # wait before next polling (or not if a write trig wait event)
            if self._wait_evt.wait(self.refresh):
                self._wait_evt.clear()
