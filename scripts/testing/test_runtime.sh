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

# Ethernet IP Address (NC)
ifconfig | fgrep "          inet addr:10.31.81.10  Bcast:10.31.81.255  Mask:255.255.255.0" && true
print_result "Built-in Ethernet IP Address" $? 0 0

cat /etc/waggle/node_id | egrep '[0-9a-f]{16}' && true
print_result "Node ID Set" $? 0 1

. /usr/lib/waggle/core/scripts/detect_mac_address.sh
cat /etc/hostname | fgrep "${MAC_STRING}${CURRENT_DISK_DEVICE_TYPE}" && true
print_result "Hostname Set" $? 0 1

units=("waggle-epoch" "waggle-heartbeat" "waggle-monitor-connectivity" \
       "waggle-monitor-shutdown" "waggle-monitor-system" \
       "waggle-monitor-wagman" "waggle-wagman-driver" "rabbitmq-server"\
       "waggle-core.target" "waggle-platform.target")
for unit in ${units[@]}; do
  systemctl status $unit | fgrep 'Active: active (running)' && true
  exit_code=$?
  if [ $exit_code -ne 0 ]; then
    # give systemctl status another try after a brief rest
    sleep 5
    systemctl status $unit | fgrep 'Active: active (running)' && true
    exit_code=$?
  fi
  print_result "$unit Service" $? 0 1
done

units=("waggle-wwan" "waggle-reverse-tunnel")
for unit in ${units[@]}; do
  systemctl status $unit | fgrep -e 'Active: active (running)' -e 'Active: activating (auto-restart)' && true
  exit_code=$?
  if [ $exit_code -ne 0 ]; then
    # give systemctl status another try after a brief rest
    sleep 5
    systemctl status $unit | fgrep -e 'Active: active (running)' -e 'Active: activating (auto-restart)' && true
    exit_code=$?
  fi
  print_result "$unit Service" $exit_code 0 1
done


directories=("/usr/lib/waggle/SSL/node" "/usr/lib/waggle/SSL/waggleca")
for dir in ${directories[@]}; do
  [ -e $dir ]
  print_result "$dir Directory" $? 0 1
done

perms=$(stat -c '%U %G %a' /usr/lib/waggle/SSL/node/key.pem)
[ "$perms" == "rabbitmq rabbitmq 600" ]
print_result "Node Key Permissions" $? 0 1

perms=$(stat -c '%U %G %a' /usr/lib/waggle/SSL/node/cert.pem)
[ "$perms" == "rabbitmq rabbitmq 600" ]
print_result "Node Cert Permissions" $? 0 1

perms=$(stat -c '%U %G %a' /usr/lib/waggle/SSL/waggleca/cacert.pem)
[ "$perms" == "root root 644" ]
print_result "Waggle CA Cert Permissions" $? 0 1
