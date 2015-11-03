#!/bin/bash

# this script is specifically for (auto-)building images on the odroid.

set -e
set -x

export URL="http://odroid.in/ubuntu_14.04lts/"
export IMAGE="ubuntu-14.04.3lts-lubuntu-odroid-c1-20151020.img"

export DIR="/root"

if [ $# -eq 0 ] ; then
  echo "usage: $0 <device>"
  exit 1
fi


export OTHER_DEVICE=$1





# this is the device where we will build the waggle image
export CURRENT_DEVICE=$(df --output=source / | grep "^/") ; echo "CURRENT_DEVICE: ${CURRENT_DEVICE}" 

CURRENT_DEVICE=`basename ${CURRENT_DEVICE}`

#if [ ${CURRENT_DEVICE} == "/dev/mmcblk1p2" ] ; then
#  export OTHER_DEVICE="mmcblk0"
#else
#  export OTHER_DEVICE="mmcblk1"
#fi

if [ ! $(lsblk -o KNAME,TYPE ${OTHER_DEVICE} | grep -c disk) -eq 1 ] ; then
  echo "device $1 not found."
  exit 1
fi

export OTHER_DEVICE=`basename ${OTHER_DEVICE}`

echo "OTHER_DEVICE: /dev/${OTHER_DEVICE}"


function dev_suffix {

  if [[ $1 =~ ^"/dev/sd" ]] ; then
    echo ""
    return 0
  fi
  if [[ $1 =~ ^"/dev/mmcblk" ]] ; then
    echo "p"
    return 0
  fi
  if [[ $1 =~ ^"/dev/disk" ]] ; then
	echo "s"
	return 0
  fi

  echo "unknown"
  return 1
}


export OTHER_DEV_SUFFIX=`dev_suffix "/dev/${OTHER_DEVICE}"`
if [ "${OTHER_DEV_SUFFIX}_" == "unknown_" ] ; then
  exit 1
fi

export CURRENT_DEV_SUFFIX=`dev_suffix "/dev/${CURRENT_DEVICE}"`
if [ "${CURRENT_DEV_SUFFIX}_" == "unknown_" ] ; then
  exit 1
fi


echo "CURRENT_DEV_SUFFIX: ${CURRENT_DEV_SUFFIX}"
echo "OTHER_DEV_SUFFIX: ${OTHER_DEV_SUFFIX}"




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


#OTHER_UUID=$(blkid /dev/${OTHER_DEVICE}p2 -s UUID | grep -o "[0-9a-zA-Z-]\{36\}")

if [ ! -e ${DIR}/${IMAGE}.xz ] ; then
  wget -O ${DIR}/${IMAGE}.xz ${URL}${IMAGE}.xz
  rm -f ${DIR}/${IMAGE}.xz.md5sum
  wget -O ${DIR}/${IMAGE}.xz.md5sum ${URL}${IMAGE}.xz.md5sum
  #sleep 1
  # too large for my 8GB-eMMC: 
  #unxz ${IMAGE}.xz
  #TODO md5sum check
fi

set +e
if [ $(df -h | grep -c /dev/${OTHER_DEVICE}${OTHER_DEV_SUFFIX}1 ) == 1 ] ; then
  while ! $(umount /dev/${OTHER_DEVICE}${OTHER_DEV_SUFFIX}1) ; do sleep 3 ; done
fi
if [ $(df -h | grep -c /dev/${OTHER_DEVICE}${OTHER_DEV_SUFFIX}2 ) == 1 ] ; then
  while ! $(umount /dev/${OTHER_DEVICE}${OTHER_DEV_SUFFIX}2) ; do sleep 3 ; done
fi
set -e

sleep 1
# dd if=${IMAGE} of=/dev/${OTHER_DEVICE} bs=1M conv=fsync
# image too large, this is why we unxz on the fly: (takes about 8 minutes)
cat ${DIR}/${IMAGE}.xz | unxz - | dd of=/dev/${OTHER_DEVICE} bs=1M conv=fsync
sleep 1 
sync
sleep 1


# now we need to insert the init script, such that on next boot the waggle image can be created:
export WAGGLEROOT=/media/waggleroot
mkdir -p ${WAGGLEROOT}
#partprobe /dev/${OTHER_DEVICE}
sleep 2
mount /dev/${OTHER_DEVICE}${OTHER_DEV_SUFFIX}2 ${WAGGLEROOT}

# download nodecontroller repo
mkdir -p ${WAGGLEROOT}/usr/lib/waggle
rm -rf ${WAGGLEROOT}/usr/lib/waggle/nodecontroller

git clone --recursive https://github.com/waggle-sensor/nodecontroller.git ${WAGGLEROOT}/usr/lib/waggle/nodecontroller

# uce rc.local to start autobuild on next boot
rm -f ${WAGGLEROOT}/etc/rc.local
#dangling symlink
ln -s /usr/lib/waggle/nodecontroller/scripts/rc.local ${WAGGLEROOT}/etc/rc.local

#umount
if [ $(df -h | grep -c /dev/${OTHER_DEVICE}${OTHER_DEV_SUFFIX}2 ) == 1 ] ; then
  while ! $(umount /dev/${OTHER_DEVICE}${OTHER_DEV_SUFFIX}2) ; do sleep 3 ; done
fi

mkdir -p /media/waggleboot
sleep 2
mount /dev/${OTHER_DEVICE}${OTHER_DEV_SUFFIX}1 /media/waggleboot

#change resolution:
sed -i.bak -e "s/^setenv m /# setenv m /" -e "s/# setenv m \"1440x900p60hz\"/setenv m \"1440x900p60hz\"/" /media/waggleboot/boot.ini

if [ $(df -h | grep -c /dev/${OTHER_DEVICE}${OTHER_DEV_SUFFIX}1 ) == 1 ] ; then
  while ! $(umount /dev/${OTHER_DEVICE}${OTHER_DEV_SUFFIX}1) ; do sleep 3 ; done
fi

if [ $(blkid /dev/${OTHER_DEVICE}${OTHER_DEV_SUFFIX}2 /dev/${CURRENT_DEVICE}${CURRENT_DEV_SUFFIX}2 | grep -o "UUID=\"[^ ]*\"" | sort -u | wc -l) == 1 ] ; then
  echo "Error: Both partitions (/dev/${OTHER_DEVICE}${OTHER_DEV_SUFFIX}2 /dev/${CURRENT_DEVICE}${CURRENT_DEV_SUFFIX}2) have the same UUID. That will not work."
  exit 1
fi

set +x
echo "Restart now with jumper 1 closed. Be sure to take the power away completly, a simple reboot is not enough. 30 seconds after new start you can open the jumper again."
echo "e.g.: shutdown -h now"
