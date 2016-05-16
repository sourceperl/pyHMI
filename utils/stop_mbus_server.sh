#!/bin/bash

# check root user
if [[ $EUID -ne 0 ]]; then
   echo "You must be root to do this." 1>&2
   exit 1
fi

# stop daemon
kill $(ps -fade | grep mbus_server.py | grep -v grep | awk '{print $2}')
