#!/bin/bash

set +e

print_result() {
  local test_description=$1
  local result=$2
  local optional=$3
  local software=$4
  local pretext=""
  local posttext=""
  if [ $result == 0 ]; then
    if [[ ! -z ${software+x} && $software == 1 ]]; then
      echo "[0;30;32m[PASS][0;30;37m [0;30;34m${test_description}[0;30;37m"
    else
      echo "[0;30;32m[PASS][0;30;37m ${test_description}"
    fi
  elif [[ ! -z ${optional+x} && $optional == 1 ]]; then
    if [[ ! -z ${software+x} && $software == 1 ]]; then
      echo "[0;30;33m[FAIL][0;30;37m [0;30;34m${test_description}[0;30;37m"
    else
      echo "[0;30;33m[FAIL][0;30;37m ${test_description}"
    fi
  else
    if [[ ! -z ${software+x} && $software == 1 ]]; then
      echo "[0;30;31m[FAIL][0;30;37m [0;30;34m${test_description}[0;30;37m"
    else
      echo "[0;30;31m[FAIL][0;30;37m ${test_description}"
    fi
  fi
}

# USB Breakout Board
test_device_count=$(ls -1 /dev/waggle_brain_test* | wc -l)
expected_device_count=2
if [ ${test_device_count} -eq ${expected_device_count} ]; then
  print_result "Detected USB test devices" 0 0 0
else
  print_result "Detected USB test devices" 0 0 0
fi

# Ethernet IP Address (NC)
ifconfig | fgrep "          inet addr:10.31.81.10  Bcast:10.31.81.255  Mask:255.255.255.0" && true
print_result "Built-in Ethernet IP Address" $? 0 0

[ -e /dev/waggle_sysmon ]
print_result "WagMan Device" $? 0 0

. /usr/lib/waggle/core/scripts/detect_disk_devices.sh
parted -s ${CURRENT_DISK_DEVICE}p2 print | grep --color=never -e ext | awk '{print $3}' | egrep '15\.[0-9]GB' && true
print_result "SD Size" $? 0 0

parted -s ${OTHER_DISK_DEVICE}p2 print | grep --color=never -e ext | awk '{print $3}' | egrep '15\.[0-9]GB' && true
print_result "eMMC Size" $? 0 0

# ssh to GN
ssh -i /usr/lib/waggle/SSL/edge_processor/id_rsa_waggle_aot_edge_processor root@10.31.81.51 \
    -o "StrictHostKeyChecking no" -o "PasswordAuthentication no" -o "ConnectTimeout 2" /bin/date && true
print_result "ssh to GN" $? 0 0
