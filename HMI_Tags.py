class Tags(object):
    def __init__(self, init_value, src=None, ref=None, get_cmd=None):
        """ Abstract access to project tags

        """
        self.ref = ref
        self._get_cmd = get_cmd
        self._src = src
        self._val = init_value
        self._err = False
        # notify src for tag add
        if self._src:
            self._src.tag_add(self)

    def set(self, value):
        if value is not None:
            if self._src is not None:
                self._src.set(value, self.ref)
            else:
                self._val = value
                self._err = False
        else:
            self._err = True

    @property
    def val(self):
        if self._src is not None:
            ret = self._src.get(self.ref)
            if ret is not None:
                self._val = ret
            return self._val
        elif self._get_cmd is not None:
            ret = self._get_cmd()
            return self._val if ret is None else ret
        else:
            return self._val

    @val.setter
    def val(self, value):
        self.set(value)

    @property
    def err(self):
        if self._src is not None:
            return self._src.err(self.ref)
        elif self._get_cmd is not None:
            return self._get_cmd() is None
        else:
            return self._err

    @err.setter
    def err(self, value):
        self._err = bool(value)
