#!/usr/bin/env python3


import sys
sys.path.append('../../../')
from waggle_protocol.utilities import packetmaker
sys.path.append('../DataCache/')
from send2dc import send


"""
    A python script that creates and sends a time request.
"""
packet = packetmaker.make_time_packet()
print('Time request packet made...') 
for pack in packet:
    send(pack)
