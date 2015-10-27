FROM ubuntu:14.04

RUN apt-get update && apt-get install -y \
  python-dev \
  python-pip \
  && \
  pip install crcmod

ADD . /usr/lib/waggle/nodecontroller/

WORKDIR /usr/lib/waggle/nodecontroller/
