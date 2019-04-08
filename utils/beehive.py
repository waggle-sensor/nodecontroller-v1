#!/usr/bin/env python3
# ANL:waggle-license
#  This file is part of the Waggle Platform.  Please see the file
#  LICENSE.waggle.txt for the legal details of the copyright and software
#  license.  For more details on the Waggle project, visit:
#           http://www.wa8.gl
# ANL:waggle-license
'''
This module provides an interface to the Beehive messaging server. Here is a
simple example of using it to repeatedly send sensor data:

import beehive

connection = beehive.Connection(
    host='beehive',
    port=23181,
    node='0000000000AAAAAA',
    keyfile='/etc/waggle/key.pem',
    certfile='/etc/waggle/cert.pem',
    caroot='/etc/waggle/cacert.pem')

while True:
    timestamp_utc = datetime.datetime.utcnow()
    timestamp_date = timestamp_utc.date()
    timestamp_epoch = int(float(timestamp_utc.strftime("%s.%f"))) * 1000

    message_data = [
        str(timestamp_date),
        'constant_plugin',
        '1',
        'default',
        '%d' % timestamp_epoch,
        'sensor_reading',
        'none',
        ['1', '2', '3'],
    ]

    connection.send_data(message_data)
    time.sleep(1)
'''
from os.path import abspath
import pika
import ssl
import pickle
import zlib
from packet import pack


class Connection(object):
    ''' Creates and manages a connection to the Beehive message server. '''

    def __init__(self, host, port, node, keyfile, certfile, caroot):
        self.host = host
        self.port = port
        self.node = node
        self.keyfile = abspath(keyfile)
        self.certfile = abspath(certfile)
        self.caroot = abspath(caroot)

        credentials = pika.PlainCredentials('node', 'waggle')

        ssl_options = {
            'ca_certs': self.caroot,
            'certfile': self.certfile,
            'keyfile': self.keyfile,
            'cert_reqs': ssl.CERT_REQUIRED,
        }

        parameters = pika.ConnectionParameters(
            host=host,
            credentials=credentials,
            virtual_host='/',
            port=port,
            ssl=True,
            ssl_options=ssl_options)

        self.connection = pika.BlockingConnection(parameters)

        self.channel = self.connection.channel()

        # consider push_queue / pull_queue
        # may also have different queues for different
        # message types
        self.queue = 'node_{}'.format(self.node)
        self.channel.queue_declare(queue=self.queue)

    def close(self):
        ''' Closes the connection. '''
        self.connection.close()

    def send_data(self, data):
        '''
        Sends a data packet over the connection. This is allowed to be any
        Python object that supports pickling.
        '''
        header_data = {
            's_uniqid': int(self.node, 16),
            'msg_mj_type': ord('s'),
            'msg_mi_type': ord('d'),
        }

        message_data = zlib.compress(pickle.dumps(data))

        for data in pack(header_data, message_data):
            self.channel.basic_publish(exchange='waggle_in',
                                       routing_key='in',
                                       body=data)
