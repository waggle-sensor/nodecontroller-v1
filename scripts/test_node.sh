#!/bin/bash

set +e

print_result() {
  local test_description=$1
  local result=$2
  local optional=$3
  if [ $result == 0 ]; then
    echo "[0;30;32m[PASS][0;30;37m $test_description"
  elif [[ ! -z ${optional+x} && $optional == 1 ]]; then
    echo "[0;30;33m[FAIL][0;30;37m $test_description"
  else
    echo "[0;30;31m[FAIL][0;30;37m $test_description"
  fi
}

shadow='root:$6$D3j0Te22$md6NULvJPliwvAhK2BlL96XCsJ0KdTnPqNdufDWgyU5k6Nc3M88qO64WCKKTLZry1GgKhGE95L5ZA1i2VFQGn.:17079:0:99999:7:::'
fgrep $shadow /etc/shadow
print_result "AoT Root Password Set" $?

keys=('ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCsYPMSrC6k33vqzulXSx8141ThfNKXiyFxwNxnudLCa0NuE1SZTMad2ottHIgA9ZawcSWOVkAlwkvufh4gjA8LVZYAVGYHHfU/+MyxhK0InI8+FHOPKAnpno1wsTRxU92xYAYIwAz0tFmhhIgnraBfkJAVKrdezE/9P6EmtKCiJs9At8FjpQPUamuXOy9/yyFOxb8DuDfYepr1M0u1vn8nTGjXUrj7BZ45VJq33nNIVu8ScEdCN1b6PlCzLVylRWnt8+A99VHwtVwt2vHmCZhMJa3XE7GqoFocpp8TxbxsnzSuEGMs3QzwR9vHZT9ICq6O8C1YOG6JSxuXupUUrHgd AoT_key' \
      'command="/bin/date" ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCedz4oU6YdvFjbWiJTpJiREplTizAk2s2dH0/aBMLmslSXzMXCgAh0EZOjsA3CW+P2SIn3NY8Hx3DmMR9+a1ISd3OcBcH/5F48pejK1MBtdLOnai64JmI80exT3CR34m3wXpmFbbzQ5jrtGFb63q/n89iVDb+BwY4ctrBn+J7BPEJbhh/aepoUNSG5yICWtjC0q8mDhHzr+40rYsxPXjp9HTaEzgLu+fNhJ0rK+4891Lr08MTud2n8TEntjBRlWQUciGrPn1w3jzIz+q2JdJ35a/MgLg6aRSQOMg6AdanZH2XBTqHbaeYOWrMhmDTjC/Pw9Jczl7S+wr0648bzXz2T AoT_key_test' \
      'from="10.31.81.5?" ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC4ohQv1Qksg2sLIqpvjJuZEsIkeLfbPusEaJQerRCqI71g8hwBkED3BBv5FehLcezTg+cFJFhf2vBGV5SbV0NzbouIM+n0lAr6+Ei/XYjO0B1juDm6cUmloD4HSzQWv+cSyNmb7aXjup7V0GP1DZH3zlmvwguhMUTDrWxQxDpoV28m72aZ4qPH7VmQIeN/JG3BF9b9F8P4myOPGuk5XTjY1rVG+1Tm2mxw0L3WuL6w3DsiUrvlXsGE72KcyFBDiFqOHIdnIYWXDLZz61KXctVLPVLMevwU0YyWg70F9pb0d2LZt7Ztp9GxXBRj5WnU9IClaRh58RsYGhPjdfGuoC3P AoT_guest_node_key')
echo ${keys[@]}
key_names=('AoT Key' 'AoT Test Key' 'AoT Guest Key')
for i in $(seq 0 `expr ${#keys[@]} - 1`); do
  key=${keys[i]}
  key_name=${key_names[i]}
  fgrep "$key" /home/waggle/.ssh/authorized_keys
  print_result "$key_name Auth" $?
done

grep '^sudo:x:27:$' /etc/group
print_result "sudo Disabled" $?

directories=("/etc/waggle" "/usr/lib/waggle" "/usr/lib/waggle/core" "/usr/lib/waggle/plugin_manager" "/usr/lib/waggle/nodecontroller" \
             "/usr/lib/waggle/SSL" "/usr/lib/waggle/SSL/guest" "/usr/lib/waggle/SSL/node" "/usr/lib/waggle/SSL/waggleca")
for dir in $directories; do
  [ -e $dir ]
  print_result "$dir Directory" $?
done

perms=$(stat -c '%U %G %a' /usr/lib/waggle/SSL/guest/id_rsa_waggle_aot_guest_node)
[ "$perms" == "root root 600" ]
print_result "Guest Key Permissions" $?

perms=$(stat -c '%U %G %a' /usr/lib/waggle/SSL/node/key.pem)
[ "$perms" == "rabbitmq rabbitmq 600" ]
print_result "Node Key Permissions" $?

perms=$(stat -c '%U %G %a' /usr/lib/waggle/SSL/node/cert.pem)
[ "$perms" == "rabbitmq rabbitmq 600" ]
print_result "Node Key Permissions" $?

