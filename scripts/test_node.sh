#!/bin/bash

print_result()
  test_description=$1
  result=$2
  send_user "\n"
  if { $result == 0 } {
    echo "\[0;30;32m\[PASS\]\[0;30;37m $test_description\n"
  } else {
    echo "\[0;30;31m\[FAIL\]\[0;30;37m $test_description\n"
  }
}

shadow='root:$6$D3j0Te22$md6NULvJPliwvAhK2BlL96XCsJ0KdTnPqNdufDWgyU5k6Nc3M88qO64WCKKTLZry1GgKhGE95L5ZA1i2VFQGn.:17079:0:99999:7:::'
fgrep $shadow /etc/shadow > /dev/null
print_result "AoT Root Password Set" $?

keys=("ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCsYPMSrC6k33vqzulXSx8141ThfNKXiyFxwNxnudLCa0NuE1SZTMad2ottHIgA9ZawcSWOVkAlwkvufh4gjA8LVZYAVGYHHfU/+MyxhK0InI8+FHOPKAnpno1wsTRxU92xYAYIwAz0tFmhhIgnraBfkJAVKrdezE/9P6EmtKCiJs9At8FjpQPUamuXOy9/yyFOxb8DuDfYepr1M0u1vn8nTGjXUrj7BZ45VJq33nNIVu8ScEdCN1b6PlCzLVylRWnt8+A99VHwtVwt2vHmCZhMJa3XE7GqoFocpp8TxbxsnzSuEGMs3QzwR9vHZT9ICq6O8C1YOG6JSxuXupUUrHgd AoT_key" \
      "command=\"/bin/date\" ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCedz4oU6YdvFjbWiJTpJiREplTizAk2s2dH0/aBMLmslSXzMXCgAh0EZOjsA3CW+P2SIn3NY8Hx3DmMR9+a1ISd3OcBcH/5F48pejK1MBtdLOnai64JmI80exT3CR34m3wXpmFbbzQ5jrtGFb63q/n89iVDb+BwY4ctrBn+J7BPEJbhh/aepoUNSG5yICWtjC0q8mDhHzr+40rYsxPXjp9HTaEzgLu+fNhJ0rK+4891Lr08MTud2n8TEntjBRlWQUciGrPn1w3jzIz+q2JdJ35a/MgLg6aRSQOMg6AdanZH2XBTqHbaeYOWrMhmDTjC/Pw9Jczl7S+wr0648bzXz2T AoT_key_test" \
      "from=\"10.31.81.5?\" ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC4ohQv1Qksg2sLIqpvjJuZEsIkeLfbPusEaJQerRCqI71g8hwBkED3BBv5FehLcezTg+cFJFhf2vBGV5SbV0NzbouIM+n0lAr6+Ei/XYjO0B1juDm6cUmloD4HSzQWv+cSyNmb7aXjup7V0GP1DZH3zlmvwguhMUTDrWxQxDpoV28m72aZ4qPH7VmQIeN/JG3BF9b9F8P4myOPGuk5XTjY1rVG+1Tm2mxw0L3WuL6w3DsiUrvlXsGE72KcyFBDiFqOHIdnIYWXDLZz61KXctVLPVLMevwU0YyWg70F9pb0d2LZt7Ztp9GxXBRj5WnU9IClaRh58RsYGhPjdfGuoC3P AoT_guest_node_key")
