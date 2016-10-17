#!/bin/bash

set -x
set -e

# python 2

apt-get install -y wvdial autossh bossa-cli curl

pip install crcmod
pip install pyserial


# python 3

apt-get install -y python3-zmq

pip3 install crcmod
pip3 install pyserial
pip3 install tabulate
pip3 install netifaces


#install pika package from the git repo.
cd nc-wag-os/packages/python/
pip install -e pika-0.10.0
pip3 install -e pika-0.10.0
