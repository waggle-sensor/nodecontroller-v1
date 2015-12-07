

## Installation

The nodecontroller is already installed on the Waggle image. If you need the very latest version of the nodecontroller you can do a git pull:

```bash
cd /usr/lib/waggle/nodecontroller/
git pull
```

Alternatively you can do a git clone on any Linux:

```bash
mkdir -p /usr/lib/waggle/
cd /usr/lib/waggle/
git clone --recursive https://github.com/waggle-sensor/nodecontroller.git
cd nodecontroller
```

Also, if you are not using the Waggle image, you may have to install the dependencies of the nodecontroller. This script uses apt-get commands. For other Linux distributions look into this file to see what needs to be installed.
```bash
scripts/install_dependencies.sh
```

### Installation with Docker (only x86)

A docker image is available for testing and developing purposes. Currently this is x86, thus it will not run on the ODROID which has an ARM architecture. We will provide ARM Docker images soon I hope.

```bash
docker rm -f nc
docker pull waggle/nodecontroller
docker run -ti --name nc --rm waggle/nodecontroller
cd /usr/lib/waggle/nodecontroller/
RABBITMQ_HOST=<IP> ./configure
```

For developing purposes mounting the git repo from the host can be helpful:
```bash
mkdir -p cd ${HOME}/git/
cd ${HOME}/git/
git clone --recursive git@github.com:waggle-sensor/nodecontroller.git
docker run -ti --name nc --rm -v ${HOME}/git/nodecontroller/:/usr/lib/waggle/nodecontroller  waggle/nodecontroller
```

## Configuration

You can use the environment variable RABBITMQ_HOST to tell the node controller where to send the sensor data. Run the configure script.

```bash
RABBITMQ_HOST=<IP> ./configure
```

### SSL certificates

The nodecontroller needs SSL certificates to be able to talk to the RabbitMQ component of the beehive server. 
```text
Private key of the node:                   /usr/lib/waggle/SSL/node/key.pem
Public certificate of the node:            /usr/lib/waggle/SSL/node/cert.pem
Public certificate of the RabbitMQ server: /usr/lib/waggle/SSL/waggleca/cacert.pem
```

The certificate files have to be created by the certificate authority on the beehive server. In principle there are two ways for the nodecontroller to get theses files. 

1. Manual: The beehive administrator creates keys for you and you have to copy them onto your node, e.g. using ssh.
2. Automatic: In some circumstances it can be an option to use a certificate server. If the certificate server is running, the nodecontroller software can automatically download the required files. Note that for security reasons this option might be available only in internal networks or with other special restrictions to avoid abuse. 



## Services

For an overview of all waggle services run the script nodecontroller.
```bash
nodecontroller
```

Individual services can be controlled like this.
```bash
/etc/init.d/data_cache.sh start
/etc/init.d/communications.sh start
```

## Simple CPU temperature sensor

This script can be used to test sending of sensor data. Note that this script sends data to the data cache. It does not check if data actually arrives at the server.

```bash
cd /usr/lib/waggle/nodecontroller/nc-wag-os/waggled/NC
./node_sensor.py 
```



## Developer Notes

Everything that is installed on the Node Controller lives here.  There
are three basic pieces: 

* the baseOS (a Linux distro) for the ODROID
   (we are curently using a ODROID stock ubuntu image, not in this repo)

* the waggle-customized OS that includes all basic management
  features and cloud communication layers

* the in-situ processing components for processing audio, images,
  hyperspectral data, etc.


