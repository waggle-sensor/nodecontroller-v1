#!/bin/bash
set -x
set -e

rm -f /etc/udev/rules.d/75-wwan-net.rules
cp 75-wwan-net.rules /etc/udev/rules.d/

rm -f /usr/bin/wvwaggle.sh
cp ./wvwaggle.sh /usr/bin/
chmod +x /usr/bin/wvwaggle.sh

rm -f /etc/udev/rules.d/40-usb_modeswitch.rules
cp 40-usb_modeswitch.rules /etc/udev/rules.d/

set +x
echo "run: udevadm control --reload-rules"
