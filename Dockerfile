FROM ubuntu:16.04

# git is installed for development purposes only, will remove later
RUN apt-get update ; apt-get install -y git wget

ADD . /usr/lib/waggle/nodecontroller/

RUN cd /usr/lib/waggle/ && git clone https://github.com/waggle-sensor/waggle_image.git

RUN cd /usr/lib/waggle/waggle_image/ && git checkout virtual-node

RUN cd /usr/lib/waggle/waggle_image/ && ./scripts/install_dependencies.sh

RUN pip install git+https://github.com/waggle-sensor/pywaggle@v0.11.6
RUN pip3 install git+https://github.com/waggle-sensor/pywaggle@v0.11.6

WORKDIR /usr/lib/waggle/nodecontroller/

# ports for internal communication with guest nodes
EXPOSE 9090 9091 
