#!/bin/bash

# this script is specifically for (auto-)building images on the odroid.

set -e
set -x

export URL="http://odroid.in/ubuntu_14.04lts/"
export IMAGE="ubuntu-14.04.3lts-lubuntu-odroid-c1-20151020.img"

# this is the device where we will build the waggle image
export CURRENT_DEVICE=$(df --output=source / | grep "^/") ; echo "CURRENT_DEVICE: ${CURRENT_DEVICE}" 
if [ ${CURRENT_DEVICE} == "/dev/mmcblk1p2" ] ; then 
  export DEVICE_NAME="mmcblk0" 
else 
  export DEVICE_NAME="mmcblk1"
fi
echo "DEVICE_NAME: ${DEVICE_NAME}"

#get curl
if ! $(hash curl 2>/dev/null) ; then
  apt-get update
  apt-get install -y curl
fi

# get git
if ! $(hash git 2>/dev/null) ; then
  apt-get update
  apt-get install -y git
fi


#OTHER_UUID=$(blkid /dev/${DEVICE_NAME}p2 -s UUID | grep -o "[0-9a-zA-Z-]\{36\}")

if [ ! -e ${IMAGE}.xz ] ; then
  wget ${URL}${IMAGE}.xz
  wget ${URL}${IMAGE}.xz.md5sum
  #sleep 1
  # too large for my 8GB-eMMC: 
  #unxz ${IMAGE}.xz
  #TODO md5sum check
fi

set +e
if [ $(df -h | grep -c /dev/${DEVICE_NAME}p1 ) == 1 ] ; then 
  while ! $(umount /dev/${DEVICE_NAME}p1) ; do sleep 3 ; done
fi
if [ $(df -h | grep -c /dev/${DEVICE_NAME}p2 ) == 1 ] ; then 
  while ! $(umount /dev/${DEVICE_NAME}p2) ; do sleep 3 ; done
fi
set -e

sleep 1
# dd if=${IMAGE} of=/dev/${DEVICE_NAME} bs=1M conv=fsync
# image too large, this is why we unxz on the fly: (takes about 8 minutes)
cat ${IMAGE}.xz | unxz - | dd of=/dev/${DEVICE_NAME} bs=1M conv=fsync
sleep 1 
sync
sleep 1


# now we need to insert the init script, such that on next boot the waggle image can be created:
export WAGGLEROOT=/media/waggleroot
mkdir -p ${WAGGLEROOT}
#partprobe /dev/${DEVICE_NAME}
sleep 2
mount /dev/${DEVICE_NAME}p2 ${WAGGLEROOT}

# download nodecontroller repo
mkdir -p ${WAGGLEROOT}/usr/lib/waggle
rm -rf ${WAGGLEROOT}/usr/lib/waggle/nodecontroller

git clone --recursive https://github.com/waggle-sensor/nodecontroller.git ${WAGGLEROOT}/usr/lib/waggle/nodecontroller

# uce rc.local to start autobuild on next boot
rm -f ${WAGGLEROOT}/etc/rc.local
#dangling symlink
ln -s /usr/lib/waggle/nodecontroller/scripts/rc.local ${WAGGLEROOT}/etc/rc.local

#umount
if [ $(df -h | grep -c /dev/${DEVICE_NAME}p2 ) == 1 ] ; then 
  while ! $(umount /dev/${DEVICE_NAME}p2) ; do sleep 3 ; done
fi

mkdir -p /media/waggleboot
sleep 2
mount /dev/${DEVICE_NAME}p1 /media/waggleboot

#change resolution:
sed -i.bak -e "s/^setenv m /# setenv m /" -e "s/# setenv m \"1440x900p60hz\"/setenv m \"1440x900p60hz\"/" /media/waggleboot/boot.ini

if [ $(df -h | grep -c /dev/${DEVICE_NAME}p1 ) == 1 ] ; then 
  while ! $(umount /dev/${DEVICE_NAME}p1) ; do sleep 3 ; done
fi

if [ $(blkid /dev/mmcblk0p2 /dev/mmcblk1p2 | grep -o "UUID=\"[^ ]*\"" | sort -u | wc -l) == 1 ] ; then 
  echo "Error: Both partitions (/dev/mmcblk0p2 /dev/mmcblk1p2) have the same UUID. That will not work."  
  exit 1
fi

set +x
echo "Restart now with jumper 1 closed. Be sure to take the power away completly, a simple reboot is not enough. 30 seconds after new start you can open the jumper again."
echo "e.g.: shutdown -h now"
