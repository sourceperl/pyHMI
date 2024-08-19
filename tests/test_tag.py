import operator as op
import pytest
from typing import Any, Optional
from pyHMI.Tag import Tag
from pyHMI.DS import GetCmd, TagOp


def tag_expect(tag: Tag, value: Any, error: bool):
    assert tag.value == value, f'val property mismatch (expected: {value} get: {tag.value})'
    assert tag.error == error, f'err property mismatch (expected: {error} get: {tag.error})'


def get_raise():
    raise RuntimeError


def test_basic():
    # startup default values
    my_tag = Tag(0)
    tag_expect(my_tag, value=0, error=False)
    # when value is set to None
    my_tag.value = None
    tag_expect(my_tag, value=0, error=True)
    # when value is set to valid value
    my_tag.value = 42
    tag_expect(my_tag, value=42, error=False)

    # since Tag must have a type, None as default_value is disallow
    with pytest.raises(TypeError):
        Tag(None)  # type: ignore


def test_src():
    class GetCmdTest:
        def __init__(self, default: int) -> None:
            self._tag = Tag(default, src=GetCmd(self.get_cmd))
            self._ret = None

        def get_cmd(self):
            if self._ret == 0:
                raise RuntimeError
            return self._ret

        def expect(self, for_ret: Optional[int], val: int, e_val: Optional[int], err: bool):
            self._ret = for_ret
            tag_expect(self._tag, value=val, error=err)

    # some test with history context
    get_cmd_test = GetCmdTest(default=55)
    # get None after init -> return default tag value
    get_cmd_test.expect(for_ret=None, val=55, e_val=None, err=False)
    # get 10 -> return 10
    get_cmd_test.expect(for_ret=10, val=10, e_val=10, err=False)
    # get None -> return last value with error
    # get_cmd_test.expect(for_ret=None, val=10, e_val=None, err=True)
    # get 100  -> return value with no error
    get_cmd_test.expect(for_ret=100, val=100, e_val=100, err=False)
    # get raise an except -> return last value with error
    get_cmd_test.expect(for_ret=0, val=100, e_val=None, err=True)
    # get 50 -> return value with no error
    get_cmd_test.expect(for_ret=50, val=50, e_val=50, err=False)

    # some test without history context
    # check some basic operations
    tag_expect(Tag(False, src=TagOp(Tag(False), op.not_)), value=True, error=False)
    tag_expect(Tag(False, src=TagOp(Tag(22.0), op.lt, 3.0)), value=False, error=False)
    tag_expect(Tag(False, src=TagOp(Tag(22.0), op.gt, 3.0)), value=True, error=False)
    # check tag error propagate
    tag_expect(Tag(False, src=TagOp(Tag(2.0, init_error=True), op.gt, 1.0)), value=True, error=True)


def test_chg_cmd():
    # change command apply to externaly sourced Tag
    # not
    tag_expect(Tag(False, src=GetCmd(lambda: True), chg_cmd=op.not_), value=False, error=False)
    # scale
    tag_expect(Tag(0, src=GetCmd(lambda: 10), chg_cmd=lambda x: 3*x+5), value=35, error=False)
    # transform str
    tag_expect(Tag('', src=GetCmd(lambda: 'case'), chg_cmd=lambda x: x.upper()), value='CASE', error=False)
    # chg_cmd don't apply if no external src
    tag_expect(Tag(42, chg_cmd=lambda _x: 100), value=42, error=False)
