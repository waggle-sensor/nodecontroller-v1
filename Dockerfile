FROM ubuntu:14.04

RUN apt-get update 

ADD . /usr/lib/waggle/nodecontroller/

WORKDIR /usr/lib/waggle/nodecontroller/
