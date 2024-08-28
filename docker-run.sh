#!/bin/sh

docker build -t pytest . && docker run --network host --volume $(pwd):/app --rm -it pytest
