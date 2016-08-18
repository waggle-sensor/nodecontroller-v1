#!/usr/bin/env python3
"""
Client script/library to talk to the WagMan. The library uses zeromq to talk
with WagMan publisher and server.
"""
import sys
from serial import Serial
from tabulate import tabulate
import zmq
import logging
from datetime import datetime


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


context = zmq.Context()

header_prefix = '<<<-'
footer_prefix = '->>>'

# make sure you keep util/wagman-client.bash_completion in sync !
usage_array = [
    ['start',       ['start <portnum>',     'starts device on portnum']],
    ['stop',        ['stop <portnum>',      'stops device on portnum']],
    ['stop!',       ['stop! <portnum>',     'immediately kills power to device on portnum']],
    ['info',        ['info',                'prints some system info']],
    ['eedump',      ['edump',               'prints a hex dump of all EEPROM']],
    ['date',        ['date',                'shows rtc date and time'],
                    ['date <year> <month> <day> <hour> <minute> <second>', 'sets rtc date and time']],
    ['cu',          ['cu',                  'current usage']],
    ['hb',          ['hb',                  'last heartbeat times']],
    ['therm',       ['therm',               'thermistor values (though none are connected right now)']],
    ['help',        ['help',                'displays help']],
    ['id',          ['id',                  'return WagMan unique identifier']],
    ['log',         ['log',                 'toggles logging']],
    ['bf',          ['bf',                  'displays boot reset flags']],
    ['reset',       ['reset',               'resets the wagman']],
    ['th',          ['th',                  'displays thermistor values']],
    ['bs',          ['bs <devnum>',         'displays boot media selection']],
    ['fc',          ['fc',                  'displays fail counts']],
    ['ping',        ['ping',                'requests a pong response'],
                    ['ping <devnum>',       'send external heartbeat for device']]
]


def random_id():
    from random import randint
    return str(randint(0, 999))


def send_request(command):
    socket_client = context.socket(zmq.REQ)
    socket_client.setsockopt(zmq.SNDTIMEO, 5000)
    socket_client.setsockopt(zmq.RCVTIMEO, 5000)

    socket_client.connect('ipc:///tmp/zeromq_wagman-server')

    socket_client.send_string(command)
    message = socket_client.recv_string()

    if message != 'OK':
        raise RuntimeError('wagman-server returned: {}'.format(message))


def wagman_client(args):
    command = ' '.join(args)

    session_id = random_id()

    # first subscribe, then send request
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.RCVTIMEO, 5000)
    socket.connect('ipc:///tmp/zeromq_wagman-pub')

    socket.setsockopt_string(zmq.SUBSCRIBE, session_id)
    send_request('@{} {}'.format(session_id, command))
    response = socket.recv_string()

    socket.setsockopt_string(zmq.UNSUBSCRIBE, session_id)

    logging.debug('Response: "{}"'.format(response))

    header, _, body = response.partition('\n')

    logging.debug('header: {}'.format(header))
    logging.debug('body: {}'.format(body))

    return header, body


def wagman_log():

    socket = context.socket(zmq.SUB)
    socket.connect('ipc:///tmp/zeromq_wagman-pub')

    # only waits for session response
    socket.setsockopt_string(zmq.SUBSCRIBE, 'log:')

    while True:
        response = socket.recv_string()
        print(response)
        prefix, _, content = response.partition(':')

        if prefix.startswith('cmd'):
            print('{}:'.format(prefix))
            print(content.strip())
        else:
            print(content.strip())


def usage():
    theader = ['syntax', 'description']
    data=[]
    supported_commands={}
    documented_commands={}
    undocumented_commands={}

    for syntax_obj in usage_array:
        cmd = syntax_obj[0]
        documented_commands[cmd]=1

    try:
        result = wagman_client(['help'])
        for cmd in result[1].split('\n'):
            supported_commands[cmd]=1
            if not cmd in documented_commands:
                undocumented_commands[cmd]=1

    except Exception as e:
        print("error: ", str(e))
        print("Note: help is only available when the wagman is connected.")
        sys.exit(1)

    #for cmd in usage_dict.keys():
    for syntax_obj in usage_array:
        cmd = syntax_obj[0]
        if cmd in supported_commands:
            for syntax in syntax_obj[1:]:
                data.append(syntax)

        else:
            data.append([cmd, ''])

    for cmd in undocumented_commands.keys():
        data.append([cmd, ' '])

    print(tabulate(data, theader, tablefmt="psql"))
    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        usage()
    elif len(sys.argv) == 2 and sys.argv[1] == 'epoch':
        _, result = wagman_client(['date'])
        year, month, day, hour, minute, second = map(int, result.split())
        epoch = datetime(year, month, day, hour, minute, second).strftime('%s')
        print(epoch)
    elif len(sys.argv) > 1:
        if sys.argv[1] == 'help' or sys.argv[1] == '?':
            usage()
        if sys.argv[1] == 'log':
            wagman_log()
            sys.exit(0)
        result = wagman_client(sys.argv[1:])
        print(result[1])
