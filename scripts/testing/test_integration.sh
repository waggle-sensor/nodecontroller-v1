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

[ -e /dev/waggle_coresense ]
print_result "Coresense Device" $? 0 0

devices=("alphasense" "gps_module" "attwwan")
device_names=("Alphasense" "GPS" "Modem")
for i in $(seq 0 `expr ${#devices[@]} - 1`); do
  device=${devices[i]}
  device_name=${device_names[i]}
  [ -e /dev/$device ]
  print_result "Optional $device_name Device" $? 1 0
done

lsusb | grep 1bc7:0021
if [ $? -eq 0 ]; then
  # Found USB Modem Device
  print_result "Modem USB" 0 0 0

  ifconfig | grep ppp0 -A 1 | fgrep "inet addr:"
  print_result "Modem IP Address" $? 0 0
else
  # No USB Modem Device Present
  ifconfig | grep -A 1 enx | grep 'inet addr:'
  exit_code=$?
  if [ $exit_code -ne 0 ]; then
    # give networking another try after a brief rest
    sleep 10
    ifconfig | grep -A 1 enx | grep 'inet addr:'
    exit_code=$?
  fi
  print_result "USB Ethernet IP Address" $exit_code 0 0
fi
