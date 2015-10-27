FROM ubuntu:14.04

RUN apt-get update && apt-get install -y python-pip

ADD . /usr/lib/waggle/nodecontroller/

WORKDIR /usr/lib/waggle/nodecontroller/
