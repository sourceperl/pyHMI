import operator as op
import pytest
from typing import Any, Optional
from pyHMI.Tag import Tag, tag_op
from pyHMI.DS import GetCmd


def tag_expect(tag: Tag, val: Any, err: bool):
    assert tag.val == val, f'val property mismatch (expected: {val} get: {tag.val})'
    assert tag.err == err, f'err property mismatch (expected: {err} get: {tag.err})'
    exp_eval = None if tag.err else val
    assert tag.e_val == exp_eval, f'e_val property mismatch (expected: {exp_eval} get: {tag.e_val})'


def test_basic():
    # startup default values
    my_tag = Tag(0)
    tag_expect(my_tag, val=0, err=False)
    # when value is set to None
    my_tag.val = None
    tag_expect(my_tag, val=0, err=True)
    # when value is set to valid value
    my_tag.val = 42
    tag_expect(my_tag, val=42, err=False)

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
            tag_expect(self._tag, val=val, err=err)

    # some test with history context
    get_cmd_test = GetCmdTest(default=55)
    # get None after init -> return default tag value
    get_cmd_test.expect(for_ret=None, val=55, e_val=None, err=True)
    # get 10 -> return value with no error
    get_cmd_test.expect(for_ret=10, val=10, e_val=10, err=False)
    # get None -> return last value with error
    get_cmd_test.expect(for_ret=None, val=10, e_val=None, err=True)
    # get 100  -> return value with no error
    get_cmd_test.expect(for_ret=100, val=100, e_val=100, err=False)
    # get raise an except -> return last value with error
    get_cmd_test.expect(for_ret=0, val=100, e_val=None, err=True)
    # get 50 -> return value with no error
    get_cmd_test.expect(for_ret=50, val=50, e_val=50, err=False)

    # some test without history context
    # check some basic operations
    tag_expect(Tag(False, src=GetCmd(lambda: tag_op(Tag(False), op.not_))),
               val=True, err=False)
    tag_expect(Tag(False, src=GetCmd(lambda: tag_op(Tag(22.0), op.lt, 3.0))),
               val=False, err=False)
    tag_expect(Tag(False, src=GetCmd(lambda: tag_op(Tag(22.0), op.gt, 3.0))),
               val=True, err=False)
    # check tag error propagate
    tag_expect(Tag(False, src=GetCmd(lambda: tag_op(Tag(22.0, src=GetCmd(lambda: None)), op.gt, 3.0))),
               val=False, err=True)


def test_chg_cmd():
    # change command apply to externaly sourced Tag
    # not
    tag_expect(Tag(False, src=GetCmd(lambda: True), chg_cmd=op.not_), val=False, err=False)
    # scale
    tag_expect(Tag(0, src=GetCmd(lambda: 10), chg_cmd=lambda x: 3*x+5), val=35, err=False)
    # transform str
    tag_expect(Tag('', src=GetCmd(lambda: 'case'), chg_cmd=lambda x: x.upper()), val='CASE', err=False)
    # chg_cmd don't apply if no external src
    tag_expect(Tag(42, chg_cmd=lambda _x: 100), val=42, err=False)
