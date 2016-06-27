#!/usr/bin/env python3

import sys, os
from serial import Serial
from tabulate import tabulate
import zmq
import sys
import uuid
import time

"""
Client script/library to talk to the WagMan. The library uses zeromq to talk with WagMan publisher and server. 
"""


header_prefix = '<<<-'
footer_prefix = '->>>'
wagman_device = '/dev/waggle_sysmon'

debug=0

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
    context = zmq.Context()
    socket_client = context.socket(zmq.REQ)
    socket_client.connect('ipc:///tmp/zeromq_wagman-server')
    
    
    #make sure first to receive, in case something has to be retrived first
    skip = 0
    try:
        message = socket_client.recv(zmq.NOBLOCK)
    except zmq.error.Again as e:
        # no message, that is ok.
        skip=1
    except zmq.error.ZMQError as e:
        # all was ok, it should not have tried to receive message
        skip=1
    except Exception as e:
        if skip==0:
            raise Exception("warning recv: (%s) %s" % (type(e), str(e)))
    
    
    try:
        socket_client.send(command.encode('ascii'))
        #serial.write(command.encode('ascii'))
        #serial.write(b'\n')
    except Exception as e:
        raise Exception('error (%s) %s' % (type(e), str(e)))
        
    message = None
    timeout = 0
    while (message == None):
        try:
            message = socket_client.recv(zmq.NOBLOCK)
        except zmq.error.Again as e:
            # no message
            if (timeout > 5):
                raise Exception("timeout")
    
            timeout+=1
            time.sleep(1)
            continue
        except Exception as e:
            raise("error recv: %s" % str(e))
    
    if not message == b"OK":
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
    
    
    # TODO use session_id ! 
    session_id=''

    # only waits for session response
    try:
        socket.setsockopt_string(zmq.SUBSCRIBE, str(session_id))
    except Exception as e:
        raise Exception("Error insetsockopt_string: %s" % (str(e)))

    # send request to server
    try:
        send_request(command)
    except Exception as e:
        raise Exception("Error sending request: %s" % (str(e)))
    
    
    # get response from publisher
    
    timeout=0
    response=''
    while 1:
        try:
            response = socket.recv_string(zmq.NOBLOCK)
        except zmq.error.Again as e:
            # no message
            if timeout > 5:
                raise Exception('recv_string timeout')
        
            timeout+=1
            time.sleep(1)
            
            continue
        except Exception as e:
            
            raise Exception("Error receiving response (%s): %s" % (type(e), str(e)))
        break
    if debug:    
        print("Response: \"%s\"" % (response))
        
    header, _, body = response.partition('\n')

    if debug:
        print("header:", header)
        print("body:", body)
        
    return [header, body]
    #if prefix.startswith('cmd'):
    #    print('{}:'.format(prefix))
    #    print(content.strip())
    #else:
    #    print(content.strip())
            

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
        result = wagman_client(['help'])
        for cmd in result[1].split('\n'):
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
        result = wagman_client(sys.argv[1:])
        print(result[1]) # prints body
    except Exception as e:
        print("error: ", str(e))
        sys.exit(1)




