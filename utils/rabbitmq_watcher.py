#!/usr/bin/python3

import argparse
import pika

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
		exit()

	if type == "exchange":
		result = channel.queue_declare(exclusive=True)
		channel.queue_bind(exchange=dest, queue=result.method.queue)
		channel.basic_consume(callback, queue=result.method.queue, no_act=True)
		# channel.basic_consume(callback, exchange=dest, no_act=True)
	elif type == "queue":
		channel.basic_consume(callback, queue=dest, no_act=True)
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
	except 