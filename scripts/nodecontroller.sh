#!/bin/bash

echo
echo -n "Data Cache:                   "
/etc/init.d/data_cache.sh status

echo
echo -n "Communication:                "
/etc/init.d/communications.sh status

echo
echo -n "core sense:                   "
/etc/init.d/waggle_core_sense.sh status

if [ -e /etc/init.d/WagMan_start.sh ] ; then
  echo
  echo -n "WagMan:                       "
  /etc/init.d/WagMan_start.sh status
fi
 
if [ -e /etc/init.d/heartbeat_setup_start.sh ] ; then
  echo
  echo -n "heartbeat_setup_start.sh:     "
  /etc/init.d/heartbeat_setup_start.sh status
fi

if [ -e /etc/init.d/heartbeat_start.sh ] ; then
  echo
  echo -n "heartbeat_start.sh:           "
  /etc/init.d/heartbeat_start.sh status
fi






echo