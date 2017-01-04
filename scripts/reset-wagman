#!/bin/bash
set -e

# Documentation
# ODROID-C1+
# Connect PIN 27 to the SRE board to allow NC to reboot the Wagman.
# Pin: 27 GPIO: 76
# GND: 9 and 39
# The NC needs to be powered by the Wagman.
# Source: http://odroid.com/dokuwiki/doku.php?id=en:c1_gpio_default#

TIME_LOW=1.0
TIME_HIGH=1.0
GPIO_EXPORT=76
PIN=27

if [ ! -d /sys/class/gpio/gpio${GPIO_EXPORT} ] ; then
  set -x
  echo ${GPIO_EXPORT} > /sys/class/gpio/export
  set +x
fi

set -x
echo "out" > /sys/class/gpio/gpio${GPIO_EXPORT}/direction
set +x

echo 0  > /sys/class/gpio/gpio${GPIO_EXPORT}/value
sleep ${TIME_LOW}
echo 1 > /sys/class/gpio/gpio${GPIO_EXPORT}/value
sleep ${TIME_HIGH}
echo 0  > /sys/class/gpio/gpio${GPIO_EXPORT}/value
sleep ${TIME_LOW}


