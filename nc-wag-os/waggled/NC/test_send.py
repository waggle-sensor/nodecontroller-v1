import time, serial, sys
sys.path.append('../../../protocol/')
from utilities import packetmaker
sys.path.append('../Communications/')
from internal_communicator import send
import time
count = 0
while 1:
    sendData=['This','is','a','fake','sensor - ',str(count)]
    print 'Sending data: ',sendData
    #packs and sends the data
    packet = packetmaker.make_data_packet(sendData)
    for pack in packet:
        send(pack)
    #send a packet every ten seconds
    time.sleep(10)


