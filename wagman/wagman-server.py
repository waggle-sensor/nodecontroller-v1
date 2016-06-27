#!/usr/bin/env python3
import zmq
import sys
from serial import Serial
import time
import os.path


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
                print(symlink_not_found_msg)
            time.sleep(5)
            continue
            
            
        try:
            # connect to wagman
            
            with Serial(wagman_device, 115200, timeout=8, writeTimeout=8) as serial:
                last_message = wagman_connected_msg
                print(wagman_connected_msg)
                
                
                
                
                while True:
                    #  Wait for next request from client
                    if debug:
                        print("call recv")
                        
                        
                    try:
                        message = server_socket.recv()
                    except Exception as e:
                        print("error recv message: %s" % str(e))
                        server_socket.send_string("something")
                        continue
        
                    print("Received request: ", message)
    
                    try:
                        serial.write(message.encode('ascii'))
                        serial.write(b'\n')
                    except Exception as e:
                        server_socket.send_string("error (serial.write): %s" % str(e))
                        raise Exception('Could not write to %s: %s' % (wagman_device, str(e)))
    
                    try:
                        server_socket.send_string("OK")
                    except Exception as e:
                        raise Exception("error sending OK: %s" % str(e))
                        
        except Exception as e:
            print("error: %s" % str(e))
            
        time.sleep(5)
                    