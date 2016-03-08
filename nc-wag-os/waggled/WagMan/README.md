


Start WagMan script on boot (ODroid):
-----
1) put "WagMan_start.sh" in /etc/init.d
2) put "WagMan.py" in dir specified at the top of "WagMan_start.sh"
3) put "99-usb-serial.rules" in /etc/udev/rules.d
3) cd /etc/init.d
4) chmod +x WagMan_start.sh
5) update-rc.d WagMan_start.sh defaults
6) cd /home/odroid/Downloads
7) wget https://bootstrap.pypa.io/get-pip.py
8) python get-pip.py
9) pip install pyserial


Reboot to become the WagMan (or part of it, anyway)!