key_names=("AoT Key" "AoT Test Key" "AoT Guest Key")
for i in $(seq 1 ${#keys[@]}); do
  key=${keys[i]}
  key_name=${key_names[i]}
  fgrep $key /home/waggle/.ssh/authorized_keys
  print_result "$key_name Auth" $?
done

grep '^sudo:x:27:$' /etc/group
print_result "sudo Disabled" $?

directories=("/etc/waggle" "/usr/lib/waggle" "/usr/lib/waggle/core" "/usr/lib/waggle/plugin_manager" "/usr/lib/waggle/nodecontroller" \
             "/usr/lib/waggle/SSL" "/usr/lib/waggle/SSL/guest" "/usr/lib/waggle/SSL/node" "/usr/lib/waggle/SSL/waggleca")
for dir in $directories; do
  print_result "$dir Directory" [ -e $dir ]
done

perms=$(stat -c '%U %G %a' /usr/lib/waggle/SSL/guest/id_rsa_waggle_aot_guest_node)
print_result "Guest Key Permissions" [ $perms == "root root 600" ]

perms=$(stat -c '%U %G %a' /usr/lib/waggle/SSL/SSL/node/key.pem)
print_result "Node Key Permissions" [ $perms == "rabbitmq rabbitmq 600" ]

perms=$(stat -c '%U %G %a' /usr/lib/waggle/SSL/SSL/node/cert.pem)
print_result "Node Key Permissions" [ $perms == "rabbitmq rabbitmq 600" ]

perms=$(stat -c '%U %G %a' /usr/lib/waggle/SSL/SSL/waggleca/cacert.pem)
print_result "Waggle CA Cert Permissions" [ $perms == "root root 644" ]

# Ethernet IP Address (NC)
ifconfig | fgrep "          inet addr:10.31.81.10  Bcast:10.31.81.255  Mask:255.255.255.0"
print_result "Ethernet IP Address" $?

devices=("waggle_sysmon" "waggle_coresense" "alphasense" "gps_module" "attwwan")
device_names=(list "WagMan" "Coresense" "Alphasense" "GPS" "Modem")
for i in $(seq 1 ${#devices[@]}); do
  device=${devices[i]}
  device_name=${device_names[i]}
  print_result "$device_name Device" [ -e $device ]
done

# Modem USB
send -- "lsusb | grep --color=never 1bc7:0021\r"
expect {
  -exact "ID 1bc7:0021 Telit Wireless Solutions HE910" {

# Modem IP Address
send -- "ifconfig | grep ppp0 --color=never -A 1\r"
expect {
  -exact "          inet addr:" {

# sshd Listen Addresses (NC)
send -- "cat /etc/ssh/sshd_config               | grep --color=never -e 'ListenAddress' -e 'PermitRootLogin'\r"
expect {
  -exact "ListenAddress 127.0.0.1\r
ListenAddress 10.31.81.10\r" {

# sshd No Root Login (NC)
  -exact "PermitRootLogin no\r" {

# Node ID Set
send -- "cat /etc/waggle/node_id | wc -l\r"
expect {
  -re "\[1\]" {

# Hostname Set (NC)
  send "cd /usr/lib/waggle/core/scripts\r"
  send "detect_mac_address.sh\r"
  send "cd\r"
} else {
  send_user "\[0;30;31m\[FAIL\]\[0;30;37m Node ID Set (GN)\n"
}

set success 0
send -- "cat /etc/hostname                      | grep \${MAC_STRING}SD | wc -l\r"
expect {
  -re "\[1\]" {

# SD Resize (NC)
send -- "parted -s /dev/mmcblk1p2 print                     | grep --color=never -e ext\r"
expect {
  -re " 1      0\.00B  15\.\[0-9\]GB  15\.\[0-9\]GB  ext" {

# Recovery to eMMC (NC)
send -- "parted -s /dev/mmcblk0p2 print | grep --color=never -e ext\r"
expect {
  -re " 1      0\.00B  15\.\[0-9\]GB  15\.\[0-9\]GB  ext" {

# waggle-communications Service (NC), etc...
set units [list "waggle-communications" "waggle-epoch" "waggle-heartbeat" \
                "waggle-plugin-manager" "waggle-wagman-publisher" \
                "waggle-wagman-server" "waggle-wellness"]
foreach unit $units {
  set success 0
  send -- "systemctl status ${unit}                  | grep --color=never Active: | sed 's/)..*/)/'\r"
  expect {
    -exact "   Active: active (running)" {

# waggle-wwan Service (NC), etc...
set units [list "waggle-wwan" "waggle-reverse-tunnel"]
foreach unit $units {
  set success 0
  send -- "systemctl status ${unit}                      | grep --color=never Active: | sed 's/)..*/)/'\r"
  expect {
    -exact "   Active: active (running)" {
      set success 1
      exp_continue
    }
    -exact "   Active: activating (auto-restart)" {

# waggle-log-wagman.timer Service (NC)
send -- "systemctl status waggle-log-wagman.timer                  | grep --color=never Active: | sed 's/)..*/)/'\r"
expect {
  -exact "   Active: active (running)" {
    set success 1
    exp_continue
  }
  -exact "   Active: active (waiting)" {

# WagMan Device, etc...
set devices [list "waggle_sysmon" "waggle_coresense" "alphasense" "gps_module" "attwwan"]
set device_names [list "WagMan" "Coresense" "Alphasense" "GPS" "Modem"]

for {set index 0} {$index < [llength $devices]} {incr index} {
  set device [lindex $devices $index]
  set device_name [lindex $device_names $index]
  set success 0
  send -- "ls /dev/${device} --color=never\r"
  expect {
    "${device}" {

# ssh to GN
    send -- "ssh waggle@10.31.81.51                           -o \"StrictHostKeyChecking no\"\r"

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
send -- "lsusb | grep --color=never 0d8c:013c\r"
expect {
  -exact "ID 0d8c:013c C-Media Electronics, Inc. CM108 Audio Controller" {

# Top Camera USB
send -- "lsusb | grep --color=never 05a3:9830\r"
expect {
  -exact "ID 05a3:9830 ARC International" {

# Bottom Camera USB
send -- "lsusb | grep --color=never 05a3:9520\r"
expect {
  -exact "ID 05a3:9520 ARC International" {
