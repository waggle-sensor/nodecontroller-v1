<!--
waggle_topic=/node_controller/introduction
-->

# Node Controller Overview

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
git clone https://github.com/waggle-sensor/nodecontroller.git
cd nodecontroller
```

### Installation with Docker (only x86)

A docker image is available for testing and developing purposes. Currently this is x86, thus it will not run on the ODROID which has an ARM architecture. We will provide ARM Docker images hopefully soon.

```bash
docker rm -f nc
docker pull waggle/nodecontroller
docker run -ti --name nc --rm waggle/nodecontroller
cd /usr/lib/waggle/nodecontroller/
```

For developing purposes mounting the git repo from the host can be helpful:
```bash
mkdir -p cd ${HOME}/git/
cd ${HOME}/git/
git clone --recursive git@github.com:waggle-sensor/nodecontroller.git
docker run -ti --name nc --rm -v ${HOME}/git/nodecontroller/:/usr/lib/waggle/nodecontroller  waggle/nodecontroller
```

## Configuration

To tell the node controller where to send the sensor data. Run the configure script with the -s option (--server=... also works) :

```bash
cd /usr/lib/waggle/nodecontroller/
./configure -s <HOSTNAME>
```

This can also be achieved by setting the environment variable BEEHIVE_HOST:

```bash
cd /usr/lib/waggle/nodecontroller/
export BEEHIVE_HOST=<HOSTNAME>
./configure
```

Inside of a Docker container communication with the guest node may require overwriting NCIP. Access to ports 9090 and 9091 is restricted by only exposing them instead of publishing them.
```bash
echo "0.0.0.0" > /etc/waggle/NCIP
```

### SSL certificates

The nodecontroller needs SSL certificates to be able to talk to the RabbitMQ component of the beehive server. Those files are not installed on the Waggle image.

SSL related files expected by the nodecontroller:
```text
Private key of the node:                   /etc/waggle/key.pem
Public certificate of the node:            /etc/waggle/cert.pem
Public certificate of the RabbitMQ server: /etc/waggle/cacert.pem
```

The certificate files have to be created by the certificate authority on the beehive server. In principle there are two ways for the nodecontroller to get theses files.

1. Manual: The beehive administrator creates keys for the node and the node user has to copy them onto the node, e.g. using ssh.
2. Automatic: In some circumstances it can be an option to use a certificate server. If the certificate server is running, the nodecontroller software can automatically download the required files. Note that for security reasons this option might be available only in internal networks or with other special restrictions to avoid abuse.



## Services

At the moment Waggle services are started by systemd. The configure script should set everything up so that the Waggle services will be started automatically.

Status of waggle services:
```bash
systemctl list-units 'waggle*'
```

The result will look somethinglike this:
```text
UNIT                                LOAD   ACTIVE SUB     DESCRIPTION
waggle-epoch.service                loaded active running Maintains the date and time on the node.
waggle-heartbeat.service            loaded active running Triggers Wagman heartbeat line.
waggle-monitor-connectivity.service loaded active running Monitors node controller connectivity status.
waggle-monitor-shutdown.service     loaded active running Monitors shutdown signals.
waggle-monitor-system.service       loaded active running Monitors node controller status.
waggle-monitor-wagman.service       loaded active running Monitors Wagman status.
waggle-plugin-alphasense.service    loaded active running Alphasense OPC-N2 plugin.
waggle-plugin-coresense.service     loaded active running Coresense 3.1 plugin.
waggle-plugin-gps.service           loaded active running GPS plugin.
waggle-reverse-tunnel.service       loaded active running Maintains an SSH reverse tunnel on Beehive.
waggle-wagman-driver.service        loaded active running Wagman Driver
waggle-wwan.service                 loaded active running ATT WWAN Client
waggle-core.target                  loaded active active  Waggle Core
waggle-platform.target              loaded active active  Waggle Platform
```
