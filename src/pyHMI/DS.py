import sys
import traceback
from typing import Callable, Optional, Union
from . import logger
from .Tag import DataSource, Tag
from .Misc import auto_repr


class TagError(Exception):
    pass


def no_error(tag: Tag) -> Tag:
    """ Raise TagError for erroneous tag. """
    if tag.error:
        raise TagError
    return tag


class GetCmd(DataSource):
    """ A basic data source to get data from a python function. """

    def __init__(self, command: Callable) -> None:
        # args
        self.command = command
        # private
        self._error = False

    def __repr__(self):
        return auto_repr(self, export_t=('command',))

    def get(self) -> Optional[Tag.TAG_TYPE]:
        try:
            cmd_value = self.command()
            self._error = False
            return cmd_value
        except TagError:
            self._error = True
            return
        except Exception as e:
            tb_obj = sys.exc_info()[2]
            filename, line_number, _function_name, _text = traceback.extract_tb(tb_obj)[-1]
            logger.warning(f'get command failed (except "{e}") at {filename}:{line_number}')
            self._error = True
            return

    def set(self, value: Tag.TAG_TYPE) -> None:
        raise ValueError(f'cannot write on read-only Tag')

    def error(self) -> bool:
        return self._error


class TagOp(DataSource):
    """ A basic data source to get data from a python function. """

    def __init__(self, a: Union[Tag, Tag.TAG_TYPE], operator: Callable,
                 b: Optional[Union[Tag, Tag.TAG_TYPE]] = None) -> None:
        # args
        self.a = a
        self.operator = operator
        self.b = b

    @property
    def _a_value(self) -> Tag.TAG_TYPE:
        return self.a.value if isinstance(self.a, Tag) else self.a

    @property
    def _b_value(self) -> Optional[Tag.TAG_TYPE]:
        return self.b.value if isinstance(self.b, Tag) else self.b

    @property
    def _a_error(self) -> bool:
        return self.a.error if isinstance(self.a, Tag) else False

    @property
    def _b_error(self) -> bool:
        return self.b.error if isinstance(self.b, Tag) else False

    def get(self) -> Union[bool, int, float, str, bytes, None]:
        # single arg (a) or dual args (a, b) operation
        if self._b_value is None:
            return self.operator(self._a_value)
        else:
            return self.operator(self._a_value, self._b_value)

    def set(self, _value: Tag.TAG_TYPE) -> None:
        raise ValueError(f'cannot write on read-only Tag')

    def error(self) -> bool:
        return self._a_error or self._b_error
