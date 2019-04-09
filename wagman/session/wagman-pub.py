from serial import Serial
# ANL:waggle-license
#  This file is part of the Waggle Platform.  Please see the file
#  LICENSE.waggle.txt for the legal details of the copyright and software
#  license.  For more details on the Waggle project, visit:
#           http://www.wa8.gl
# ANL:waggle-license
import zmq
import time
import sys


context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind('tcp://*:5555')

while True:
    try:
        # connect to device
        serial = Serial(sys.argv[1], 57600, timeout=30)
        print('connected!')

        output = []
        incommand = False
        commandname = None

        while True:
            line = serial.readline().decode().strip()

            if incommand:
                if line.startswith('->>>'):
                    incommand = False
                    msg = 'cmd.{}:{}'.format(commandname, '\n'.join(output))
                    print(msg)
                    socket.send_string(msg)
                    output = []
                else:
                    output.append(line)
            elif line.startswith('<<<-'):
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

        serial.close()
    except Exception as e:
        print(e)
        time.sleep(5)
