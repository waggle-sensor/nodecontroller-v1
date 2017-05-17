#!/bin/bash

# The HOST & PORT are taken from the command line, if present.
# If no args are present, use the default tunnel's HOST & PORT.

set -x

if [ $# == 2 ]; then
    HOST=$1
    PORT=$2
elif [ $# == 0 ]; then
    HOST="root@beehive1.mcs.anl.gov"
    PORT=`cat /etc/waggle/reverse_ssh_port`
else
    echo "USAGE: " $0 " [<HOST>  <PORT>]"
    exit 1
fi

echo 'HOST = ' ${HOST}
echo 'PORT = ' ${PORT}

# TODO! remove these options: -o "StrictHostKeyChecking no" -o "UserKnownHostsFile=/dev/null"
autossh -i /usr/lib/waggle/SSL/node/key.pem -M 0 -gNC -o "ServerAliveInterval 5" -o "ServerAliveCountMax 3" -R ${PORT}:localhost:22 -o "StrictHostKeyChecking no" -o "UserKnownHostsFile=/dev/null" -o "ExitOnForwardFailure yes" ${HOST} -p 20022

# For us, autossh should never exit unless there's a problem...however, it's possible that it doesn't
# exit with an error code needed to have upstart respawn it. This is to correct that possible behavior.
exit 1
