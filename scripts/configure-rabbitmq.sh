#!/bin/bash

. /usr/lib/waggle/core/scripts/detect_mac_address.sh
if grep -q "reply_to, <<\"$NODE_ID\">>" "/etc/rabbitmq/rabbitmq.config"; then
  echo "rabbitmq.config is correct"
else
  echo "rabbitmq.config is wrong"
  echo "copy /usr/lib/waggle/nodecontroller/etc/rabbitmq/rabbitmq.config to /etc/rabbitmq and put node id in the file"
  cp /usr/lib/waggle/nodecontroller/etc/rabbitmq/rabbitmq.config /etc/rabbitmq
  sed -i -e "s/%NODE_ID%/$NODE_ID/" /etc/rabbitmq/rabbitmq.config
fi
