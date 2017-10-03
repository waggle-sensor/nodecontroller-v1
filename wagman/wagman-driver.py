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

logging.basicConfig(level=logging.DEBUG)

header_prefix = '<<<-'
footer_prefix = '->>>'


def publisher(serial):
    logger = logging.getLogger('publisher')

    logger.info('starting')

    context = zmq.Context()

    socket = context.socket(zmq.PUB)
    socket.setsockopt(zmq.LINGER, 10000)
    socket.setsockopt(zmq.SNDTIMEO, 10000)
    socket.bind('ipc:///tmp/zeromq_wagman-pub')

    logger.info('ready')

    try:
        output = []
        incommand = False
        commandname = None
        session_id = ''

        while True:
            try:
                line = serial.readline().decode().strip()
            except UnicodeDecodeError:
                continue

            logger.debug('readline: {}'.format(line))

            if incommand:
                if line.startswith(footer_prefix):
                    incommand = False

                    if session_id:
                        header = '{} cmd.{}'.format(session_id, commandname)
                    else:
                        header = 'cmd.{}'.format(commandname)

                    body = '\n'.join(output)

                    logger.debug("sending header: {}".format(header))
                    logger.debug("sending body: {}".format(body))

                    msg = '{}\n{}'.format(header, body)

                    socket.send_string(msg)
                    output = []
                else:
                    output.append(line)
            elif line.startswith(header_prefix):
                session_id = ''
                logger.debug('received header: {}'.format(line))
                matchObj = re.match(r'.*sid=(\S+)', line, re.M | re.I)
                if matchObj:
                    session_id = matchObj.group(1).rstrip()

                if session_id:
                    logger.debug("detected session_id: {}".format(session_id))
                else:
                    logger.debug("no session_id detected")

                fields = line.split()
                logger.debug(fields)

                commandname = fields[-1]

                incommand = True
            elif line.startswith('log:'):
                socket.send_string(line)
    except Exception as exc:
        logger.error('fatal exception: {}'.format(exc))
    finally:
        logger.info('cleaning up')
        socket.send_string('error: not connected to wagman')
        socket.close()
        logger.info('terminating')


def server(serial):
    logger = logging.getLogger('server')

    logger.info('starting')

    context = zmq.Context()

    server_socket = context.socket(zmq.REP)
    server_socket.setsockopt(zmq.LINGER, 10000)
    server_socket.setsockopt(zmq.SNDTIMEO, 10000)
    server_socket.bind('ipc:///tmp/zeromq_wagman-server')

    logger.info('ready')

    try:
        while True:
            try:
                serial.write(server_socket.recv() + b'\n')
            except Exception as e:
                server_socket.send_string('ERROR')
                break
            else:
                server_socket.send_string('OK')
    except Exception as exc:
        logger.error('fatal exception: {}'.format(exc))
    finally:
        logger.info('cleaning up')
        server_socket.close()
        logger.info('terminating')


def manager(serial):
    logger = logging.getLogger('manager')

    logger.info('creating workers')

    processes = [
        Process(name='publisher', target=publisher, args=(serial,)),
        Process(name='server', target=server, args=(serial,)),
    ]

    logger.info('starting workers')

    for p in processes:
        p.start()

    logger.info('started workers')

    while all(p.is_alive() for p in processes):
        time.sleep(1)

    for p in processes:
        if not p.is_alive():
            logger.error('worker {} failed'.format(p.name))

    logger.info('terminating workers')

    for p in processes:
        p.terminate()

    logger.info('terminated workers')


def main():
    logger = logging.getLogger()

    try:
        wagman_device = sys.argv[1]
    except IndexError:
        wagman_device = '/dev/waggle_sysmon'

    for attempt in range(3):
        try:
            with Serial(wagman_device, 57600, timeout=10, writeTimeout=10) as serial:
                manager(serial)
        except KeyboardInterrupt:
            break
        except OSError:
            logger.warning('could not connect to device {}'.format(wagman_device))

        time.sleep(10)

    logger.error('too many attempts to open {}'.format(wagman_device))


if __name__ == '__main__':
    main()
