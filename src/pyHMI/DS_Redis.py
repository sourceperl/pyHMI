import threading
from .Tag import DS
import redis



class RedisKey(object):
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
        # client advanced parameters
        if client_adv_args is None:
            self.client_adv_args = dict()
        else:
            self.client_adv_args = client_adv_args
        # privates vars
        self._all_keys = {}
        self._tmp_keys = {}
        self._lock = threading.Lock()
        self._wait_evt = threading.Event()
        # redis client
        self._r = redis.Redis(host=self.host, port=self.port,
                              socket_timeout=self.timeout, socket_keepalive=True,
                              **self.client_adv_args)
        self._poll_cycle = 0
        self._connected = False
        # start thread
        self._th = threading.Thread(target=self.polling_thread)
        self._th.daemon = True
        self._th.start()

    def __repr__(self):
        return 'RedisDevice(host=%s, port=%i, refresh=%.1f, timeout=%.1f, client_adv_args=%s)' \
               % (self.host, self.port, self.refresh, self.timeout, self.client_adv_args)

    @property
    def connected(self):
        with self._lock:
            return self._connected

    @property
    def poll_cycle(self):
        with self._lock:
            return self._poll_cycle

    # tag_add, get, err and set are mandatory function to be a valid tag source
    def tag_add(self, tag):
        # check key is set
        if 'key' not in tag.ref:
            raise ValueError('Key is not define for tag on Redis host %s' % self.host)
        # check valid type
        if not tag.ref['type'] in ('bool', 'int', 'float', 'str'):
            raise ValueError('Wrong tag type %s for Redis host %s' % (tag.ref['type'], self.host))
        # add tag to keys dict
        with self._lock:
            self._all_keys[tag.ref['key']] = RedisKey(var_type=tag.ref['type'], ttl=tag.ref.get('ttl', None))

    def get(self, ref):
        with self._lock:
            return self._all_keys[ref['key']].value()

    def err(self, ref):
        with self._lock:
            return self._all_keys[ref['key']].error

    def set(self, ref, value):
        with self._lock:
            return self._all_keys[ref['key']].update(value)

    def polling_thread(self):
        # polling cycle
        while True:
            # do thread safe copy of read/write buffer for this cycle
            with self._lock:
                self._tmp_keys = self._all_keys.copy()
            # do all redis read
            for k in self._tmp_keys:
                try:
                    # write value in redis if need
                    if self._tmp_keys[k].write_flag:
                        self._tmp_keys[k].write_flag = False
                        self._r.set(k, self._tmp_keys[k].redis_write, ex=self._tmp_keys[k].ttl)
                    # read value in redis
                    redis_val = self._r.get(k)
                    if redis_val is not None:
                        self._tmp_keys[k].redis_read = redis_val
                        self._tmp_keys[k].error = False
                    else:
                        self._tmp_keys[k].error = True
                except redis.RedisError:
                    self._tmp_keys[k].error = True
            # update _keys dict
            with self._lock:
                self._all_keys.update(self._tmp_keys)
            # do stat stuff
            with self._lock:
                try:
                    self._connected = self._r.ping()
                except redis.RedisError:
                    self._connected = False
                self._poll_cycle += 1
            # wait before next polling (or not if a write trig wait event)
            if self._wait_evt.wait(self.refresh):
                self._wait_evt.clear()
