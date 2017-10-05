#!/usr/bin/env python3
import serial
import zmq
import sys
import logging
import time
import re
from contextlib import ExitStack

logger = logging.getLogger('driver')
wagman_logger = logging.getLogger('wagman')

# this is globally shared - perhaps it's not ideal, but it works for now.
last_readline = time.time()


def readline(ser):
    global last_readline

    while True:
        # give up if global readline timeout is expired
        if time.time() - last_readline > 60.0:
            raise TimeoutError('wagman timed out')

        # read and decode wagman output
        try:
            line = ser.readline().decode()
        except UnicodeDecodeError:
            continue

        # handle serial port timeout with an empty response
        if len(line) == 0:
            raise TimeoutError('readline timed out')

        last_readline = time.time()

        # show wagman log output instead of returning
        if line.startswith('log:'):
            wagman_logger.info(line.lstrip('log:').strip())
            continue

        return line


def writeline(ser, line):
    ser.write(line.encode())
    ser.write(b'\n')


def sanitize(s):
    return ' '.join(re.findall(r'@?[A-Za-z0-9]+', s))


def dispatch(ser, command):
    writeline(ser, sanitize(command))

    start = time.time()

    # wait for header
    while True:
        # check for dispatch timeout
        if time.time() - start > 15.0:
            raise TimeoutError('dispatch timed out')

        try:
            line = readline(ser)
        except TimeoutError:
            continue

        logger.debug('line: {}'.format(line))

        _, sep, right = line.partition('<<<-')

        if sep:
            fields = right.split()
            sid = fields[0].split('=')[1]
            break

    lines = []

    # wait for footer
    while True:
        # check for dispatch timeout
        if time.time() - start > 15.0:
            raise TimeoutError('dispatch timed out')

        try:
            line = readline(ser)
        except TimeoutError:
            continue

        logger.debug('line: {}'.format(line))

        if '<<<-' in line:
            raise RuntimeError('unexpected message header')

        left, sep, _ = line.partition('->>>')

        if left:
            lines.append(left.strip())

        if sep:
            break

    # need support for err reponse
    return '@{} ok\n{}'.format(sid, '\n'.join(lines))


def manager(ser, server):
    global last_readline

    last_readline = time.time()

    while True:
        # timeout if we haven't seen any message from the wagman in the last 60s
        if time.time() - last_readline > 60.0:
            raise TimeoutError('wagman timed out')

        # read and process requests
        try:
            command = server.recv_string()
            response = dispatch(ser, command)
            server.send_string(response)
        except zmq.error.Again:
            pass

        # read non-request lines (logging / debug)
        try:
            readline(ser)
        except TimeoutError:
            pass


def main(device):
    with ExitStack() as stack:
        context = stack.enter_context(zmq.Context())
        server = stack.enter_context(context.socket(zmq.REP))

        # do not attempt to complete client requests during cleanup
        server.setsockopt(zmq.LINGER, 0)

        # do not wait on client for more than 1s
        server.setsockopt(zmq.RCVTIMEO, 1000)
        server.setsockopt(zmq.SNDTIMEO, 1000)

        server.bind('ipc://wagman-server')

        ser = stack.enter_context(serial.Serial(device, 57600, timeout=1.0))

        manager(ser, server)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--device', type=str, default='/dev/waggle_sysmon')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    while True:
        try:
            logger.info('starting main')
            main(device=args.device)
        except KeyboardInterrupt:
            break
        except Exception:
            logger.exception('fatal exception in main. will restart in 15s...')

        time.sleep(15)
