#!/bin/bash

recover_rabbitmq_config() {
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
  if [ -w / ]; then
    cp /usr/lib/waggle/nodecontroller/etc/rabbitmq/enabled_plugins /etc/rabbitmq
  else
    waggle-fs-unlock
    cp /usr/lib/waggle/nodecontroller/etc/rabbitmq/enabled_plugins /etc/rabbitmq
    waggle-fs-lock
  fi
}

echo "Checking Rabbitmq Config files..."
NODE_ID=$(/usr/lib/waggle/core/scripts/detect_mac_address.sh | grep MAC_STRING | cut -d '=' -f 2)
cd /etc/rabbitmq
check_result=$(./check_config_files)

echo -n "Checking rabbitmq.config..."
syntax_check_result=$(echo "$check_result" | grep rabbitmq.config | cut -d ' ' -f 2)
node_id_check_result=$(grep "reply_to, <<\"$NODE_ID\">>" "/etc/rabbitmq/rabbitmq.config" | wc -l)
if [ "$syntax_check_result" == "ok" ] && [ "$node_id_check_result" == "1" ]; then
  echo "correct"
else
  echo "wrong - recoverying rabbitmq.config..."
  recover_rabbitmq_config $NODE_ID
fi

echo -n "Checking enabled_plugins..."
syntax_check_result=$(echo "$check_result" | grep enabled_plugins | cut -d ' ' -f 2)
enabled_plugins_check_result=$(grep "rabbitmq_management,rabbitmq_shovel,rabbitmq_shovel_management" "/etc/rabbitmq/enabled_plugins" | wc -l)
if [ "$syntax_check_result" == "ok" ] && [ "$enabled_plugins_check_result" == "1" ]; then
  echo "correct"
else
  echo "wrong - recovering enabled_plugins..."
  recover_enabled_plugins
fi

echo -n "Checking .erlang.cookie..."
cookie_length_check_result=$(cat /var/lib/rabbitmq/.erlang.cookie | wc -c)
if [ "$cookie_length_check_result" != "0" ];  then
  echo "correct"
else
  echo "wrong - removing /var/lib/rabbitmq/.erlang.cookie file..."
  rm -f /var/lib/rabbitmq/.erlang.cookie
fi

echo "Checking done"