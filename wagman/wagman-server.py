#!/usr/bin/env python3
"""
The WagMan server accepts commands that can be send to the WagMan. A session ID
(e.g. based on UUID) is used to identify the correct reply message.
"""
import zmq
import sys
from serial import Serial
import time
import os.path
import logging


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

if len(sys.argv) > 1:
    wagman_device = sys.argv[1]
else:
    wagman_device = '/dev/waggle_sysmon'

context = zmq.Context()
server_socket = context.socket(zmq.REP)
server_socket.setsockopt(zmq.SNDTIMEO, 15000)
server_socket.bind('ipc:///tmp/zeromq_wagman-server')

while True:
    try:
        with Serial(wagman_device, 57600, timeout=8, writeTimeout=8) as serial:
            logging.debug('connected')

            while True:
                logging.debug('waiting for message')
                message = server_socket.recv()
                logging.debug('Received request: {}'.format(message))

                try:
                    serial.write(message)
                    serial.write(b'\n')
                except Exception as e:
                    server_socket.send_string('ERROR')
                    raise e
                else:
                    server_socket.send_string('OK')

    except Exception as e:
        logging.error(e)

    time.sleep(5)
