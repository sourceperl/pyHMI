""" Test Tag and generic data sources """

import operator as op
from typing import Any, Optional

import pytest

from pyHMI.DS import GetCmd, TagOp, no_error
from pyHMI.Tag import Tag


def tag_expect(tag: Tag, value: Any, error: bool):
    assert tag.value == value, f'value property mismatch (expected: {value} get: {tag.value})'
    assert tag.error == error, f'error property mismatch (expected: {error} get: {tag.error})'


def test_basic():
    # startup default values
    tag_expect(Tag(42), value=42, error=False)
    tag_expect(Tag(42, init_error=True), value=42, error=True)
    # set a tag
    my_tag = Tag(0xc0ffee)
    # if value is set to nothing (None), tag keep last one
    my_tag.value = None
    tag_expect(my_tag, value=0xc0ffee, error=False)
    # value is set to anything, tag is set to anything
    my_tag.value = 0xfeed
    tag_expect(my_tag, value=0xfeed, error=False)
    # since Tag must have a type, None as default_value is disallow
    with pytest.raises(TypeError):
        Tag(None)  # type: ignore


def test_src_tag_op():
    # check some basic operations
    tag_expect(Tag(False, src=TagOp(Tag(False), op.not_)), value=True, error=False)
    tag_expect(Tag(False, src=TagOp(Tag(2.0), op.lt, 3.0)), value=True, error=False)
    tag_expect(Tag(False, src=TagOp(Tag(4.0), op.lt, 3.0)), value=False, error=False)
    # test the effect of the source disabled flag
    tag_expect(Tag(False, src=TagOp(Tag(False), op.not_), src_enabled=False), value=False, error=False)
    # tag error is propagate, value is set
    tag_expect(Tag(False, src=TagOp(Tag(False, init_error=True), op.not_)), value=True, error=True)
    a_tag = Tag(0xfeed)
    b_tag = Tag(0)
    tst_tag = Tag(0xc0ffee, src=TagOp(a_tag, op.floordiv, b_tag))
    # an except occur, value is keep and error flag is set
    tag_expect(tst_tag, value=0xc0ffee, error=True)
    # remove the except condition, get new value and turn off error flag
    b_tag.value = 1
    tag_expect(tst_tag, value=0xfeed, error=False)


def test_src_get_cmd():
    # some test with history context
    class GetCmdTest:
        def __init__(self, default: int) -> None:
            self._tag = Tag(default, src=GetCmd(self.get_cmd))
            self._ret = None

        def get_cmd(self):
            if self._ret == 0xdead:
                raise RuntimeError('get is dead')
            return self._ret

        def expect(self, for_ret: Optional[int], val: int, err: bool):
            self._ret = for_ret
            tag_expect(self._tag, value=val, error=err)

    get_cmd_test = GetCmdTest(default=0xdef)
    # get_cmd return None after init -> get default tag value
    get_cmd_test.expect(for_ret=None, val=0xdef, err=False)
    # get_cmd return 0xfeed -> tag set to 0xfeed
    get_cmd_test.expect(for_ret=0xfeed, val=0xfeed, err=False)
    # get_cmd return None -> tag keep last value (no error)
    get_cmd_test.expect(for_ret=None, val=0xfeed, err=False)
    # get_cmd raise an except -> tag keep last value (with error)
    get_cmd_test.expect(for_ret=0xdead, val=0xfeed, err=True)
    # get_cmd return 0xc0ffee -> tag set to 0xc0ffee (no error)
    get_cmd_test.expect(for_ret=0xc0ffee, val=0xc0ffee, err=False)

    # test the effect of the source enabled flag
    tag_expect(Tag(False, src=GetCmd(lambda: True)), value=True, error=False)
    tag_expect(Tag(False, src=GetCmd(lambda: True), src_enabled=False), value=False, error=False)
    tag_expect(Tag(False, init_error=True, src=GetCmd(lambda: True)), value=True, error=False)
    tag_expect(Tag(False, init_error=True, src=GetCmd(lambda: True), src_enabled=False), value=False, error=True)

    # some tests with error handling
    tag_1 = Tag(init_value='O', init_error=False)
    tag_2 = Tag(init_value='K', init_error=False)
    # no error
    tag_expect(Tag('last', src=GetCmd(lambda: no_error(tag_1).value + no_error(tag_2).value)),
               value='OK', error=False)
    tag_expect(Tag('last', src=GetCmd(lambda: tag_1.value + tag_2.value, error_cmd=lambda: tag_1.error or tag_2.error)),
               value='OK', error=False)
    # with an error
    tag_1.error = True
    tag_expect(Tag('last', src=GetCmd(lambda: no_error(tag_1).value + no_error(tag_2).value)),
               value='last', error=True)
    tag_expect(Tag('last', src=GetCmd(lambda: tag_1.value + tag_2.value, error_cmd=lambda: tag_1.error or tag_2.error)),
               value='OK', error=True)
    # test "error_on_none" arg: keep last value and set error flag if get_cmd return None
    tag_expect(Tag('last', src=GetCmd(lambda: None, error_on_none=True)),
               value='last', error=True)


def test_chg_cmd():
    # change command apply to externaly sourced Tag
    # not
    tag_expect(Tag(False, src=GetCmd(lambda: True), chg_cmd=op.not_), value=False, error=False)
    # scale
    tag_expect(Tag(0, src=GetCmd(lambda: 10), chg_cmd=lambda x: 3*x+5), value=35, error=False)
    # transform str
    tag_expect(Tag('', src=GetCmd(lambda: 'case'), chg_cmd=lambda x: x.upper()), value='CASE', error=False)
    # except behaviour
    my_value = 0
    my_tag = Tag(10, src=GetCmd(lambda: my_value), chg_cmd=lambda x: 1//x)
    tag_expect(my_tag, value=10, error=True)
    my_value = 1
    tag_expect(my_tag, value=1, error=False)
    # chg_cmd don't apply if no external src
    tag_expect(Tag(42, chg_cmd=lambda _x: 100), value=42, error=False)
