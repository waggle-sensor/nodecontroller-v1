#!/bin/bash

. /usr/lib/waggle/core/scripts/detect_mac_address.sh
sed -i -e "s/%NODE_ID%/$NODE_ID/" /etc/rabbitmq/rabbitmq.config
