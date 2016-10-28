#!/bin/bash

#if /home/waggle/start_test exists:
#  - run tests > log file
#  - rm /home/waggle/start_test
#  - mount other disk partition 2
#  - touch <MOUNT_POINT>/home/waggle/continue_test
#  if on SD:
#    - wagman-client bs 0 emmc
#  else:
#    - wagman-client bs 0 sd
#  - wagman-client stop 0 0
#if /home/waggle/continue_test exists:
#  - run tests > log file
#  - rm /home/waggle/start_test
#  if on eMMC:
#    - mount other disk partition 2
#    - touch <MOUNT_POINT>/home/waggle/finish_test
#  else:
#    - run "finish" code
#if /home/waggle/finish_test and on SD:
#    - mount other disk partition 2
#    - merge eMMC and SD test logs
#    - rm /home/waggle/finish_test

function run_tests {
}

# determine Odroid model 
# - sets ${ODROID_MODEL} to either 'C' or 'XU3'
. /usr/lib/waggle/core/scripts/detect_odroid_model.sh

# Determine root and alternate boot medium root device paths
boot_device=$(df | grep '/$' | awk '{print $1}' | sed 's/p2//')


start_file=/home/waggle/start_test
continue_file=/home/waggle/continue_test
finish_file=/home/waggle/finish_test
if [ -e ${start_file} ] ; then
  run_tests
  rm ${start_file}
#  - mount other disk partition 2
  mount 
#  - touch <MOUNT_POINT>/home/waggle/continue_test
#  if on SD:
#    - wagman-client bs 0 emmc
#  else:
#    - wagman-client bs 0 sd
#  - wagman-client stop 0 0
fi
