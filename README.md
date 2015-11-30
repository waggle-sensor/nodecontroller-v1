

## Setting up the node controller

You can use the environment variable RABBITMQ_HOST to tell the node controller where to send the sensor data.

```bash
git clone --recursive https://github.com/waggle-sensor/nodecontroller.git
cd nodecontroller
RABBITMQ_HOST=<IP> ./configure
```

### node controller services

```bash
/etc/init.d/data_cache.sh start
/etc/init.d/communications.sh start
```

### Simple CPU temperature sensor

This script can be used to test sending of sensor data. Note that this script sends data to the data cache. It does not check if data actually arrives at the server.

```bash
cd /usr/lib/waggle/nodecontroller/nc-wag-os/waggled/NC
./node_sensor.py 
```

## Docker (only x86)

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

## Developer Notes

Everything that is installed on the Node Controller lives here.  There
are three basic pieces: 

* the baseOS (a Linux distro) for the ODROID
   (we are curently using a ODROID stock ubuntu image, not in this repo)

* the waggle-customized OS that includes all basic management
  features and cloud communication layers

* the in-situ processing components for processing audio, images,
  hyperspectral data, etc.


