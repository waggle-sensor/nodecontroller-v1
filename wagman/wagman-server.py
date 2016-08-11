#!/usr/bin/env python3
import zmq
import sys
from serial import Serial
import time
import os.path
import logging

LOG_FORMAT='%(asctime)s - %(name)s - %(levelname)s - line=%(lineno)d - %(message)s'
formatter = logging.Formatter(LOG_FORMAT)

handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)

logger.addHandler(handler)
logger.setLevel(logging.DEBUG)



wagman_device = '/dev/waggle_sysmon'

"""
The WagMan server accepts commands that can be send to the WagMan. A session ID (e.g. based on UUID) is used to identify the correct reply message.
Returns: "OK" on success
         "error"-prefixed error message in case of an error
"""


debug=1

if __name__ == "__main__":
    
    context = zmq.Context()
    server_socket = context.socket(zmq.REP)
    server_socket.bind('ipc:///tmp/zeromq_wagman-server')
    
    
    last_message=""
    
    symlink_not_found_msg="error: symlink %s not found" % (wagman_device)
    wagman_connected_msg = 'connected to %s!' % (wagman_device)
    
    
   
    while True:
        
        if not os.path.exists(wagman_device):
            if last_message != symlink_not_found_msg:
                last_message = symlink_not_found_msg
                logger.debug(symlink_not_found_msg)
            time.sleep(5)
            continue
            
            
        try:
            # connect to wagman
            
            with Serial(wagman_device, 57600, timeout=8, writeTimeout=8) as serial:
                last_message = wagman_connected_msg
                logger.debug(wagman_connected_msg)
                
                
                
                
                while True:
                    #  Wait for next request from client
                    if debug:
                        logger.debug("call recv")
                        
                        
                    try:
                        message = server_socket.recv()
                    except zmq.error.ZMQError as e:
                        logger.debug("zmq.error.ZMQError: (%s) %s" % (str(type(e)), str(e)))
                        server_socket.send_string("could not read message")
                        continue
                    except Exception as e:
                        logger.debug("error recv message: (%s) %s" % (str(type(e)), str(e)))
                        continue
        
                    print(("Received request: ", message))
                    
                    try:
                        if str(type(message))=="<class 'bytes'>":
                            if debug:
                                logger.debug("send message")
                            serial.write(message)
                        else:
                            if debug:
                                logger.debug("send message with encode")
                            serial.write(message.encode('ascii'))
                            
                        serial.write(b'\n')
                    except Exception as e:
                        logger.error("error in serial write: %s" % (str(e)))
                        server_socket.send_string("error (serial.write): %s" % str(e))
                        raise Exception('Could not write to %s: %s' % (wagman_device, str(e)))
    
                    try:
                        server_socket.send_string("OK")
                    except Exception as e:
                        raise Exception("error sending OK: %s" % str(e))
                        
        except Exception as e:
            logger.error("error in wagman-server.py: %s" % str(e))
            
        time.sleep(5)
                    
