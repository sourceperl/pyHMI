from datetime import datetime, timezone
import operator
from typing import Any, Callable, Optional, Union


class Device:
    """Device class template for externally sourced tags (from Modbus/TCP, database...).

    Each Device must derive from this class.
    """
    pass


class DataSource:
    """DataSource class template for externally sourced tags (from Modbus/TCP, database...).

    Every DataSource must derive from this class.
    """

    def add_tag(self, tag: "Tag") -> None:
        """ Method call by Tag class constructor to notify datasource of tag creation. """
        pass

    def get(self) -> Union[bool, int, float, str, bytes, None]:
        """ Method call by Tag class to retrieve value from datasource. """
        pass

    def set(self, value: Union[bool, int, float, str, bytes]) -> None:
        """ Method call by Tag class to set value in datasource. """
        pass

    def error(self) -> bool:
        """ Method call by Tag class to retrieve error status from datasource. """
        return False


class Tag:
    def __init__(self, init_value, src: Optional[DataSource] = None, 
                 get_cmd: Optional[Callable] = None, chg_cmd: Optional[Callable] = None):
        """Constructor

        Abstract access to project tags.

        :param init_value: initial value of the tag
        :param src: an external data source like RedisKey
        :param get_cmd: a callback to read value/error status of the tag
        :param chg_cmd: a method to change tag value (scale, limit value...)

        :rtype Tag
        """
        # args
        self.init_value = init_value
        self.src = src
        self.get_cmd = get_cmd
        self.chg_cmd = chg_cmd
        # public
        self.dt_created = datetime.now(timezone.utc)
        self.dt_last_change = self.dt_created
        # set on tag change, must be reset by user
        self.updated = False
        # private
        self._value = init_value
        self._old_value = init_value
        self._error = False
        # notify tag creation to external source
        if isinstance(self.src, DataSource):
            self.src.add_tag(self)

    def __repr__(self):
        return f'Tag({self.init_value!r}, src={self.src!r}, get_cmd={self.get_cmd})'

    def _set_value(self, value):
        # update value if change command if defined
        if callable(self.chg_cmd):
            value = self.chg_cmd(value)
        # on change
        if value != self._value:
            self._old_value = self._value
            self._value = value
            # set flags and call event for user
            self.dt_last_change = datetime.now(timezone.utc)
            self.updated = True
            self.on_value_change()

    def on_value_change(self):
        """ Event call when value of tag change (for user purpose). """
        pass

    def set(self, value: Any):
        """ An helper to let user set the val property in lambda usage context. """
        self.val = value

    @property
    def val(self) -> Union[bool, int, float, str, bytes]:
        """Return current tag value from any way (ext sourced tag, get command tag or internal value).

        :return: tag value
        """
        # read tag value from external source
        if isinstance(self.src, DataSource):
            src_get_ret = self.src.get()
            if src_get_ret is not None:
                self._set_value(src_get_ret)
            return self._value
        # read tag value from get command
        elif callable(self.get_cmd):
            # call external command (return last good value on run error)
            try:
                get_value = self.get_cmd()
                if get_value is None:
                    raise RuntimeError
            except Exception:
                self._error = True
                return self._value
            # on success
            self._error = False
            self._set_value(get_value)            
            return get_value
        # read tag value from internal
        else:
            return self._value

    @val.setter
    def val(self, value) -> None:
        """Set value of tag.

        :param value: value of tag
        """
        if value is None:
            self._error = True
        else:
            # notify external source to update the value
            if isinstance(self.src, DataSource):
                self.src.set(value)
                self._set_value(value)
            # no external source to notify
            else:
                self._set_value(value)
                self._error = False

    @property
    def e_val(self) -> Union[bool, int, float, str, bytes, None]:
        """Return tag value or None if tag error status is set.

        :return: tag value or None
        """
        return None if self.err else self.val

    @property
    def err(self) -> bool:
        """Return True is Tag have error status set, False if not.

        :return: error status
        :rtype: bool
        """
        # read error status from external source
        if isinstance(self.src, DataSource):
            return self.src.error()
        # read error status from internal store
        else:
            return self._error

    @err.setter
    def err(self, value: bool) -> None:
        """Set the error status of tag (useless for externally sourced or tag with get_cmd set).

        :param value: error status
        """
        self._error = value


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
            return args[int(tag.val)]
        except IndexError:
            return


def tag_equal(tag: Tag, value: Union[float, int]):
    return tag_op(tag, operator.eq, value)
