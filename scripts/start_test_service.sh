#!/bin/bash

if [[ ! -e /home/waggle/continue_test && ! -e /home/waggle/finish_test ]]; then
  touch /home/waggle/start_test
fi
sudo /bin/systemctl start waggle-test.service
