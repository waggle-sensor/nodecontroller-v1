#!/usr/bin/env python
import time, serial, sys
sys.path.append('../../../protocol/')
from utilities import packetmaker
sys.path.append('../Communications/')
from internal_communicator import send
import time


def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()

def unix_time_millis(dt):
    return long(unix_time(dt) * 1000.0)
    


count = 0
while 1:
    tempC = int(open('/sys/class/thermal/thermal_zone0/temp').read()) / 1e3
    sendData=['sensor1', int(unix_time_millis(datetime.datetime.now())), ['Temperature']  , ['i'], [tempC], ['Celsius'], ['count='+str(count)]]
    print 'Sending data: ',sendData
    #packs and sends the data
    packet = packetmaker.make_data_packet(sendData)
    for pack in packet:
        send(pack)
    #send a packet every second
    time.sleep(1)
    count = count + 1


