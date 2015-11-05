#!/bin/bash
set -x
IMAGE="waggle-odroid-c1-20151105.img"
USB_NAME="Transcend"
SD_DISK=""

### Use 


if [ ! -e ${IMAGE} ] ; then
  echo "Error: Image file ${IMAGE} not found"
  exit 1
fi

unamestr=`uname`
if [[ "$unamestr" == 'Darwin' ]]; then


  while [ 1 ] ; do
    SD_DISK=$(system_profiler SPUSBDataType | grep -A 20  "${USB_NAME}"  | grep "BSD Name" | cut -d ':' -f 2 | tr -d ' ')
    if [ "${SD_DISK}_" != "_" ] ; then
  
      sleep 2
      export DEVICE_NAME=${SD_DISK}
      diskutil unmountDisk /dev/${DEVICE_NAME}
      sleep 2
      dd if=${IMAGE} of=/dev/r${DEVICE_NAME} bs=1m
      sleep 2
      sync
      diskutil eject /dev/r${DEVICE_NAME}

    fi
      echo "waiting for memory device..."
      sleep 2

  done

else
  echo "TODO"
fi
