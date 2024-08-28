""" Test of every DS_Redis DataSource subclass """

import pytest
import redis
from pyHMI.DS_Redis import RedisDevice, RedisGetKey, RedisSetKey, RedisPublish, RedisSubscribe


@pytest.fixture
def redis_cli():
    # setup code
    redis_cli = redis.Redis(host='pytest-redis', decode_responses=False)
    # pass to test functions
    yield redis_cli
    # teardown code
    redis_cli.flushall()
    redis_cli.close()


def test_truc(redis_cli):
    redis_cli.ping()

