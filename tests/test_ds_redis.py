""" Test of every DS_Redis DataSource subclass """

from typing import Union
import pytest
import redis
from pyHMI.DS_Redis import RedisDevice, RedisGetKey, RedisSetKey, RedisPublish, RedisSubscribe


REDIS_HOST = 'pyhmi_redis'


@pytest.fixture
def redis_cli():
    # setup code
    redis_cli = redis.Redis(host=REDIS_HOST, decode_responses=False)
    # pass to test functions
    yield redis_cli
    # teardown code
    #redis_cli.flushall()
    redis_cli.close()


def run_and_wait_ok(request):
    """ Run request and wait for a valid result """
    if not request.run():
        raise RuntimeError('unable to run request')
    if not request.run_done_evt.wait(timeout=5.0):
        raise RuntimeError('request not processed')
    # if request.error:
    #     raise RuntimeError('request processing error')


def test_redis_up(redis_cli):
    redis_cli.ping()


def test_redis_key(redis_cli):
    redis_device = RedisDevice(host=REDIS_HOST)
    foo_set_key = RedisSetKey(redis_device, 'foo', type=int)
    foo_set_key.set(42)
    run_and_wait_ok(foo_set_key.request)

    foo_get_key = RedisGetKey(redis_device, 'foo', type=int)
    if foo_get_key.request.run():
        foo_get_key.request.run_done_evt.wait(timeout=0.2)
    assert foo_get_key.get() == 42
