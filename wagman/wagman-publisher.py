#!/usr/bin/env python3
"""
The WagMan publisher is responsible for distributing output of the Wagman
serialline to subscribers. Subscribers may need to use a session ID.
"""
from serial import Serial
import zmq
import time
import sys
import os.path
import re

header_prefix = '<<<-'
footer_prefix = '->>>'

if len(sys.argv) > 1:
    wagman_device = sys.argv[1]
else:
    wagman_device = '/dev/waggle_sysmon'

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind('ipc:///tmp/zeromq_wagman-pub')

last_message = ''

symlink_not_found_msg = 'error: symlink %s not found' % (wagman_device)
wagman_connected_msg = 'connected to %s!' % (wagman_device)

while True:
    try:
        with Serial(wagman_device, 57600, timeout=8, writeTimeout=8) as serial:
            last_message = wagman_connected_msg
            print(wagman_connected_msg)

            output = []
            incommand = False
            commandname = None
            session_id = ''

            while True:
                line = serial.readline().decode().strip()

                if incommand:
                    if line.startswith(footer_prefix):
                        incommand = False

                        if session_id:
                            header = '{} cmd.{}'.format(session_id, commandname)
                        else:
                            header = 'cmd.{}'.format(commandname)

                        body = '\n'.join(output)

                        print("sending header:", header)
                        print("sending body:", body)

                        msg = '{}\n{}'.format(header, body)

                        socket.send_string(msg)
                        output = []
                    else:
                        output.append(line)
                elif line.startswith(header_prefix):
                    session_id=''
                    print("received header:", line)
                    matchObj = re.match( r'.*sid=(\S+)', line, re.M|re.I)
                    if matchObj:
                        session_id=matchObj.group(1).rstrip()

                    if session_id:
                        print("detected session_id:", session_id)
                    else:
                        print("no session_id detected")

                    fields = line.split()
                    print(fields)

                    #if len(fields) <= 2:
                    #    commandname = '?'
                    #else:
                    #    commandname = fields[2]

                    commandname = fields[-1]

                    incommand = True
                elif line.startswith('log:'):
                    print(line)
                    socket.send_string(line)

    except Exception as e:
        socket.send_string("error: not connected to wagman")
        if str(e) != last_message:
            print(e)
            previous_error = str(e)

    time.sleep(5)
