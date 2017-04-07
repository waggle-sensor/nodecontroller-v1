#!/usr/bin/env python3
'''
A python script that creates and sends a time request.
'''
import sys
from waggle.protocol.utils import packetmaker
sys.path.append('../DataCache/')
from send2dc import send


packet = packetmaker.make_time_packet()
print('Time request packet made...')
for pack in packet:
    send(pack)
