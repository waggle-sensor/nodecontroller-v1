#!/bin/bash
# ANL:waggle-license
#  This file is part of the Waggle Platform.  Please see the file
#  LICENSE.waggle.txt for the legal details of the copyright and software
#  license.  For more details on the Waggle project, visit:
#           http://www.wa8.gl
# ANL:waggle-license
#This goes in /usr/bin/wvwaggle.sh, and make the file executable with chmod +x /usr/bin/wvwaggle.sh
#Let us give the modem time to settle.
rm -f /var/lock/*attwwan
rm -f /dev/attwwan
sleep 15
ln -s $(ls /dev/attwwan[0-9] | sort | head -1) /dev/attwwan
