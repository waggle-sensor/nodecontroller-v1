#!/usr/bin/env python3

import sys, os
from serial import Serial
from tabulate import tabulate
import zmq
import sys
import uuid


"""
Client script/library to talk to the WagMan. The library uses zeromq to talk with WagMan publisher and server. 
"""


header_prefix = '<<<-'
footer_prefix = '->>>'
wagman_device = '/dev/waggle_sysmon'


# make sure you keep util/wagman-client.bash_completion in sync !
usage_dict={
    'start'     : [['start <portnum>', 'starts device on portnum']],
    'stop'      : [['stop <portnum>', 'stops device on portnum']],
    'stop!'     : [['stop! <portnum>', 'immediately kills power to device on portnum']],
    'info'      : [['info', 'prints some system info']],
    'eedump'    : [['edump', 'prints a hex dump of all EEPROM']],
    'date'      : [['date', 'shows rtc date and time'], 
                    ['date <year> <month> <day> <hour> <minute> <second>', 'sets rtc date and time']],
    'cu'        : [['cu', 'current usage']],
    'hb'        : [['hb', 'last heartbeat times']],
    'therm'     : [['therm', 'thermistor values (though none are connected right now)']],
    'help'      : [['help', '']]
    }


def send_request(command):
    
    # connection to server to send request
    socket_client = context.socket(zmq.REQ)
    socket_client.connect('ipc:///tmp/zeromq_wagman-server')
    
    try:
        socket_client.send(command)
        #serial.write(command.encode('ascii'))
        #serial.write(b'\n')
    except Exception as e:
        raise Exception('error %s' % (str(e)))
        
        
    message = socket_client.recv()
    
    if not message == "OK":
        raise Exception("wagman-server returned: %s" % (message))
    

def wagman_client(args):
    
    if not os.path.islink(wagman_device):
        raise Exception('Symlink %s not found' % (wagman_device))
    
    command = ' '.join(args)
    
    session_id = uuid.uuid4()
    
    # first subscribe, then send request
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect('ipc:///tmp/zeromq_wagman-pub')
    
    
    

    # only waits for session response
    socket.setsockopt_string(zmq.SUBSCRIBE, bytes(session_id, encoding="latin-1"))
    

    # send request to server
    try:
        send_request(command)
    except Exception as e:
        raise Exception("Error sending request: %s" % (str(e)))
    
    
    # get response from publisher
    
    try:
        response = socket.recv_string()
    except Exception as e:
        raise Exception("Error receiving response: %s" % (str(e)))
        
    print("Response:", response)
    prefix, _, content = response.partition(':')

    if prefix.startswith('cmd'):
        print('{}:'.format(prefix))
        print(content.strip())
    else:
        print(content.strip())
            

def wagman_log():
    
    context = zmq.Context()
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
    try:
        for cmd in wagman_client(['help']):
            if cmd in usage_dict:
                for syntax in usage_dict[cmd]:
                    #print "\n".join(variant)
                    data.append(syntax)
            else:
                data.append([cmd, ''])
    except Exception as e:
        print("error: ", str(e))
        print("Note: help is only available when the wagman is connected.")
        sys.exit(1)


    print(tabulate(data, theader, tablefmt="psql"))
    sys.exit(0)
    

if __name__ == "__main__":

    
    if len(sys.argv) <= 1:
        usage()
         
    if len(sys.argv) > 1: 
        if sys.argv[1] == 'help' or sys.argv[1] == '?':
            usage()
        if sys.argv[1] == 'log':
            wagman_log()
            sys.exit(0)
            

    try:
        for line in wagman_client(sys.argv[1:]):
            print(line)
    except Exception as e:
        print("error: ", str(e))
        sys.exit(1)




