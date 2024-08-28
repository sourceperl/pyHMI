#!/bin/sh

docker container rm -f pytest-redis
docker network rm pytest-net

