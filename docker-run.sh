#!/bin/sh

docker network create pytest-net
docker run --network pytest-net --name pytest-redis -d redis:7.0.15
docker build -t pytest . && docker run --network pytest-net --volume $(pwd):/app --rm -it pytest
