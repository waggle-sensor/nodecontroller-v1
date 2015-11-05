#!/bin/bash
set -x
set -e
apt-get update && apt-get install -y \
    python-dev \
    python-pip \
    && \
    pip install crcmod

