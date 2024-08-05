from queue import Queue, Full
import threading
import time
from typing import Any, Dict, Optional, Union
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


class _PubRequest:
    """ A publish request data container for publish io thread queue. """

    def __init__(self, redis_pub: "RedisPub", message: Union[str, bytes]) -> None:
        self.redis_pub = redis_pub
        self.message = message


class RedisPub(TagRef):
    def __init__(self, channel: str) -> None:
        # args
        self.channel = channel
        # error flags
        self.error = False
        # private
        self._pub_q: Optional[Queue[_PubRequest]] = None

    def __repr__(self):
        return f'RedisPub({self.channel!r})'

    def publish(self, value: Union[str, bytes]):
        try:
            if self._pub_q:
                self._pub_q.put(_PubRequest(self, value))
        except Full:
            self.error = True


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
        self._pub_q = Queue(maxsize=5)
        # redis client
        args_d = {} if self.client_adv_args is None else self.client_adv_args
        self.lock_cli = _LockRedisCli(redis.Redis(host=self.host, port=self.port, db=self.db,
                                                  socket_timeout=self.timeout, socket_keepalive=True, **args_d))
        self._connected = False
        # start threads
        self._th_keys_io = threading.Thread(target=self._keys_io_thread, daemon=True)
        self._th_pub_io = threading.Thread(target=self._pub_io_thread, daemon=True)
        self._th_keys_io.start()
        self._th_pub_io.start()

    def __repr__(self):
        return 'RedisDevice(host=%s, port=%i, refresh=%.1f, timeout=%.1f, client_adv_args=%s)' \
               % (self.host, self.port, self.refresh, self.timeout, self.client_adv_args)

    @property
    def connected(self):
        return self._connected

    # tag_add, get, err and set are mandatory function to be a valid tag source
    def tag_add(self, tag: Tag):
        if isinstance(tag.ref, RedisKey):
            # add tag to keys dict
            with self._keys_d_lock:
                self._keys_d[tag.ref.uid] = tag.ref
        elif isinstance(tag.ref, RedisPub):
            tag.ref._pub_q = self._pub_q
        else:
            raise ValueError(f'RedisDevice: bad type for ref in tag {Tag} it must be a RedisKey/RedisPub/RedisSub')

    def get(self, ref: Union[RedisKey, RedisPub]):
        if isinstance(ref, RedisKey):
            with self._keys_d_lock:
                return self._keys_d[ref.uid].value
        elif isinstance(ref, RedisPub):
            raise ValueError(f'cannot read write-only {ref!r}')

    def err(self, ref: Union[RedisKey, RedisPub]):
        if isinstance(ref, RedisKey):
            with self._keys_d_lock:
                return self._keys_d[ref.uid].error
        elif isinstance(ref, RedisPub):
            return ref.error

    def set(self, ref: Union[RedisKey, RedisPub], value):
        if isinstance(ref, RedisKey):
            with self._keys_d_lock:
                self._keys_d[ref.uid].value = value
        elif isinstance(ref, RedisPub):
            if not isinstance(value, (str, bytes)):
                raise ValueError(f'bad type for publish on {ref!r}')
            ref.publish(value)

    def _keys_io_thread(self):
        """ Process every I/O for keys on redis DB. """
        while True:
            # do thread safe copy of read/write buffer for this cycle
            with self._keys_d_lock:
                keys_d_copy = self._keys_d.copy()
            # redis i/o keys part
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
                    else:
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
                            except ValueError:
                                redis_key.fmt_error = True
                except redis.RedisError:
                    redis_key.io_error = True
            # update keys dict
            with self._keys_d_lock:
                self._keys_d.update(keys_d_copy)
            # set connected flag
            try:
                with self.lock_cli as cli:
                    self._connected = cli.ping()
            except redis.RedisError:
                self._connected = False
            # wait before next polling (or not if a write trig wait event)
            time.sleep(self.refresh)

    def _pub_io_thread(self):
        """ Process every I/O for pub/sub on redis DB. """
        while True:
            # do thread safe copy of read/write buffer for this cycle
            request: _PubRequest = self._pub_q.get()
            # redis i/o pub/sub part
            try:
                with self.lock_cli as cli:
                    cli.publish(request.redis_pub.channel, request.message)
                request.redis_pub.error = False
            except redis.RedisError:
                request.redis_pub.error = True
