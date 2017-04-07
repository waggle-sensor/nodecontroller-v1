import zmq
import sys


context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect('tcp://localhost:5555')
socket.setsockopt_string(zmq.SUBSCRIBE, sys.argv[1])

while True:
    response = socket.recv_string()
    prefix, _, content = response.partition(':')

    if prefix.startswith('cmd'):
        print('{}:'.format(prefix))
        print(content.strip())
    else:
        print(content.strip())
