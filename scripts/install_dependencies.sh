#!/bin/bash

set -x
set -e
apt-get install -y \
    python-dev \
    python-pip \
    && \
    pip install crcmod

# install rabbitmq server
echo 'deb http://www.rabbitmq.com/debian/ testing main' | sudo tee /etc/apt/sources.list.d/rabbitmq.list

wget -O- https://www.rabbitmq.com/rabbitmq-release-signing-key.asc | sudo apt-key add -

apt-get update
apt-get install -y rabbitmq-server

#install pika package from the git repo.
cd nc-wag-os/packages/python/

pip install -e pika-0.10.0
pip install pyserial


# python3

apt-get install -y python3-pip python3-zmq

pip3 install -e pika-0.10.0
pip3 install crcmod
pip3 install pyserial
pip3 install tabulate
pip3 install netifaces
