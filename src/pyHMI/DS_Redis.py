import threading
from typing import Dict
from .Tag import Tag, DS
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


class _RedisKey(object):
    def __init__(self, var_type='int', init_value=0, ttl=None):
        self.var_type = var_type
        self.error = True
        self.redis_read = init_value
        self.redis_write = init_value
        self.write_flag = False
        self.ttl = ttl

    def value(self):
        # read value with format
        if self.var_type == 'bool':
            try:
                return self.redis_read == b'True'
            except ValueError:
                return False
        elif self.var_type == 'int':
            try:
                return int(self.redis_read)
            except ValueError:
                return 0
        elif self.var_type == 'float':
            try:
                return float(self.redis_read)
            except ValueError:
                return float('nan')
        elif self.var_type == 'str':
            if type(self.redis_read) is bytes:
                return bytes(self.redis_read).decode('utf-8')
            elif type(self.redis_read) is str:
                return self.redis_read
            else:
                return ''

    def update(self, value):
        # format data for write
        if self.var_type == 'bool':
            self.redis_write = b'True' if bool(value) else b'False'
            self.write_flag = True
        elif self.var_type == 'int':
            self.redis_write = int(value)
            self.write_flag = True
        elif self.var_type == 'float':
            self.redis_write = float(value)
            self.write_flag = True
        elif self.var_type == 'str':
            if type(value) is bytes:
                self.redis_write = value
            else:
                self.redis_write = bytes(value, 'utf-8')
            self.write_flag = True


class RedisDevice(DS):
    def __init__(self, host='localhost', port=6379, refresh=1.0, timeout=1.0, client_adv_args=None):
        super().__init__()
        # public vars
        self.host = host
        self.port = port
        self.refresh = refresh
        self.timeout = timeout
        self.client_adv_args = client_adv_args
        # privates vars
        self._keys_d: Dict[_RedisKey] = {}
        self._keys_d_lock = threading.Lock()
        self._wait_evt = threading.Event()
        # redis client
        args_d = {} if self.client_adv_args is None else self.client_adv_args
        self.lock_cli = _LockRedisCli(redis.Redis(host=self.host, port=self.port,
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
        # check key is set
        if 'key' not in tag.ref:
            raise ValueError('Key is not define for tag on Redis host %s' % self.host)
        # check valid type
        if not tag.ref['type'] in ('bool', 'int', 'float', 'str'):
            raise ValueError('Wrong tag type %s for Redis host %s' % (tag.ref['type'], self.host))
        # add tag to keys dict
        with self._keys_d_lock:
            self._keys_d[tag.ref['key']] = _RedisKey(var_type=tag.ref['type'], ttl=tag.ref.get('ttl', None))

    def get(self, ref):
        with self._keys_d_lock:
            return self._keys_d[ref['key']].value()

    def err(self, ref):
        with self._keys_d_lock:
            return self._keys_d[ref['key']].error

    def set(self, ref, value):
        with self._keys_d_lock:
            return self._keys_d[ref['key']].update(value)

    def _io_thread(self):
        """ Process every I/O with redis DB. """
        while True:
            # do thread safe copy of read/write buffer for this cycle
            with self._keys_d_lock:
                keys_d_copy = self._keys_d.copy()
            # do redis i/o
            for key in keys_d_copy:
                try:
                    # write
                    if keys_d_copy[key].write_flag:
                        keys_d_copy[key].write_flag = False
                        with self.lock_cli as cli:
                            cli.set(key, keys_d_copy[key].redis_write, ex=keys_d_copy[key].ttl)
                    # read
                    with self.lock_cli as cli:
                        redis_val = cli.get(key)
                    # status update
                    if redis_val is None:
                        keys_d_copy[key].error = True
                    else:
                        keys_d_copy[key].redis_read = redis_val
                        keys_d_copy[key].error = False
                except redis.RedisError:
                    keys_d_copy[key].error = True
            # update keys dict
            with self._keys_d_lock:
                self._keys_d.update(keys_d_copy)
            # update connected flag
            try:
                with self.lock_cli as cli:
                    self._connected = cli.ping()
            except redis.RedisError:
                self._connected = False
            # loop counter
            self._poll_cycle += 1
            # wait before next polling (or not if a write trig wait event)
            if self._wait_evt.wait(self.refresh):
                self._wait_evt.clear()
