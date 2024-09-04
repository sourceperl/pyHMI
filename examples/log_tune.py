#!/usr/bin/env python3

import logging
import time

import pyHMI
import pyHMI.DS_Redis
from pyHMI.DS_Redis import RedisDevice, RedisSetKey
from pyHMI.Tag import Tag

# logging setup
logging.basicConfig(format='%(asctime)s - %(levelname)-8s - %(module)s - %(message)s', level=logging.DEBUG)
# turn on debug for global pyHMI package
pyHMI.logger.setLevel(logging.DEBUG)
# or turn on debug for redis data source only
# pyHMI.DS_Redis.logger.setLevel(logging.DEBUG)


class Tags:
    FOO = Tag(0, src=RedisSetKey(RedisDevice(), 'foo', type=int, on_set=True))


logging.debug(f'app start')

# main loop
while True:
    for i in range(0, 100):
        Tags.FOO.set(i)
        time.sleep(1.0)
