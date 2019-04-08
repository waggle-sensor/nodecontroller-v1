#!/usr/bin/env python3
# ANL:waggle-license
#  This file is part of the Waggle Platform.  Please see the file
#  LICENSE.waggle.txt for the legal details of the copyright and software
#  license.  For more details on the Waggle project, visit:
#           http://www.wa8.gl
# ANL:waggle-license
from contextlib import ExitStack
import zmq
import sys
import re
import time

descriptions = sorted([
    ('rtc', 'shows rtc timestamp'),
    ('ping', 'simulate a device heartbeat'),
    ('start', 'starts a device immediately'),
    ('stop', 'stops a device after specified number of seconds'),
    ('reset', 'resets the wagman!'),
    ('id', 'shows wagman id'),
    ('cu', 'shows current usage'),
    ('hb', 'shows milliseconds since device heartbeats'),
    ('env', 'shows wagman temperature and humidity'),
    ('bs', 'shows selected boot media'),
    ('th', 'shows thermistor values'),
    ('date', 'shows current date'),
    ('bf', 'shows wagman boot flags'),
    ('fc', 'shows device failure counts'),
    ('up', 'shows wagman uptime'),
    ('enable', 'enables device'),
    ('disable', 'disables device'),
    ('eereset', 'prepares wagman to persistant memory on next reset'),
    ('boots', 'shows number of times wagman has booted'),
    ('ver', 'shows hardware and firmware version info'),
    ('blf', 'show / set bootloader phase boot flag'),
    ('sdinfo', 'show sd card info'),
])

commands = {name for name, _ in descriptions}


def check_args(args):
    if args[0] not in commands:
        print('invalid command: {}'.format(args[0]))
        sys.exit(1)


def sanitize(s):
    return ' '.join(re.findall(r'[A-Za-z0-9]+', s))


def dispatch(args, timeout):
    with ExitStack() as stack:
        context = stack.enter_context(zmq.Context())
        client = stack.enter_context(context.socket(zmq.REQ))

        # do not attempt to complete incomplete request on exit
        client.setsockopt(zmq.LINGER, 0)

        # do not wait for more than timeout seconds
        timeout_ms = int(timeout * 1000)
        client.setsockopt(zmq.RCVTIMEO, timeout_ms)
        client.setsockopt(zmq.SNDTIMEO, timeout_ms)

        client.connect('ipc:///tmp/wagman-server')

        try:
            client.send_string(sanitize(' '.join(args)))
            header, _, body = client.recv_string().partition('\n')
        except zmq.error.Again:
            raise TimeoutError('request timed out')

        if 'invalid command' in body:
            raise RuntimeError('invalid command')

        return body


def main(args, timeout=15.0, retry_delay=5.0, retry_attempts=3):
    check_args(args)

    for attempt in range(retry_attempts):
        try:
            print(dispatch(args, timeout=timeout))
            break
        except KeyboardInterrupt:
            break
        except Exception:
            pass

        time.sleep(retry_delay)
    else:
        print('request failed', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    import argparse

    epilog = 'wagman commands:\n{}'.format('\n'.join(['  {: <10} {}'.format(name, descr) for name, descr in descriptions]))

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='command and controller interface to the wagman.',
        epilog=epilog)

    parser.add_argument('--timeout', type=float, default=15.0)
    parser.add_argument('--retry-delay', type=float, default=5.0)
    parser.add_argument('--retry-attempts', type=int, default=3)
    parser.add_argument('args', nargs='+')

    args = parser.parse_args()

    main(args=args.args,
         timeout=args.timeout,
         retry_delay=args.retry_delay,
         retry_attempts=args.retry_attempts)
