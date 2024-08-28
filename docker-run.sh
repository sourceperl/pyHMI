#!/bin/sh

# user defines
TEST_NAME="pyhmi"
PYTHON_VERSION="3.8"
REDIS_VERSION="7.0.15"

# internal
NET_NAME=${TEST_NAME}_net
REDIS_CONT_NAME=${TEST_NAME}_redis
APP_IMG_NAME=${TEST_NAME}_app_img

# run stack
docker network create ${NET_NAME}
docker run --network ${NET_NAME} --name ${REDIS_CONT_NAME} -d redis:${REDIS_VERSION}
docker build --build-arg BASE_IMAGE=python:${PYTHON_VERSION} -t ${APP_IMG_NAME} .
docker run --network ${NET_NAME} --volume $(pwd):/app --rm -it ${APP_IMG_NAME}

# clean stack
docker container rm -f ${REDIS_CONT_NAME}
docker network rm ${NET_NAME}
