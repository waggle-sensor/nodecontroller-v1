#!/usr/bin/env python3

from serial import Serial
import zmq
import time
import sys




header_prefix = '<<<-'
footer_prefix = '->>>'
wagman_device = '/dev/waggle_sysmon'




if __name__ == "__main__":

    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind('tcp://*:5555')



    while True:
        try:
            # connect to device
            with Serial(wagman_device, 115200, timeout=5, write_timeout=5) as serial:
                print('connected!')

                output = []
                incommand = False
                commandname = None

                while True:
                    line = serial.readline().decode().strip()

                    if incommand:
                        if line.startswith(footer_prefix):
                            incommand = False
                            msg = 'cmd.{}:{}'.format(commandname, '\n'.join(output))
                            print(msg)
                            socket.send_string(msg)
                            output = []
                        else:
                            output.append(line)
                    elif line.startswith(header_prefix):
                        fields = line.split()
                        print(fields)
                        if len(fields) <= 2:
                            commandname = '?'
                        else:
                            commandname = fields[2]

                        incommand = True
                    elif line.startswith('log:'):
                        print(line)
                        socket.send_string(line)

            
        except Exception as e:
            print(e)
        
        time.sleep(5)
    
    