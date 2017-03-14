#!/usr/bin/python3

import pika
import sys
import time
import json

with open('/usr/lib/waggle/nodecontroller/scripts/testing/fake_image.b64') as image_file:
  image = image_file.read()

connection = pika.BlockingConnection(
  pika.ConnectionParameters("localhost"))
channel = connection.channel()
#channel.exchange_declare(exchange='images', type='fanout')
body = json.dumps({'results':[1234, 5678], 'image':image})
channel.basic_publish(exchange='images', routing_key='', body=body)