perms=$(stat -c '%U %G %a' /usr/lib/waggle/SSL/waggleca/cacert.pem)
[ "$perms" == "root root 644" ]
print_result "Waggle CA Cert Permissions" $?

# Ethernet IP Address (NC)
ifconfig | fgrep "          inet addr:10.31.81.10  Bcast:10.31.81.255  Mask:255.255.255.0"
print_result "Built-in Ethernet IP Address" $?

devices=("waggle_sysmon" "waggle_coresense")
device_names=("WagMan" "Coresense")
for i in $(seq 0 `expr ${#devices[@]} - 1`); do
  device=${devices[i]}
  device_name=${device_names[i]}
  [ -e /dev/$device ]
  print_result "$device_name Device" $?
done

devices=("alphasense" "gps_module" "attwwan")
device_names=("Alphasense" "GPS" "Modem")
for i in $(seq 0 `expr ${#devices[@]} - 1`); do
  device=${devices[i]}
  device_name=${device_names[i]}
  [ -e /dev/$device ]
  print_result "Optional $device_name Device" $? 1
done

lsusb | grep 1bc7:0021
if [ $? -eq 0 ]; then
  # Found USB Modem Device
  print_result "Modem USB" 0

  ifconfig | grep ppp0 -A 1 | fgrep "inet addr:"
  print_result "Modem IP Address" $?
else
  # No USB Modem Device Present
  ifconfig | grep -A 1 enx | grep 'inet addr:'
  print_result "USB Ethernet IP Address" $?
fi

line_count=$(cat /etc/ssh/sshd_config | fgrep -e 'ListenAddress 127.0.0.1' -e 'ListenAddress 10.31.81.10' | wc -l)
[ $line_count -eq 2 ]
print_result "sshd Listen Addresses" $?

cat /etc/ssh/sshd_config | fgrep 'PermitRootLogin no'
print_result "sshd No Root Login" $?

cat /etc/waggle/node_id | egrep '[0-9a-f]{16}'
print_result "Node ID Set" $?

. /usr/lib/waggle/core/scripts/detect_mac_address.sh
cat /etc/hostname | fgrep "${MAC_STRING}SD"
print_result "Hostname Set" $?

parted -s /dev/mmcblk1p2 print | grep --color=never -e ext | awk '{print $3}' | egrep '15\.[0-9]GB'
print_result "SD Resize" $?

parted -s /dev/mmcblk0p2 print | grep --color=never -e ext | awk '{print $3}' | egrep '15\.[0-9]GB'
print_result "Recovery to eMMC" $?

units=("waggle-communications" "waggle-epoch" "waggle-heartbeat" \
       "waggle-plugin-manager" "waggle-wagman-publisher" \
       "waggle-wagman-server" "waggle-wellness")
for unit in $units; do
  systemctl status $unit | fgrep 'Active: active (running)'
  print_result "$unit Service" $?
done

units=("waggle-wwan" "waggle-reverse-tunnel")
for unit in $units; do
  systemctl status $unit | fgrep -e 'Active: active (running)' -e 'Active: activating (auto-restart)'
  print_result "$unit Service" $?
done

unit='waggle-log-wagman.timer'
systemctl status $unit | fgrep -e 'Active: active (running)' -e 'Active: active (waiting)'
print_result "$unit Service" $?

# ssh to GN
ssh -i /usr/lib/waggle/SSL/guest/id_rsa_waggle_aot_guest_node waggle@10.31.81.51 \
    -o "StrictHostKeyChecking no" -o "PasswordAuthentication no" -o "ConnectTimeout 2" /bin/date
print_result "ssh to GN" $?

##### Repeat above as necessary for GN tests #####
# Node ID Set (GN)
# Hostname Set (GN)
# sudo Disabled (GN)
# su (GN)
# SD Resize (GN)
# Recovery to eMMC (GN)
# Directory /etc/waggle Exists (GN)
# Directory /usr/lib/waggle Exists (GN)
# Directory /usr/lib/waggle/core Exists (GN)
# Directory /usr/lib/waggle/plugin_manager Exists (GN)
# Directory /usr/lib/waggle/guestnode Exists (GN)
# Directory /usr/lib/waggle/SSL Exists (GN)
# Directory /usr/lib/waggle/SSL/guest Exists (GN)
# waggle-epoch Service (GN)
# waggle-heartbeat Service (GN)
# waggle-plugin-manager Service (GN)
# sshd Listen Addresses (GN)
# sshd No Root Login (GN)
##################################################

# Microphone USB
#send -- "lsusb | grep --color=never 0d8c:013c\r"
#expect {
#  -exact "ID 0d8c:013c C-Media Electronics, Inc. CM108 Audio Controller" {
#
## Top Camera USB
#send -- "lsusb | grep --color=never 05a3:9830\r"
#expect {
#  -exact "ID 05a3:9830 ARC International" {
#
## Bottom Camera USB
#send -- "lsusb | grep --color=never 05a3:9520\r"
#expect {
#  -exact "ID 05a3:9520 ARC International" {
