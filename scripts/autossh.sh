#!/bin/bash

set -x

# TODO! remove these options: -o "StrictHostKeyChecking no" -o "UserKnownHostsFile=/dev/null"

autossh -i /usr/lib/waggle/SSL/node/key.pem -M 0 -gNC -o "ServerAliveInterval 5" -o "ServerAliveCountMax 3" -R `cat /etc/waggle/reverse_ssh_port`:localhost:22 -o "StrictHostKeyChecking no" -o "UserKnownHostsFile=/dev/null" -o "ExitOnForwardFailure yes" root@beehive1.mcs.anl.gov  -p 20022

# For us, autossh should never exit unless there's a problem...however, it's possible that it doesn't
# exit with an error code needed to have upstart respawn it. This is to correct that possible behavior.
exit 1
