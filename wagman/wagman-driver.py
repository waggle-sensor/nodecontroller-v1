#!/usr/bin/env python3
"""
The WagMan publisher is responsible for distributing output of the Wagman
serialline to subscribers. Subscribers may need to use a session ID.
"""
from serial import Serial
import zmq
import time
import sys
import re
import logging
from multiprocessing import Process

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

header_prefix = '<<<-'
footer_prefix = '->>>'


def publisher(serial):
    context = zmq.Context()

    socket = context.socket(zmq.PUB)
    socket.setsockopt(zmq.SNDTIMEO, 15000)
    socket.bind('ipc:///tmp/zeromq_wagman-pub')

    try:
        output = []
        incommand = False
        commandname = None
        session_id = ''

        while True:
            line = serial.readline().decode().strip()
            print(line)

            if incommand:
                if line.startswith(footer_prefix):
                    incommand = False

                    if session_id:
                        header = '{} cmd.{}'.format(session_id, commandname)
                    else:
                        header = 'cmd.{}'.format(commandname)

                    body = '\n'.join(output)

                    logging.debug("sending header: {}".format(header))
                    logging.debug("sending body: {}".format(body))

                    msg = '{}\n{}'.format(header, body)

                    socket.send_string(msg)
                    output = []
                else:
                    output.append(line)
            elif line.startswith(header_prefix):
                session_id = ''
                logging.debug('received header: {}'.format(line))
                matchObj = re.match(r'.*sid=(\S+)', line, re.M | re.I)
                if matchObj:
                    session_id = matchObj.group(1).rstrip()

                if session_id:
                    logging.debug("detected session_id: {}".format(session_id))
                else:
                    logging.debug("no session_id detected")

                fields = line.split()
                logging.debug(fields)

                commandname = fields[-1]

                incommand = True
            elif line.startswith('log:'):
                socket.send_string(line)
    finally:
        socket.send_string('error: not connected to wagman')


def server(serial):
    context = zmq.Context()

    server_socket = context.socket(zmq.REP)
    server_socket.setsockopt(zmq.SNDTIMEO, 15000)
    server_socket.bind('ipc:///tmp/zeromq_wagman-server')

    while True:
        try:
            serial.write(server_socket.recv() + b'\n')
        except Exception as e:
            server_socket.send_string('ERROR')
            break
        else:
            server_socket.send_string('OK')


if __name__ == '__main__':
    try:
        wagman_device = sys.argv[1]
    except IndexError:
        wagman_device = '/dev/waggle_sysmon'

    while True:
        try:
            with Serial(wagman_device, 57600, timeout=10, writeTimeout=10) as serial:
                processes = [
                    Process(target=publisher, args=(serial,)),
                    Process(target=server, args=(serial,)),
                ]

                for p in processes:
                    p.start()

                while all(p.is_alive() for p in processes):
                    time.sleep(1)

                for p in processes:
                    p.terminate()
        except OSError:
            print('could not connect to device')
        time.sleep(3)
