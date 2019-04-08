#!/usr/bin/python3
# ANL:waggle-license
#  This file is part of the Waggle Platform.  Please see the file
#  LICENSE.waggle.txt for the legal details of the copyright and software
#  license.  For more details on the Waggle project, visit:
#           http://www.wa8.gl
# ANL:waggle-license

import argparse
import pika
import time

LOGS_EXCHANGE = 'logs.fanout'

connection = None
channel = None

def init():
	global connection, channel
	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()

def deinit():
	global connection
	connection.close()

def callback(ch, method, properties, body):
	print(body)

def watch(dest, type='queue'):
	global channel
	init()
	if not channel:
		print("connection failed")
		# exit()

	if "exchange" in type:
		result = channel.queue_declare(exclusive=True)
		channel.queue_bind(exchange=dest, queue=result.method.queue)
		channel.basic_consume(callback, queue=result.method.queue, no_ack=True)
		# channel.basic_consume(callback, exchange=dest, no_act=True)
	elif "queue" in type:
		channel.basic_consume(callback, queue=dest, no_ack=True)
	channel.start_consuming()

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('-q', dest='queue', help='Specify queue name to watch')
	parser.add_argument('-e', dest='exchange', help='Specify exchange name to watch')
	args = parser.parse_args()

	try:
		if args.queue:
			watch(args.queue)
		elif args.exchange:
			watch(args.exchange, type='exchange')
	except (KeyboardInterrupt, Exception) as e:
		pass

	deinit(
