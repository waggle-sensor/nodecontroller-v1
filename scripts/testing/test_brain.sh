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
expected_ids=("07b43408-4157-491b-b527-27f0c09eabe6" "bebc2419-a049-4966-b9f1-cd16fad854f8" "ffdb5e6d-bf3d-4f77-aaaa-9cc91b1218d3" "b6e874a0-21b3-4373-bc5f-7b44f70ccddd")
ids=$(blkid | grep -e /dev/sda1 -e /dev/sdb1 -e /dev/sdc1 -e /dev/sdd1 | sed -e 's/..* UUID="//' -e 's/" TYPE..*//')
for expected_id in $expected_ids; do
  found_id=0
  for id in ids; do
    if [ "$id" == "$expected_id" ]; then
      found_id=1
      break
    fi
  done
  if [ $found_id -eq 1 ]; then
    print_result "Detected USB drive $expected_id" 0 0 0
  else
    print_result "Detected USB drive $expected_id" 1 0 0
  fi
done

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
ssh -i /usr/lib/waggle/SSL/guest/id_rsa_waggle_aot_guest_node root@10.31.81.51 \
    -o "StrictHostKeyChecking no" -o "PasswordAuthentication no" -o "ConnectTimeout 2" /bin/date && true
print_result "ssh to GN" $? 0 0
