#!/bin/bash

. /usr/lib/waggle/core/scripts/detect_mac_address.sh

recover_rabbitmq_config() {
  echo "* copy /usr/lib/waggle/nodecontroller/etc/rabbitmq/rabbitmq.config to /etc/rabbitmq and recover the file (put node id in the file)" 
  NODE_ID=$1
  if [ -w / ]; then
    cp /usr/lib/waggle/nodecontroller/etc/rabbitmq/rabbitmq.config /etc/rabbitmq
    sed -i -e "s/%NODE_ID%/$NODE_ID/" /etc/rabbitmq/rabbitmq.config
  else
    waggle-fs-unlock
    cp /usr/lib/waggle/nodecontroller/etc/rabbitmq/rabbitmq.config /etc/rabbitmq
    sed -i -e "s/%NODE_ID%/$NODE_ID/" /etc/rabbitmq/rabbitmq.config
    waggle-fs-lock
  fi
}

recover_enabled_plugins() {
  echo "* enabled_plugins is wrong"
  echo "* copy /usr/lib/waggle/nodecontroller/etc/rabbitmq/enabled_plugins to /etc/rabbitmq"
  if [ -w / ]; then
    cp /usr/lib/waggle/nodecontroller/etc/rabbitmq/enabled_plugins /etc/rabbitmq
  else
    waggle-fs-unlock
    cp /usr/lib/waggle/nodecontroller/etc/rabbitmq/enabled_plugins /etc/rabbitmq
    waggle-fs-lock
  fi
}

check_rabbitmq_config() {
  NODE_ID=$1
  config=$2
  if [ $config == "ok" ]; then
    echo "* rabbitmq.config is correct synthetically"
  else
    echo "* rabbitmq.config is synthetically wrong"
    recover_rabbitmq_config $NODE_ID
  fi
}

check_enabled_plugins() {
  enabled=$1
  if [ $enabled == "ok" ]; then
    echo "* enabled_plugins is correct synthetically, but what if elements"
    check_enabled_plugins_elements
  else
    recover_enabled_plugins
  fi
}

check_enabled_plugins_elements() {
  if grep "rabbitmq_management,rabbitmq_shovel,rabbitmq_shovel_management" /etc/rabbitmq/enabled_plugins; then
    echo "* enabled_plugins is correct"
  else
    recover_enabled_plugins
  fi
}

check_syntex() {
  NODE_ID=$1
  echo "* check syntex of config files"
  cd /etc/rabbitmq
  ./check_config_files
  check_result=$(./check_config_files)

  rabbitmq_config=$(echo "$check_result" | grep rabbitmq.config | cut -d ' ' -f 2)
  enabled_plugins=$(echo "$check_result" | grep enabled_plugins | cut -d ' ' -f 2)

  check_rabbitmq_config $NODE_ID $rabbitmq_config
  check_enabled_plugins $enabled_plugins
}

if grep -q "reply_to, <<\"$NODE_ID\">>" "/etc/rabbitmq/rabbitmq.config"; then
  echo "* rabbitmq.config is correct, but let see syntex"
  check_syntex $NODE_ID
else
  echo "* rabbitmq.config is wrong, so recovery it first, and then let's see syntex"
  recover_rabbitmq_config $NODE_ID
  check_syntex $NODE_ID
fi
