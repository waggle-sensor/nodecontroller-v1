

## Setting up the node controller

You can use the environment variable BEEHIVE_HOST to tell the node controller where to send the sensor data.

```bash
git clone --recursive https://github.com/waggle-sensor/nodecontroller.git
cd nodecontroller
BEEHIVE_HOST=<IP> ./configure
```

## Docker (only x86)

A docker image is available for testing and developing purposes. Currently this is x86, thus it will not run on the ODROID, you can only execute it on Linux. We will provide ARM Docker images soon I guess.

```bash
docker run -ti --name nc --rm waggle/nodecontroller
cd /usr/lib/waggle/nodecontroller/
BEEHIVE_HOST=<IP> ./configure
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


