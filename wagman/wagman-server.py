#!/usr/bin/env python3
import zmq
import sys
from serial import Serial


wagman_device = '/dev/waggle_sysmonX'



if __name__ == "__main__":
    
    server_socket = context.socket(zmq.REP)
    server_socket.bind('ipc:///tmp/zeromq_wagman-server')
    
    while True:
        try:
            # connect to device
            with Serial(wagman_device, 115200, timeout=8, writeTimeout=8) as serial:
                print('connected to %s!' % (wagman_device))
                
                
                
                
                while True:
                    #  Wait for next request from client
                    message = socket.recv()
                    print "Received request: ", message
                    
                    try:
                        serial.write(message.encode('ascii'))
                        serial.write(b'\n')
                    except Exception as e:
                        socket.send("error: %s" % str(e))
                        raise Exception('Could not write to %s: %s' % (wagman_device, str(e)))
                    
                    socket.send("OK")
                    