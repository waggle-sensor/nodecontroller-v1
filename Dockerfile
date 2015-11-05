FROM ubuntu:14.04

ADD . /usr/lib/waggle/nodecontroller/

RUN /usr/lib/waggle/nodecontroller/scripts/install_dependencies.sh

WORKDIR /usr/lib/waggle/nodecontroller/
