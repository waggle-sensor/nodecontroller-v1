#!/bin/bash

# The HOST & PORT are taken from the command line, if present.
# If no args are present, use the default tunnel's HOST & PORT.

key_file="/etc/waggle/key.pem"

if [ $# == 2 ]; then
    HOST=$1
    PORT=$2
elif [ $# == 0 ]; then
    HOST="root@beehive"
    PORT=`cat /etc/waggle/reverse_ssh_port`
else
    echo "USAGE: $0 [<HOST>  <PORT>]"
    exit 1
fi

if [ -z "$PORT" ]; then
    echo "Error: Invalid port number \"$PORT\""
    exit 1
fi

if ! [ "$PORT" -eq "$PORT" ] 2> /dev/null; then
    echo "Error: Invalid port number."
    exit 1
fi

# TODO! remove these options: -o "StrictHostKeyChecking no" -o "UserKnownHostsFile=/dev/null"
autossh -v -i $key_file -M 0 -gNC -o "ServerAliveInterval 5" -o "ServerAliveCountMax 3" -R $PORT:localhost:22 -o "StrictHostKeyChecking no" -o "UserKnownHostsFile=/dev/null" -o "ExitOnForwardFailure yes" $HOST -p 20022

# This final exit 1 is to make sure that autossh terminating should be considered
# an error, even if autossh has return code 0.
exit 1
