from abc import ABC, abstractmethod
from datetime import datetime, timezone
import operator
from typing import Callable, Optional, Union


class Device:
    """Device class template for externally sourced tags (from Modbus/TCP, database...).

    Each Device must derive from this class.
    """
    pass


class DataSource(ABC):
    """DataSource class template for externally sourced tags (from Modbus/TCP, database...).

    Every DataSource must derive from this abstract class.
    """

    @abstractmethod
    def tag_add(self, tag: "Tag") -> None:
        """ Method call by Tag class constructor to notify datasource of tag creation. """
        pass

    @abstractmethod
    def get(self) -> Union[bool, int, float, str, bytes, None]:
        """ Method call by Tag class to retrieve value from datasource. """
        pass

    @abstractmethod
    def set(self, value: Union[bool, int, float, str, bytes]) -> None:
        """ Method call by Tag class to set value in datasource. """
        pass

    @abstractmethod
    def error(self) -> bool:
        """ Method call by Tag class to retrieve error status from datasource. """
        pass


class Tag:
    def __init__(self, init_value, src: Optional[DataSource] = None, get_cmd: Optional[Callable] = None):
        """Constructor

        Abstract access to project tags.

        :param init_value: initial value of the tag
        :param src: an external data source like RedisKey
        :param get_cmd: a callback to read value/error status of the tag

        :rtype Tag
        """
        # args
        self.init_value = init_value
        self.src = src
        self.get_cmd = get_cmd
        # public
        self.dt_created = datetime.now(timezone.utc)
        self.dt_last_change = self.dt_created
        # set on tag change, must be reset by user
        self.updated = False
        # private
        self._cache_cur_val = init_value
        self._cache_old_val = init_value
        self._error = False
        # notify tag creation to external source
        if isinstance(self.src, Device):
            self.src.tag_add(self)

    def __repr__(self):
        return f'Tag({self.init_value!r}, src={self.src!r}, get_cmd={self.get_cmd})'

    def _set_cache_value(self, value):
        if value != self._cache_cur_val:
            self._cache_old_val = self._cache_cur_val
            self._cache_cur_val = value
            self.dt_last_change = datetime.now(timezone.utc)
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
        """ Set value of the tag.

        :param value: value of the tag
        """
        if value is None:
            self._set_error(True)
        else:
            # notify external source to update the value
            if isinstance(self.src, DataSource):
                if self.src.set(value):
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
        """Return current tag value from any way (ext sourced tag, get command tag or internal value).

        :return: tag value
        """
        # read tag from external source
        if isinstance(self.src, DataSource):
            ret = self.src.get()
            if ret is not None:
                self._set_cache_value(ret)
            return self._get_cache_value()
        # read tag from a get command
        elif callable(self.get_cmd):
            try:
                ret = self.get_cmd()
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
        """Set value of tag.

        :param value: value of tag
        """
        self.set(value)

    @property
    def e_val(self):
        """Return tag value or None if tag error status is set.

        :return: tag value or None
        """
        return None if self.err else self.val

    @property
    def err(self):
        """Return True is Tag have error status set, False if not.

        :return: error status
        :rtype: bool
        """
        # read error status from external source
        if isinstance(self.src, DataSource):
            return self.src.error()
        # read error status from get command
        elif callable(self.get_cmd):
            try:
                ret = self.get_cmd()
            except TypeError:
                return True
            else:
                return ret is None
        # read error status from internal store
        else:
            return self._get_error()

    @err.setter
    def err(self, value):
        """Set the error status of tag (useless for externally sourced or tag with get_cmd set).

        :param value: error status
        """
        self._set_error(value)


class TagsBank:
    """Generic Tags enumeration

    Derive from this class to define Tags enumerations in your project.
    """

    @classmethod
    def to_dict(cls):
        """
        Retrieve Tags as a dict with tag name as key and tag as value.

        :return: Tags dict with {tag name: tag object, ...} format.
        :rtype: dict
        """
        return {k: v for k, v in cls.__dict__.items() if not k.startswith('__') and isinstance(v, Tag)}

    @classmethod
    def items(cls):
        """
        Retrieve Tags as a list of tuple for easy iteration with for loop.

        :return: List of Tags as tuple [(tag name, tag object), (...), ...].
        :rtype: list
        """
        return [(k, v) for k, v in cls.__dict__.items() if not k.startswith('__') and isinstance(v, Tag)]


def tag_op(a: Union[Tag, bool, float, int], operator, b: Union[Tag, bool, float, int, None] = None):
    # handle Tag args
    a_val, a_err = (a.val, a.err) if isinstance(a, Tag) else (a, False)
    b_val, b_err = (b.val, b.err) if isinstance(b, Tag) else (b, False)
    # return None if any Tag have "err" flag set
    if a_err or b_err:
        return
    else:
        # single a or dual a/b args operation
        if b_val is None:
            return operator(a_val)
        else:
            return operator(a_val, b_val)


def tag_sel(tag: Tag, *args):
    if tag.err:
        return
    else:
        try:
            return args[tag.val]
        except IndexError:
            return


def tag_equal(tag: Tag, value: Union[float, int]):
    return tag_op(tag, operator.eq, value)
