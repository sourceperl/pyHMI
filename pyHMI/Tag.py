# -*- coding: utf-8 -*-

import datetime
import time


class DS(object):
    def __init__(self):
        """Constructor

        DataSource template for externally sourced tags (from Modbus/TCP, database...)

        :rtype DS
        """
        pass

    def tag_add(self, tag):
        pass

    def get(self, ref):
        return 0

    def set(self, ref, value):
        return None

    def err(self, ref):
        return True


class Tag(object):
    def __init__(self, init_value, src=None, ref=None, get_cmd=None):
        """Constructor

        Abstract access to project tags.

        :param init_value: initial value of the tag
        :param src: an external data source like Modbus
        :param ref: ref dict for data source
        :param get_cmd: a callback to read value/error status of the tag

        :rtype Tag
        """
        # public
        self.ref = ref
        self.tag_type = type(init_value)
        self.dt_created = datetime.datetime.utcnow()
        self.dt_last_change = datetime.datetime.utcnow()
        # set on tag change, reset by package user
        self.updated = False
        # private
        self._get_cmd = get_cmd
        self._src = src
        self._cache_cur_val = init_value
        self._cache_old_val = init_value
        self._error = False
        # notify tag creation to external source
        if isinstance(self._src, DS):
            self._src.tag_add(self)

    def __str__(self):
        return '%s' % self._cache_cur_val

    def __repr__(self):
        return 'Tag(%s, src=%r, ref=%s, get_cmd=%s)' % (self._cache_cur_val, self._src, self.ref, self._get_cmd)

    def _set_cache_value(self, value):
        if value != self._cache_cur_val:
            self._cache_old_val = self._cache_cur_val
            self._cache_cur_val = value
            self.dt_last_change = datetime.datetime.utcnow()
            self.updated = True
            self.on_value_change()

    def _get_cache_value(self):
        return self._cache_cur_val

    def _set_error(self, value):
        self._error = bool(value)

    def _get_error(self):
        return self._error

    def on_value_change(self):
        pass

    def set(self, value):
        """ Set value of the tag

        :param value: value of the tag
        """
        if value is None:
            self._set_error(True)
        else:
            # notify external source to update the value
            if isinstance(self._src, DS):
                if self._src.set(self.ref, value):
                    # on update success
                    self._set_cache_value(value)
                    self._set_error(False)
                else:
                    # on update error
                    self._set_error(True)
            # no external source to notify
            else:
                self._set_cache_value(value)
                self._set_error(False)

    @property
    def val(self):
        """Return current tag value from any way (ext sourced tag, get command tag or internal value)

        :return: tag value
        """
        # read tag from external source
        if isinstance(self._src, DS):
            ret = self._src.get(self.ref)
            if ret is not None:
                self._set_cache_value(ret)
            return self._get_cache_value()
        # read tag from a get command
        elif callable(self._get_cmd):
            try:
                ret = self._get_cmd()
            except TypeError:
                return self._get_cache_value()
            else:
                if ret is None:
                    return self._get_cache_value()
                else:
                    self._set_cache_value(ret)
                    return self._get_cache_value()
        # read tag from internal store
        else:
            return self._get_cache_value()

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
        # read error status from external source
        if isinstance(self._src, DS):
            return self._src.err(self.ref)
        # read error status from get command
        elif callable(self._get_cmd):
            try:
                ret = self._get_cmd()
            except TypeError:
                return True
            else:
                return ret is None
        # read error status from internal store
        else:
            return self._get_error()

    @err.setter
    def err(self, value):
        """Set the error status of tag (useless for externally sourced or tag with get_cmd set)

        :param value: error status
        """
        self._set_error(value)


def tag_equal(tag, value):
    if tag.err:
        return None
    else:
        return tag.val == value


def dt_utc2local(dt_utc):
    """Convert UTC datetime to local datetime

    :param dt_utc: UTC datetime
    :type dt_utc: datetime.datetime

    :return: local datetime
    :rtype: datetime.datetime
    """
    now_ts = time.time()
    offset = datetime.datetime.fromtimestamp(now_ts) - datetime.datetime.utcfromtimestamp(now_ts)
    dt_local = dt_utc + offset
    return dt_local
