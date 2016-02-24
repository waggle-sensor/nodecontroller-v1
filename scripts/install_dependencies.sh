#!/bin/bash
set -x
set -e
apt-get update && apt-get install -y \
    python-dev \
    python-pip \
    supervisor \
    && \
    pip install crcmod

#install pika package from the git repo.
cd nc-wag-os/packages/python/

pip install -e pika-0.9.14
pip install pyserial
