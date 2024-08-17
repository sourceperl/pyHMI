from typing import Callable, Union
from . import logger
from .Tag import DataSource
from .Misc import auto_repr


class GetCmd(DataSource):
    """ A basic data source to get data from a python function. """

    def __init__(self, command: Callable) -> None:
        # args
        self.command = command
        # private
        self._error = False

    def __repr__(self):
        return auto_repr(self)

    def get(self) -> Union[bool, int, float, str, bytes, None]:
        try:
            cmd_value = self.command()
            self._error = False
            return cmd_value
        except Exception as e:
            logger.warning(f'command processing failed (except "{e}") in {self!r}')
            self._error = True
            return

    def set(self, value: Union[bool, int, float, str, bytes]) -> None:
        raise ValueError(f'cannot write read-only {self!r}')

    def error(self) -> bool:
        return self._error
