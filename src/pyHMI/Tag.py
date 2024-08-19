from typing import Any, Callable, Optional, Union, get_args
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

    def __init__(self, init_value: TAG_TYPE, init_error: bool = False,
                 src: Optional[DataSource] = None, chg_cmd: Optional[Callable] = None, ) -> None:
        """Constructor

        Abstract access to project tags.

        :param first_value: initial value of the tag
        :param src: an external data source like RedisKey
        :param chg_cmd: a method to change tag value (scale, limit value...)
        """
        # runtime type check
        if not isinstance(init_value, Tag.TAG_TYPE):
            raise TypeError(f'first_value type must be in {get_args(Tag.TAG_TYPE)}')
        # args
        self.init_value = init_value
        self.init_error = init_error
        self.src = src
        self.chg_cmd = chg_cmd
        # private
        self._value = self.init_value
        self._error = self.init_error
        # notify tag creation to external source
        if isinstance(self.src, DataSource):
            self.src.add_tag(self)

    def __str__(self) -> str:
        return f'tag.value={self.value!r} tag.error={self.error!r}'

    def __repr__(self) -> str:
        return f'Tag({self.init_value!r}, src={self.src!r}, chg_cmd={self.chg_cmd!r})'

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
    def value(self) -> Any:
        """Return current tag value from any way (ext sourced tag or internal value).

        :return: tag value
        """
        # get tag value from external source if available
        if self.src:
            self._set_value(self._get_src())
        # return internal tag value
        return self._value

    @value.setter
    def value(self, value: Optional[TAG_TYPE]) -> None:
        """Set value of tag.

        :param value: value of tag
        """
        # set internal value
        self._set_value(value)
        # notify external source if available
        if self.src:
            self._set_src(self._value)

    @property
    def error(self) -> bool:
        """ Return True is Tag have error status set. """
        # read error status from external source
        if isinstance(self.src, DataSource):
            return self.src.error()
        # read error status from internal store
        else:
            return self._error

    @error.setter
    def error(self, value: bool) -> None:
        """ Set the error status of tag (useless for externally sourced). """
        self._error = value

    def set(self, value: Optional[TAG_TYPE]) -> None:
        """ An helper to let user set the val property in lambda usage context. """
        self.value = value
