#!/bin/bash
#This goes in /usr/bin/wvwaggle.sh, and make the file executable with chmod +x /usr/bin/wvwaggle.sh
#Let us give the modem time to settle.
rm /var/lock/*attwwan
rm /dev/attwwan
sleep 15
ln -s $(ls /dev/attwwan[0-9] | sort | head -1) /dev/attwwan
sleep 15
