import zmq
# ANL:waggle-license
#  This file is part of the Waggle Platform.  Please see the file
#  LICENSE.waggle.txt for the legal details of the copyright and software
#  license.  For more details on the Waggle project, visit:
#           http://www.wa8.gl
# ANL:waggle-license
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
