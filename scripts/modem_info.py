#!/usr/bin/env python3
from serial import Serial
from contextlib import closing
import sys
import re


try:
    device = sys.argv[1]
except:
    device = '/dev/attwwan4'

try:
    baudrate = int(sys.argv[2])
except:
    baudrate = 57600


def getid(command):
    command = (command + '\r').encode()
    pattern = re.compile('[0-9]+')

    while True:
        try:
            with closing(Serial(device, baudrate, timeout=1.5)) as s:
                s.flushInput()
                s.write(command)
                output = s.read(256).decode()
                match = pattern.search(output)
                if match:
                    return match.group()
        except:
            continue

imei = getid('AT+CGSN')
assert len(imei) == 15

ccid = getid('AT+CCID')
assert len(ccid) == 20

print('IMEI={}'.format(imei))
print('CCID={}'.format(ccid))
