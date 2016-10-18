# -*- coding: utf-8 -*-

import redis


class RedisDevice(object):
    def __init__(self, host='localhost', port=6379, timeout=0.1):
        self.host = host
        self.port = port
        self.timeout = timeout
        # privates vars
        self._r = redis.Redis(host=self.host, port=self.port, socket_timeout=self.timeout)

    @property
    def connected(self):
        try:
            return self._r.ping()
        except redis.RedisError:
            return False

    # tag_add, get, err and set are mandatory function to be a valid tag source
    def tag_add(self, tag):
        # check type
        if not any(tag.ref['type'] in s for s in ('bool', 'int', 'float', 'str')):
            raise ValueError(
                'Wrong tag type %s for Redis host %s' % (tag.ref['type'], self.host))

    def get(self, ref):
        try:
            # read
            value = self._r.get(ref['key'])
            # cast
            if ref['type'] == 'bool':
                return bool(value)
            elif ref['type'] == 'int':
                return int(value)
            elif ref['type'] == 'float':
                return float(value)
            elif ref['type'] == 'str':
                return str(value)
        except redis.RedisError:
            return None

    def err(self, ref):
        try:
            return self._r.get(ref['key']) is None
        except redis.RedisError:
            return True

    def set(self, value, ref):
        return False
