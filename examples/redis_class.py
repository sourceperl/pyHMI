#!/usr/bin/env python3

import logging
import random
import time
from pyHMI.DS_Redis import RedisDevice, RedisPublish, RedisSubscribe, RedisGetKey, RedisSetKey
from pyHMI.Tag import Tag


# logging setup
logging.basicConfig(format='%(asctime)s - %(levelname)-8s - %(message)s', level=logging.DEBUG)


class Devices:
    def __init__(self) -> None:
        self.redis = RedisDevice(host='localhost')


class Tags:
    def __init__(self, devices: Devices) -> None:
        self.FOO_KEY_READ = Tag('', src=RedisGetKey(devices.redis, 'foo', type=str, request_cyclic=True))
        self.FOO_KEY_WRITE = Tag('', src=RedisSetKey(devices.redis, 'foo', type=str, request_on_set=True))
        self.PUB_PUB_CHANNEL = Tag('', src=RedisPublish(devices.redis, 'pub', type=str))
        self.SUB_PUB_CHANNEL = Tag('', src=RedisSubscribe(devices.redis, 'pub', type=str))
        self.TMP_KEY_READ = Tag(0.0, src=RedisGetKey(devices.redis, 'tmp', type=float, request_cyclic=True))
        self.TMP_KEY_WRITE = Tag(0.0, src=RedisSetKey(devices.redis, 'tmp', type=float, request_cyclic=True, ex=5))


# init tags and datasources
devices = Devices()
tags = Tags(devices)

# main loop
while True:
    for i in range(0, 100):
        tags.FOO_KEY_WRITE.value = f'{i=}'
        print(f'FOO_KEY_READ: {tags.FOO_KEY_READ!s}')
        tags.PUB_PUB_CHANNEL.value = f'{i=}'
        print(f'SUB_PUB_CHANNEL: {tags.SUB_PUB_CHANNEL!s}')
        tags.TMP_KEY_WRITE.value = round(random.random() * 1_000, 3)
        print(f'TMP_KEY_READ: {tags.TMP_KEY_READ!s}')
        time.sleep(1.0)
