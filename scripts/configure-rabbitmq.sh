#!/bin/bash

. /usr/lib/waggle/core/scripts/detect_mac_address.sh
sed -i -e "s/%NODE_ID%/$NODE_ID/" /etc/rabbitmq/rabbitmq.config

# Shovels for guest node
GUESTNODE_IP=$(cat /etc/hosts | grep -m 1 extensionnode | awk '{print $1}')
sed -i -e "s/%GUESTNODE_IP%/$GUESTNODE_IP/" /etc/rabbitmq/rabbitmq.config

