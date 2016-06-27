#!/usr/bin/env python3
import zmq
import sys
from serial import Serial
import time

wagman_device = '/dev/waggle_sysmon'

"""
The WagMan server accepts commands that can be send to the WagMan. A session ID (e.g. based on UUID) is used to identify the correct reply message.
Returns: "OK" on success
         "error"-prefixed error message in case of an error
"""

if __name__ == "__main__":
    
    context = zmq.Context()
    server_socket = context.socket(zmq.REP)
    server_socket.bind('ipc:///tmp/zeromq_wagman-server')
    
    
    while True:
        try:
            # connect to device
            with Serial(wagman_device, 115200, timeout=8, writeTimeout=8) as serial:
                print('connected to %s!' % (wagman_device))
                
                
                
                
                while True:
                    #  Wait for next request from client
                    message = server_socket.recv()
                    print("Received request: ", message)
                    
                    try:
                        serial.write(message.encode('ascii'))
                        serial.write(b'\n')
                    except Exception as e:
                        server_socket.send("error (serial.write): %s" % str(e))
                        raise Exception('Could not write to %s: %s' % (wagman_device, str(e)))
                    
                    try:
                        server_socket.send("OK".encode('ascii'))
                    except Exception as e:
                        raise Exception("error sending OK: %s" % str(e))
                        
        except Exception as e:
            print("error: %s" % str(e))
            
        time.sleep(5)
                    