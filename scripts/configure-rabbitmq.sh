#!/bin/sh

cp -r /usr/lib/waggle/nodecontroller/etc/rabbitmq /etc
WAGGLE_ID=$(ip link | awk '/ether 00:1e:06/ { print $2 }' | sed 's/://g')
sed -i -e "s/%WAGGLE_ID%/$WAGGLE_ID/" /etc/rabbitmq/rabbitmq.config
