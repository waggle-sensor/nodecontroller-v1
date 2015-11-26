#!/bin/bash

echo
echo -n "Data Cache:    "
/etc/init.d/data_cache.sh status

echo
echo -n "Communication: "
/etc/init.d/communications.sh status

echo
echo -n "Sensor:        "
/etc/init.d/start_sensor.sh status

echo