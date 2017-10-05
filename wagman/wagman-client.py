#!/usr/bin/env python3
from contextlib import ExitStack
import zmq
import sys
import re
import time

commands = {
    'rtc',
    'ping',
    'start',
    'stop',
    'reset',
    'id',
    'cu',
    'hb',
    'env',
    'bs',
    'th',
    'date',
    'bf',
    'fc',
    'up',
    'enable',
    'disable',
    'watch',
    'log',
    'eereset',
    'boots',
    'ver',
    'blf',
}


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

        client.connect('ipc://wagman-server')

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

    parser = argparse.ArgumentParser()

    parser.add_argument('--timeout', type=float, default=15.0)
    parser.add_argument('--retry-delay', type=float, default=5.0)
    parser.add_argument('--retry-attempts', type=int, default=3)
    parser.add_argument('args', nargs='+')

    args = parser.parse_args()

    main(args=args.args,
         timeout=args.timeout,
         retry_delay=args.retry_delay,
         retry_attempts=args.retry_attempts)
