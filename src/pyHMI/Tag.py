import logging
import sys
import traceback
from typing import Any, Callable, Optional, Union, get_args

TAG_TYPE = Union[bool, int, float, str, bytes]

logger = logging.getLogger(__name__)


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

    def set(self, value: Any) -> None:
        """ Method call by Tag class to set value in datasource. """
        pass

    def error(self) -> bool:
        """ Method call by Tag class to retrieve error status from datasource. """
        return False

    def sync(self) -> bool:
        """ Try to synchronize the data source with its target. (e.g. trigger an immediate write to a DB). """
        raise NotImplemented('this method is not implemented in this data source')


class Tag:
    def __init__(self, init_value: TAG_TYPE, init_error: bool = False,
                 src: Optional[DataSource] = None, chg_cmd: Optional[Callable] = None,
                 src_enabled: bool = True) -> None:
        """Constructor

        Abstract access to project tags.

        :param first_value: initial value of the tag
        :param src: an external data source like RedisKey
        :param chg_cmd: a method to change tag value (scale, limit value...)
        :param src_enabled: enabled data source flag
        """
        # runtime type check
        if not isinstance(init_value, get_args(TAG_TYPE)):
            raise TypeError(f'first_value type must be in {get_args(TAG_TYPE)}')
        # args
        self.init_value = init_value
        self.init_error = init_error
        self.src = src
        self.chg_cmd = chg_cmd
        self.src_enabled = src_enabled
        # private
        self._value = self.init_value
        self._error = self.init_error
        self._chg_cmd_error = False
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
        # if a change command is defined and a value is available
        if self.chg_cmd and value is not None:
            # try to alter or transform value with it
            try:
                chg_cmd_return = self.chg_cmd(value)
                self._chg_cmd_error = False
                return chg_cmd_return
            except Exception as e:
                tb_obj = sys.exc_info()[2]
                filename, line_number, _function_name, _text = traceback.extract_tb(tb_obj)[-1]
                logger.warning(f'change command failed (except "{e}") at {filename}:{line_number}')
                self._chg_cmd_error = True
                return
        else:
            # pass through if chg_cmd is unset or None value
            return value

    @property
    def value(self) -> Any:
        """Return current tag value from any way (ext sourced tag or internal value).

        :return: tag value
        """
        # get tag value from a data source if set
        if self.src and self.src_enabled:
            get_src_return = self._get_src()
            # keep internal value unchange if data source return None
            if get_src_return is not None:
                self._value = get_src_return
        # return internal tag value
        return self._value

    @value.setter
    def value(self, value: Optional[TAG_TYPE]) -> None:
        """Set value of tag.

        :param value: value of tag
        """
        prev_value = self._value
        # set internal value
        if value is not None:
            self._value = value
        # notify external source if set
        if self.src and self.src_enabled:
            self._set_src(self._value)
        # notify user
        self.on_set(value, prev_value)

    @property
    def error(self) -> bool:
        """ Return True is Tag have error status set. """
        # read error status from external source
        if isinstance(self.src, DataSource) and self.src_enabled:
            return self.src.error() or self._chg_cmd_error
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

    def on_set(self, value: Optional[TAG_TYPE], prev_value: TAG_TYPE):
        """ A callback for user purposes to be informed when the value is set. """
        pass
