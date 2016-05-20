# -*- coding: utf-8 -*-


class Tag(object):
    def __init__(self, init_value, src=None, ref=None, get_cmd=None):
        """Constructor

        Abstract access to project tags.

        :param init_value: initial value of the tag
        :param src: an external data source like Modbus
        :param ref: ref dict for data source
        :param get_cmd: a callback to read value/error status of the tag

        :rtype Tags
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
        """ Set value of the tag

        :param value: value of the tag
        """
        if value is not None:
            if self._src is not None:
                if self._src.set(value, self.ref):
                    self._val = value
                    self._err = False
                else:
                    self._err = True
            else:
                self._val = value
                self._err = False
        else:
            self._err = True

    @property
    def val(self):
        """Return current tag value from any way (ext sourced tag, get command tag or internal value)

        :return: tag value
        """
        # read tag from external source
        if self._src is not None:
            ret = self._src.get(self.ref)
            if ret is not None:
                self._val = ret
            return self._val
        # read tag from a get command
        elif self._get_cmd is not None:
            try:
                ret = self._get_cmd()
            except TypeError:
                return self._val
            else:
                if ret is None:
                    return self._val
                else:
                    self._val = ret
                    return self._val
        # read tag from internal store
        else:
            return self._val

    @val.setter
    def val(self, value):
        """Set value of tag

        :param value: value of tag
        """
        self.set(value)

    @property
    def e_val(self):
        """Return tag value or None if tag error status is set

        :return: tag value or None
        """
        return None if self.err else self.val

    @property
    def err(self):
        """Return True is Tag have error status set, False if not

        :return: error status
        :rtype: bool
        """
        if self._src is not None:
            return self._src.err(self.ref)
        elif self._get_cmd is not None:
            try:
                ret = self._get_cmd()
            except TypeError:
                return True
            else:
                return ret is None
        else:
            return self._err

    @err.setter
    def err(self, value):
        """Set the error status of tag

        :param value: error status
        :type bool
        """
        self._err = bool(value)


def tag_equal(tag, value):
    if not tag.err:
        return tag.val == value
    else:
        return None
