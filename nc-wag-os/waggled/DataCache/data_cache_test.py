#!/usr/bin/env python

import socket, os, os.path, logging, sys, time
from datetime import datetime

sys.path.append('/usr/lib/waggle/nodecontroller/')
sys.path.append('/usr/lib/waggle/nodecontroller/waggle_protocol/')
from utilities import packetmaker

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def send2dc(message):
    if os.path.exists('/tmp/Data_Cache_server'):
        client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            client_sock.connect('/tmp/Data_Cache_server')
            #data = comm.DC_push.get() #Gets message out of the queue and sends to data cache
            client_sock.sendall(message)
            client_sock.close() #closes socket after each message is sent
        except Exception as e:
            logger.error(e)
            #print e
            client_sock.close()
            time.sleep(1)
            return None
        logger.debug("Sending data from DC-push queue to Data_Cache socket")
        return "success"
        
"""
Script to test data cache by sending bulk messages to the data cache.
"""
if __name__ == "__main__":
    
    start = time.time()
    x = datetime.now()
    packettime = x-x
    sendingtime=x-x
    for i in range(1,10):
        tstart = datetime.now()
        
        packet = packetmaker.make_data_packet("hello world_"+str(i))
        packettime = packettime + (datetime.now()-tstart)
        
        print "huhu"
        logger.info("A")
        for pack in packet:
            logger.info("a pack")
            while 1:
                try:
                    sending_start = datetime.now()
                    send2dc(pack)
                    sendingtime = sendingtime + (datetime.now()-sending_start)
                    logger.info("sent!")
                except KeyboardInterrupt as e:
                    raise
                except Exception as e:
                    logger.error("Could not send message to %s:%d : %s" % (self.HOST, self.PORT, str(e)))
        
                    time.sleep(2)
                    continue
                break
                
    end = time.time()
    print "time in seconds: %s" % (end - start)
    
    print "packettime: ", packettime.total_seconds()
    print "sendingtime: ", sendingtime.total_seconds()

