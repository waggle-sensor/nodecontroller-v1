#!/bin/bash
set -x
set -e
apt-get update && apt-get install -y \
    python-dev \
    python-pip \
    && \
    pip install crcmod

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
