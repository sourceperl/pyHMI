import operator as op
import pytest
from pyHMI.Tag import Tag, tag_op


def tag_expect(tag: Tag, val, e_val, err):
    assert tag.val == val, f'val property mismatch (expected: {val} get: {tag.val})'
    assert tag.e_val == e_val, f'e_val property mismatch (expected: {e_val} get: {tag.e_val})'
    assert tag.err == err, f'err property mismatch (expected: {err} get: {tag.err})'


def test_basic():
    # startup default values
    my_tag = Tag(0)
    tag_expect(my_tag, val=0, e_val=0, err=False)
    # when value is set to None
    my_tag.val = None
    tag_expect(my_tag, val=0, e_val=None, err=True)
    # when value is set to valid value
    my_tag.val = 42
    tag_expect(my_tag, val=42, e_val=42, err=False)


def test_src():
    pass


def test_get_cmd():
    class GetCmdTest:
        def __init__(self, default: int) -> None:
            self._tag = Tag(default, get_cmd=self.get_cmd)
            self._ret = None

        def get_cmd(self):
            if self._ret == 0:
                raise RuntimeError
            return self._ret

        def expect(self, for_ret, val, e_val, err):
            self._ret = for_ret
            tag_expect(self._tag, val=val, e_val=e_val, err=err)

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
    tag_expect(Tag(False, get_cmd=lambda: tag_op(Tag(False), op.not_)),
               val=True, e_val=True, err=False)
    tag_expect(Tag(False, get_cmd=lambda: tag_op(Tag(22.0), op.lt, 3.0)),
               val=False, e_val=False, err=False)
    tag_expect(Tag(False, get_cmd=lambda: tag_op(Tag(22.0), op.gt, 3.0)),
               val=True, e_val=True, err=False)
    tag_expect(Tag(False, get_cmd=lambda: tag_op(Tag(22.0, get_cmd=lambda: None), op.gt, 3.0)),
               val=False, e_val=None, err=True)


def test_chg_cmd():
    # check not
    tag = Tag(False, chg_cmd=op.not_)
    tag.set(True)
    assert tag.val == False

    # scale a value
    tag = Tag(0, chg_cmd=lambda x: 3*x+5)
    tag.set(10)
    assert tag.val == 35

    # except
    tag = Tag(0, chg_cmd=lambda x: 1/x)
    with pytest.raises(ZeroDivisionError):
        tag.set(0)
