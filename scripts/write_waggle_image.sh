#!/bin/bash
set -x
IMAGE="waggle-odroid-c1-20151105.img"
USB_NAME="Transcend"
DEVICE_NAME=""

### Use this script at your own risk ###


# OSX: brew install pv


if [ ! -e ${IMAGE} ] ; then
  echo "Error: Image file ${IMAGE} not found"
  exit 1
fi

unamestr=`uname`
if [[ "$unamestr" == 'Darwin' ]]; then


  while [ 1 ] ; do
    set +x
    echo "waiting for memory device..."
    while [ "${DEVICE_NAME}_" == "_" ] ; do
      sleep 2
      DEVICE_NAME=$(system_profiler SPUSBDataType | grep -A 20  "${USB_NAME}"  | grep -m 1 "BSD Name" | cut -d ':' -f 2 | tr -d ' ' | tr -d '\n')

      if [ "${DEVICE_NAME}_" != "_" ] ;then
        if [ ! -e ${DEVICE_NAME} ] ; then
          DEVICE_NAME=""
        fi
      fi
    done

    if [ "${DEVICE_NAME}_" != "_" ] && [ -e /dev/r${DEVICE_NAME} ] ; then
      echo "found device: ${SD_DISK}"
      sleep 2
      
      set -x
      if [ $(diskutil list | grep -c "^/dev/${DEVICE_NAME}") -eq 1 ] ; then      
        diskutil unmountDisk /dev/${DEVICE_NAME}
        sleep 2
      fi
      #dd if=${IMAGE} of=/dev/r${DEVICE_NAME} bs=1m
      pv -per --width 80 -f ${IMAGE} | dd of=/dev/r${DEVICE_NAME} bs=1m
      sleep 2
      sync
      diskutil eject /dev/r${DEVICE_NAME}
      set +x
    fi
    sleep 2  

  done

else
  echo "TODO"
fi
