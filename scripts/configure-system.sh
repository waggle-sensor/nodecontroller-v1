#!/bin/bash

while [[ $# -gt 0 ]]; do
  key="$1"
  echo "Key: $key"
  case $key in
    -s)
      SERVER_HOST="$2"
      shift
      ;;
    --server-host=*)
      SERVER_HOST="${key#*=}"
      ;;
      *)
      ;;
  esac
  shift
done

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# this will make sure that an empty eMMC card will get the waggle image
touch /root/do_recovery

# this will trigger a self test on the first full boot
touch /home/waggle/start_test

# (re)build the /etc/hosts file
if [ ${SERVER_HOST}x != "x" ] ; then
  cp $script_dir/../etc/hosts /etc/hosts
  sed -i "s/SERVER_HOST/${SERVER_HOST}/" /etc/hosts
fi

# Restrict SSH connections to local port bindings and ethernet card subnet
sed -i 's/^#ListenAddress ::$/ListenAddress 127.0.0.1/' /etc/ssh/sshd_config
sed -i 's/^#ListenAddress 0.0.0.0$/ListenAddress 10.31.81.10/' /etc/ssh/sshd_config

# disable all password authentication
sed -i 's/^#PasswordAuthentication yes$/PasswordAuthentication no/' /etc/ssh/sshd_config

cp ./etc/network/interfaces /etc/network/interfaces

rm -f /etc/sudoers.d/waggle*
cp ./etc/sudoers.d/* /etc/sudoers.d/

# add AoT test cert for waggle user
echo "command=\"/bin/date\" ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCedz4oU6YdvFjbWiJTpJiREplTizAk2s2dH0/aBMLmslSXzMXCgAh0EZOjsA3CW+P2SIn3NY8Hx3DmMR9+a1ISd3OcBcH/5F48pejK1MBtdLOnai64JmI80exT3CR34m3wXpmFbbzQ5jrtGFb63q/n89iVDb+BwY4ctrBn+J7BPEJbhh/aepoUNSG5yICWtjC0q8mDhHzr+40rYsxPXjp9HTaEzgLu+fNhJ0rK+4891Lr08MTud2n8TEntjBRlWQUciGrPn1w3jzIz+q2JdJ35a/MgLg6aRSQOMg6AdanZH2XBTqHbaeYOWrMhmDTjC/Pw9Jczl7S+wr0648bzXz2T AoT_key_test" > /home/waggle/.ssh/authorized_keys
echo >> /home/waggle/.ssh/authorized_keys

# add AoT node controller cert for root
mkdir -p /root/.ssh/
chmod 744 /root/.ssh
echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCsYPMSrC6k33vqzulXSx8141ThfNKXiyFxwNxnudLCa0NuE1SZTMad2ottHIgA9ZawcSWOVkAlwkvufh4gjA8LVZYAVGYHHfU/+MyxhK0InI8+FHOPKAnpno1wsTRxU92xYAYIwAz0tFmhhIgnraBfkJAVKrdezE/9P6EmtKCiJs9At8FjpQPUamuXOy9/yyFOxb8DuDfYepr1M0u1vn8nTGjXUrj7BZ45VJq33nNIVu8ScEdCN1b6PlCzLVylRWnt8+A99VHwtVwt2vHmCZhMJa3XE7GqoFocpp8TxbxsnzSuEGMs3QzwR9vHZT9ICq6O8C1YOG6JSxuXupUUrHgd AoT_key" > /root/.ssh/authorized_keys
echo >> /root/.ssh/authorized_keys

# add AoT Edge Processor cert for root
echo "from=\"10.31.81.5?\" ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC4ohQv1Qksg2sLIqpvjJuZEsIkeLfbPusEaJQerRCqI71g8hwBkED3BBv5FehLcezTg+cFJFhf2vBGV5SbV0NzbouIM+n0lAr6+Ei/XYjO0B1juDm6cUmloD4HSzQWv+cSyNmb7aXjup7V0GP1DZH3zlmvwguhMUTDrWxQxDpoV28m72aZ4qPH7VmQIeN/JG3BF9b9F8P4myOPGuk5XTjY1rVG+1Tm2mxw0L3WuL6w3DsiUrvlXsGE72KcyFBDiFqOHIdnIYWXDLZz61KXctVLPVLMevwU0YyWg70F9pb0d2LZt7Ztp9GxXBRj5WnU9IClaRh58RsYGhPjdfGuoC3P AoT_edge_processor_key" >> /root/.ssh/authorized_keys
echo >> /root/.ssh/authorized_keys

# add an ssh config host for the Edge Processor
cat <<EOT > /root/.ssh/config
Host edgeprocessor
  StrictHostKeyChecking no
  PasswordAuthentication no
  ConnectTimeout 5
  ForwardAgent yes
EOT
 
# Setup RabbitMQ config files.
cp -r /usr/lib/waggle/nodecontroller/etc/rabbitmq /etc

# Just in case for now...ideally this would be in /etc/envinronment already.
WAGGLE_ID=$(ip link | awk '/ether 00:1e:06/ { print $2 }' | sed 's/://g')
sed -i -e "s/%WAGGLE_ID%/$WAGGLE_ID/" /etc/rabbitmq/rabbitmq.config
