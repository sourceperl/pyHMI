class Tags(object):
    def __init__(self, init_value, src=None, ref=None, get_cmd=None):
        """ Abstract access to project tags

        """
        self.ref = ref
        self._get_cmd = get_cmd
        self._src = src
        self._val = init_value
        self._err = False

    def set(self, value):
        if value is not None:
            self._val = value
            self._err = False
        else:
            self._err = True

    @property
    def val(self):
        if self._src is not None:
            return self._src.get('val', self.ref)
        elif self._get_cmd is not None:
            ret = self._get_cmd()
            return self._val if ret is None else ret
        else:
            return self._val

    @property
    def err(self):
        if self._src is not None:
            return self._src.get('err', self.ref)
        elif self._get_cmd is not None:
            return self._get_cmd() is None
        else:
            return self._err
