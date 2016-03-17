#!/bin/bash

autossh -i /usr/lib/waggle/SSL/node/key.pem -M 0 -gNC -o "ServerAliveInterval 5" -o "ServerAliveCountMax 3" -R `cat /etc/waggle/reverse_ssh_port`:localhost:22 root@beehive1.mcs.anl.gov  -p 20022