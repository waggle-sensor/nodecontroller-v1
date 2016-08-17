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
server_socket.bind('ipc:///tmp/zeromq_wagman-server')

last_message = ''
symlink_not_found_msg = "error: symlink %s not found" % (wagman_device)
wagman_connected_msg = 'connected to %s!' % (wagman_device)

while True:
    try:
        with Serial(wagman_device, 57600, timeout=8, writeTimeout=8) as serial:
            last_message = wagman_connected_msg
            logging.debug(wagman_connected_msg)

            while True:
                #  Wait for next request from client
                logging.debug("waiting for message")

                try:
                    message = server_socket.recv()
                except zmq.error.ZMQError as e:
                    logging.error("zmq.error.ZMQError: (%s) %s" % (str(type(e)), str(e)))
                    server_socket.send_string("could not read message")
                    continue
                except Exception as e:
                    logging.error("error recv message: (%s) %s" % (str(type(e)), str(e)))
                    continue

                logging.info("Received request: {}".format(message))

                try:
                    if str(type(message))=="<class 'bytes'>":
                        logging.debug("send message")
                        serial.write(message)
                    else:
                        logging.debug("send message with encode")
                        serial.write(message.encode('ascii'))

                    serial.write(b'\n')
                except Exception as e:
                    logging.error("error in serial write: %s" % (str(e)))
                    server_socket.send_string("error (serial.write): %s" % str(e))
                    raise Exception('Could not write to %s: %s' % (wagman_device, str(e)))

                try:
                    server_socket.send_string("OK")
                except Exception as e:
                    raise Exception("error sending OK: %s" % str(e))

    except Exception as e:
        logging.error("error in wagman-server.py: %s" % str(e))

    time.sleep(5)
