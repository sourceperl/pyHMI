""" Test of every DS_Redis DataSource subclass """

from typing import List, Union
import os
import random
import pytest
import redis
from pyHMI.DS_Redis import RedisDevice, RedisGetKey, RedisSetKey, RedisPublish, RedisSubscribe
from .utils import build_random_str


REDIS_HOST = 'pyhmi_redis'


@pytest.fixture
def redis_cli():
    # setup code
    redis_cli = redis.Redis(host=REDIS_HOST, decode_responses=False)
    # pass to test functions
    yield redis_cli
    # teardown code
    # redis_cli.flushall()
    redis_cli.close()


def test_redis_up(redis_cli):
    redis_cli.ping()


def test_redis_key(redis_cli):
    # some functions
    def sync_key_wait_ok(redis_key: Union[RedisGetKey, RedisSetKey]):
        """ Run request and wait for a valid result """
        if not redis_key.sync():
            raise RuntimeError('unable to request a sync')
        if not redis_key.sync_evt.wait(timeout=5.0):
            raise RuntimeError('sync request not processed')
        if redis_key.error():
            raise RuntimeError('request processing error')

    # init device
    redis_device = RedisDevice(host=REDIS_HOST)
    
    # test the transfer of all supported data types
    # build test pattern list and run it
    test_pat_l: List[tuple] = []
    for _ in range(10):
        # bool, int, float (with special values), str and bytes
        test_pat_l.extend([(False, bool), (True, bool)])
        test_pat_l.append((random.randint(-0xffff_ffff_ffff_ffff, 0xffff_ffff_fff_fff), int))
        test_pat_l.append((float('+inf'), float))
        test_pat_l.append((float('-inf'), float))
        test_pat_l.append((float('nan'), float))
        test_pat_l.append((1_000_000 * random.random() - 500_000, float))
        test_pat_l.append((build_random_str(), str))
        test_pat_l.append((os.urandom(random.randint(1, 255)), bytes))
    # run it
    for value, _type in test_pat_l:
        # set value
        foo_set_key = RedisSetKey(redis_device, 'foo', type=_type)
        foo_set_key.set(value)
        sync_key_wait_ok(foo_set_key)
        # get value
        foo_get_key = RedisGetKey(redis_device, 'foo', type=_type)
        sync_key_wait_ok(foo_get_key)
        # check transfer ok
        assert foo_get_key.get() == pytest.approx(value, nan_ok=True)

    RedisSetKey