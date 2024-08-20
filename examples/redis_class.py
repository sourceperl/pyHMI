#!/usr/bin/env python3

from pyHMI.DS_Redis import RedisDevice, RedisPub, RedisKey
from pyHMI.Tag import Tag
import time


class Devices:
    def __init__(self) -> None:
        class Redis:
            def __init__(self) -> None:
                self.device = RedisDevice(host='localhost')
                self.key_foo_get = RedisKey(self.device, 'foo', type=str, update_cyclic=True)
                self.key_foo_set = RedisKey(self.device, 'foo', type=str, write=True, update_cyclic=True)
                self.pub_my_channel = RedisPub(self.device, 'my_channel')
        self.redis = Redis()



class Tags:
    def __init__(self, devices: Devices) -> None:
        self.FOO_KEY_READ = Tag('', src=devices.redis.key_foo_get)
        self.FOO_KEY_WRITE = Tag('', src=devices.redis.key_foo_set)
        self.PUB_MY_CHANNEL = Tag('', src=devices.redis.pub_my_channel)


# init tags and datasources
devices = Devices()
tags = Tags(devices)

# main loop
while True:
    for i in range(0, 100):
        tags.FOO_KEY_WRITE.value = f'{i=}'
        tags.PUB_MY_CHANNEL.value = f'{i=}'
        print(tags.FOO_KEY_READ)
        time.sleep(1.0)
