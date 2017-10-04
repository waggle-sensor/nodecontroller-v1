#!/bin/bash

. /usr/lib/waggle/core/scripts/detect_mac_address.sh

recover_rabbitmq_config() {
  NODE_ID=$1
  echo "rabbitmq.config is wrong"
  echo "copy /usr/lib/waggle/nodecontroller/etc/rabbitmq/rabbitmq.config to /etc/rabbitmq and put node id in the file"
  cp /usr/lib/waggle/nodecontroller/etc/rabbitmq/rabbitmq.config /etc/rabbitmq
  sed -i -e "s/%NODE_ID%/$NODE_ID/" /etc/rabbitmq/rabbitmq.config
}

cd /etc/rabbitmq
check_result=$(./check_config_files)
if [ $(echo "$check_result" | grep rabbitmq.config | cut -d ' ' -f 2) == "ok" ]; then
  echo "rabbitmq.config is correct synthetically"
else
  recover_rabbitmq_config $NODE_ID
  exit 0
fi

if grep -q "reply_to, <<\"$NODE_ID\">>" "/etc/rabbitmq/rabbitmq.config"; then
  echo "rabbitmq.config is correct"
else
  recover_rabbitmq_config $NODE_ID
fi
