#!/usr/bin/env python3

import logging
import time
from pyHMI.DS_Redis import RedisDevice, RedisSetKey
from pyHMI.Tag import Tag
from pyHMI import logger, logger_modbus, logger_redis


# logging setup
logging.basicConfig(format='%(asctime)s - %(levelname)-8s - %(module)s - %(message)s', level=logging.DEBUG)
# pyHMI: fine tuning of the log
logger.setLevel(logging.WARNING)
# log_modbus.setLevel(logging.DEBUG)
logger_redis.setLevel(logging.DEBUG)


class Tags:
    FOO = Tag(0, src=RedisSetKey(RedisDevice(), 'foo', type=int, sync_on_set=True))


# main loop
while True:
    for i in range(0, 100):
        Tags.FOO.set(i)
        time.sleep(1.0)
