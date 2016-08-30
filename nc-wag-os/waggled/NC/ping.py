#!/usr/bin/env python3


import sys
sys.path.append('../../../')
from waggle_protocol.utilities import packetmaker
sys.path.append('../DataCache/')
from send2dc import send


""" 
    A python script that creates and sends a ping. 
""" 
packet = packetmaker.make_ping_packet()
print('Ping packet made...') 
for pack in packet:
    send(pack)
print('Ping packet sent.')
