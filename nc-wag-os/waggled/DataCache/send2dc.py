#!/usr/bin/env python
import socket, os, os.path, time, sys, logging


sys.path.append('../../../')
from waggle_protocol.protocol.PacketHandler import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


def send(msg):
    """
        This function is used only if the guest node and node controller are being run on the same machine. 
        It skips the push server that is used to connect with external guestnodes and pushes the message directly into the data cache.
        Skipping the server eliminates the need for a network setup in order to get messages from sensors to the data cache, 
        allowing a bare-essentials version of waggle to be used anywhere. 
        
        :param string msg: The packed waggle message that needs to be sent.
    """
    while True:
        try:
            #connect to DC and send msg
            if os.path.exists('/tmp/Data_Cache_server'):
                client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                try:
                    client_sock.connect('/tmp/Data_Cache_server')
                    logger.info( "Connected to data cache... ")
                    logger.info( "send(msg)... msg len: %d"% (len(msg)))
                    client_sock.sendall(msg)
                    client_sock.close() #closes socket after each message is sent 
                    break #break loop when message sent. Otherwise, keep trying to connect until successful.
                except Exception as e:
                    logger.error( e )
                    time.sleep(1)
                    client_sock.close()

            else: 
                time.sleep(1)
                logger.warning('Unable to connect to DC...')

        except KeyboardInterrupt, k:
            logger.Info("Shutting down.")
            
            break
    client_sock.close()