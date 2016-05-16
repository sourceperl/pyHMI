#!/bin/bash

# check root user
if [[ $EUID -ne 0 ]]; then
   echo "You must be root to do this." 1>&2
   exit 1
fi

# start as daemon
nohup ./mbus_server.py 0<&- 1>/dev/null 2>&1 &
