import operator
from typing import Callable, Optional, Union, get_args
from . import logger


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
    TAG_TYPE = Union[bool, int, float, str, bytes]

    def __init__(self, first_value: TAG_TYPE, src: Optional[DataSource] = None,
                 chg_cmd: Optional[Callable] = None) -> None:
        """Constructor

        Abstract access to project tags.

        :param first_value: initial value of the tag
        :param src: an external data source like RedisKey
        :param chg_cmd: a method to change tag value (scale, limit value...)
        """
        # runtime type check
        if not isinstance(first_value, Tag.TAG_TYPE):
            raise TypeError(f'first_value type must be in {get_args(Tag.TAG_TYPE)}')
        # args
        self.first_value = first_value
        self.src = src
        self.chg_cmd = chg_cmd
        # private
        self._value = self.first_value
        self._error = False
        # notify tag creation to external source
        if isinstance(self.src, DataSource):
            self.src.add_tag(self)

    def __str__(self) -> str:
        return f'tag.val={self.val!r} tag.e_val={self.e_val!r} tag.err={self.err!r}'

    def __repr__(self) -> str:
        return f'Tag({self.first_value!r}, src={self.src!r}, chg_cmd={self.chg_cmd})'

    def _set_src(self, value: TAG_TYPE) -> None:
        if isinstance(self.src, DataSource):
            chg_value = self._apply_chg_cmd(value)
            if chg_value is not None:
                self.src.set(chg_value)

    def _get_src(self) -> Optional[TAG_TYPE]:
        if isinstance(self.src, DataSource):
            return self._apply_chg_cmd(self.src.get())

    def _apply_chg_cmd(self, value: Optional[TAG_TYPE]) -> Optional[TAG_TYPE]:
        # if a change command is set
        if self.chg_cmd:
            # try to alter or transform value with it
            try:
                return self.chg_cmd(value)
            except Exception as e:
                logger.warning(f'chg_cmd processing failed (except "{e}") in {self!r}')
                return
        else:
            # pass through if chg_cmd is unset
            return value

    def _set_value(self, value: Optional[TAG_TYPE]) -> None:
        # on None value keep internal value unchange and set error flag
        if value is None:
            self._error = True
        else:
            self._error = False
            self._value = value

    @property
    def val(self) -> TAG_TYPE:
        """Return current tag value from any way (ext sourced tag or internal value).

        :return: tag value
        """
        # get tag value from external source if available
        if self.src:
            self._set_value(self._get_src())
        # return internal tag value
        return self._value

    @val.setter
    def val(self, value: Optional[TAG_TYPE]) -> None:
        """Set value of tag.

        :param value: value of tag
        """
        # set internal value
        self._set_value(value)
        # notify external source if available
        if self.src:
            self._set_src(self._value)

    @property
    def e_val(self) -> Optional[TAG_TYPE]:
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
            return self._error or self.src.error()
        # read error status from internal store
        else:
            return self._error

    def set(self, value: Optional[TAG_TYPE]) -> None:
        """ An helper to let user set the val property in lambda usage context. """
        self.val = value


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
