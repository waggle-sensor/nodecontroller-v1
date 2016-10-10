#!/usr/bin/env bash

# NC configuration for RabbitMQ
# init
rabbitmq-plugins enable rabbitmq_management
rabbitmq-plugins enable rabbitmq_shovel
wget http://server-name:15672/cli/rabbitmqadmin
cp rabbitmqadmin /usr/local/bin

# queues
rabbitmqadmin declare queue name=data durable=true arguments='{"x-max-priority":5}'

# exchanges
rabbitmqadmin declare exchange name=outgoing type=direct durable=true
rabbitmqadmin declare exchange name=incoming type=direct durable=true

# bindings
rabbitmqadmin declare binding source=outgoing destination=data routing_key=data

# Dynamic Shovel configuration
rabbitmqctl set_parameter shovel data_shovel '{"src-uri": "amqp://", "src-queue": "data", "dest-uri": "amqp://waggle:waggle@10.10.10.169", "dest-exchange": "incoming"}'
