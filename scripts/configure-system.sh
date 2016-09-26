#!/bin/bash

# this will make sure that an empty eMMC card will get the waggle image
touch /root/do_recovery

echo -e "10.31.81.51\textensionnode1 extensionnode" >> /etc/hosts
for i in 2 3 4 5 ; do
	echo -e "10.31.81.5${i}\textensionnode${i}" >> /etc/hosts
done

echo -e "127.0.0.1\tnodecontroller" >> /etc/hosts

# Restrict SSH connections to local port bindings and ethernet card subnet
sed -i 's/^#ListenAddress ::$/ListenAddress 127.0.0.1/' /etc/ssh/sshd_config
sed -i 's/^#ListenAddress 0.0.0.0$/ListenAddress 10.31.81.10/' /etc/ssh/sshd_c
