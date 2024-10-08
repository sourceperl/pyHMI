""" Test of every DS_Redis DataSource subclass """

import os
import random
from typing import Any, List, Optional, Union

import pytest
import redis

from pyHMI.DS_Redis import (KEY_TYPE, RedisDevice, RedisGetKey, RedisPublish,
                            RedisSetKey, RedisSubscribe)

from .utils import build_random_str

# some constants
REDIS_HOST = 'pyhmi_redis'


# redis fixtures
@pytest.fixture
def cli():
    # setup code
    cli = redis.Redis(host=REDIS_HOST, decode_responses=False)
    # pass to test functions
    yield cli
    # teardown code
    cli.flushall()
    cli.close()


@pytest.fixture
def dev():
    # setup code
    dev = RedisDevice(host=REDIS_HOST)
    # pass to test functions
    yield dev
    # teardown code
    pass


# tests functions
def test_redis_up(cli):
    cli.ping()


def test_redis_key(cli, dev):
    # some functions
    def sync_key(redis_key: Union[RedisGetKey, RedisSetKey],
                 assert_error: Optional[bool] = None,
                 assert_get: Any = None, get_none: bool = False):
        """ Run request and wait for a valid result """
        if not redis_key.sync():
            raise RuntimeError('unable to request a sync')
        if not redis_key.is_sync_evt.wait(timeout=1.0):
            raise RuntimeError('sync request not processed')
        if assert_error is not None:
            assert redis_key.error() == assert_error, 'bad error() value'
        if assert_get is not None:
            assert redis_key.get() == assert_get, 'bad get() value'
        if get_none:
            assert redis_key.get() == None, 'get() should return None'

    # test the transfer of all supported data types
    # build test model list and run it
    model_l: List[tuple] = []
    for _ in range(10):
        # bool, int, float (with special values), str and bytes
        model_l.extend([(False, bool), (True, bool)])
        model_l.append((random.randint(-0xffff_ffff_ffff_ffff, 0xffff_ffff_fff_fff), int))
        model_l.append((float('+inf'), float))
        model_l.append((float('-inf'), float))
        model_l.append((float('nan'), float))
        model_l.append((1_000_000 * random.random() - 500_000, float))
        model_l.append((build_random_str(), str))
        model_l.append((os.urandom(random.randint(1, 255)), bytes))
    # run it
    for value, _type in model_l:
        # set value
        set_key = RedisSetKey(dev, 'foo', type=_type)
        set_key.set(value)
        sync_key(set_key)
        # get value
        get_key = RedisGetKey(dev, 'foo', type=_type)
        sync_key(get_key)
        # check transfer ok
        assert get_key.get() == pytest.approx(value, nan_ok=True)

    # deal with abnormal value
    # bool
    cli.set('foo', b'True')
    sync_key(RedisGetKey(dev, 'foo', type=bool), assert_error=False, assert_get=True)
    cli.set('foo', b'true')
    sync_key(RedisGetKey(dev, 'foo', type=bool), assert_error=True, get_none=True)
    # int
    cli.set('foo', b'12')
    sync_key(RedisGetKey(dev, 'foo', type=int), assert_error=False, assert_get=12)
    cli.set('foo', b'12.22')
    sync_key(RedisGetKey(dev, 'foo', type=int), assert_error=True, get_none=True)
    # int
    cli.set('foo', b'12')
    sync_key(RedisGetKey(dev, 'foo', type=float), assert_error=False, assert_get=12.0)
    cli.set('foo', b'12..22')
    sync_key(RedisGetKey(dev, 'foo', type=float), assert_error=True, get_none=True)
    # str
    cli.set('foo', b'ok')
    sync_key(RedisGetKey(dev, 'foo', type=str), assert_error=False, assert_get='ok')
    cli.set('foo', b'\xff\xff')
    sync_key(RedisGetKey(dev, 'foo', type=str), assert_error=True, get_none=True)
    # bytes
    cli.set('foo', b'ok')
    sync_key(RedisGetKey(dev, 'foo', type=bytes), assert_error=False, assert_get=b'ok')


def test_pubsub(cli, dev):
    # some class
    class SubTest:
        def __init__(self, type: type, pub: bytes, sub_get: Any, sub_error: bool) -> None:
            self.type = type
            self.pub = pub
            self.sub_get = sub_get
            self.sub_error = sub_error

    # test RedisPublish -> RedisSubscribe
    # init subscribe
    red_sub = RedisSubscribe(dev, 'my_desk', type=bool)
    red_sub.subscribe_evt.wait(timeout=1.0)
    # init publish
    red_pub = RedisPublish(dev, 'my_desk', type=bool)
    # run the same test with some types
    for _type, value in [(bool, False), (bool, True), (int, 0xc0ffee), (float, 0.42), (str, ''), (bytes, b'data')]:
        # load value type
        red_sub.type = red_pub.type = _type
        # reset receive event (subscribe part)
        red_sub.receive_evt.clear()
        # publish
        red_pub.set(value)
        # wait process done (publish part)
        if not red_pub.last_message or not red_pub.last_message.send_evt.wait(timeout=1.0):
            raise RuntimeError('unable to send publish message')
        # wait process done (subscribe part)
        if not red_sub.receive_evt.wait(timeout=1.0):
            raise RuntimeError('unable to receive publish message')
        # check subscribe value
        assert red_sub.get() == value

    # check error
    # init subscribe
    red_sub = RedisSubscribe(dev, 'foo', type=bool)
    red_sub.subscribe_evt.wait(timeout=1.0)
    # publish invalid/valid content for some types
    tst_l = [SubTest(type=bool, pub=b'False', sub_get=False, sub_error=False),
             SubTest(type=bool, pub=b'not_bool', sub_get=False, sub_error=True),
             SubTest(type=int, pub=b'123', sub_get=123, sub_error=False),
             SubTest(type=int, pub=b'abc', sub_get=123, sub_error=True),
             SubTest(type=float, pub=b'42.0', sub_get=42.0, sub_error=False),
             SubTest(type=float, pub=b'99..9', sub_get=42.0, sub_error=True),
             SubTest(type=str, pub=b'test', sub_get='test', sub_error=False),
             SubTest(type=str, pub=b'\xff\xff', sub_get='test', sub_error=True),
             SubTest(type=bytes, pub=b'bytes', sub_get=b'bytes', sub_error=False)]
    for tst in tst_l:
        # init redis_sub
        red_sub.type = tst.type
        red_sub.receive_evt.clear()
        # publish and wait red_sub is updated
        cli.publish('foo', tst.pub)
        red_sub.receive_evt.wait(timeout=1.0)
        # asserts
        assert red_sub.get() == tst.sub_get
        assert red_sub.error() == tst.sub_error
