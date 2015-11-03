#!/bin/bash

# this script is specifically for (auto-)building images on the odroid.
# it copies a new waggle partition into a .img-file.

if [ $# -eq 0 ] ; then
  echo "usage: $0 <device>"
  echo ""
  echo "list of available devices:"
  blkid
  exit 1
fi

export DIR="/root"

set -e
set -x

export OTHER_DEVICE=$1

if [ ! $(lsblk -o KNAME,TYPE ${OTHER_DEVICE} | grep -c disk) -eq 1 ] ; then
  echo "device $1 not found."
  exit 1
fi


OTHER_DEVICE=`basename ${OTHER_DEVICE}`
echo "OTHER_DEVICE: /dev/${OTHER_DEVICE}"


# probably not needed anyway....
export CURRENT_DEVICE=$(df --output=source / | grep "^/") ; echo "CURRENT_DEVICE: ${CURRENT_DEVICE}"
CURRENT_DEVICE=`basename ${CURRENT_DEVICE}`


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



# unmount in case it is already mounted (it might be already mounted, but with another mount point)
if [ $(df -h | grep -c /dev/${OTHER_DEVICE}${OTHER_DEV_SUFFIX}2 ) == 1 ] ; then
  while ! $(umount /dev/${OTHER_DEVICE}${OTHER_DEV_SUFFIX}2) ; do sleep 3 ; done
fi

export DATE=`date +"%Y%m%d"` ; echo "DATE: ${DATE}"
export NEW_IMAGE="${DIR}/waggle-odroid-c1-${DATE}.img" ; echo "NEW_IMAGE: ${NEW_IMAGE}"

# extract the report.txt from the new waggle image
export WAGGLE_ROOT="/media/waggle/"
mkdir -p ${WAGGLE_ROOT}
mount /dev/${OTHER_DEVICE}${OTHER_DEV_SUFFIX}2 ${WAGGLE_ROOT}
cp ${WAGGLE_ROOT}/root/report.txt ${NEW_IMAGE}.report.txt
cp ${WAGGLE_ROOT}/root/rc.local.log ${NEW_IMAGE}.rc.local.log

# put original rc.local in place again
rm -f ${WAGGLE_ROOT}/etc/rc.local
cat <<EOF > ${WAGGLE_ROOT}/etc/rc.local
#!/bin/sh -e
#
# rc.local
#
# This script is executed at the end of each multiuser runlevel.
# Make sure that the script will "exit 0" on success or any other
# value on error.
#
# In order to enable or disable this script just change the execution
# bits.
#
# By default this script does nothing.

[ ! -f /etc/ssh/ssh_host_dsa_key ]; dpkg-reconfigure openssh-server

exit 0
EOF


#TODO: delete some intermediate files ine the new waggle image.


#get size
export FILESYSTEM_SIZE_KB=`df -BK --output=used /dev/${OTHER_DEVICE}${OTHER_DEV_SUFFIX}2 | grep -o "[0-9]\+"` ; echo "FILESYSTEM_SIZE_KB: ${FILESYSTEM_SIZE_KB}"

# add 300MB
export NEW_PARTITION_SIZE_KB=$(echo "${FILESYSTEM_SIZE_KB} + (1024)*300" | bc) ; echo "NEW_PARTITION_SIZE_KB: ${NEW_PARTITION_SIZE_KB}"

if [ $(df -h | grep -c /dev/${OTHER_DEVICE}${OTHER_DEV_SUFFIX}2 ) == 1 ] ; then
  while ! $(umount /dev/${OTHER_DEVICE}${OTHER_DEV_SUFFIX}2) ; do sleep 3 ; done
fi


# just for information: dumpe2fs -h ${OTHER_DEVICE}${OTHER_DEV_SUFFIX}2

# verify partition:
e2fsck -f -y /dev/${OTHER_DEVICE}${OTHER_DEV_SUFFIX}2

# shrink filesystem (that does not shrink the partition!)
resize2fs /dev/${OTHER_DEVICE}${OTHER_DEV_SUFFIX}2 ${NEW_PARTITION_SIZE_KB}K

# detect start position of second partition
export START=$(fdisk -l /dev/${OTHER_DEVICE} | grep "/dev/${OTHER_DEVICE}${OTHER_DEV_SUFFIX}2" | awk '{print $2}') ; echo "partition START: ${START}"

export SECTOR_SIZE=`fdisk -l /dev/${OTHER_DEVICE} | grep "Sector size" | grep -o ": [0-9]*" | grep -o "[0-9]*"` ; echo "SECTOR_SIZE: ${SECTOR_SIZE}"

export FRONT_SIZE_KB=`echo "${SECTOR_SIZE} * ${START} / 1024" | bc` ; echo "FRONT_SIZE_KB: ${FRONT_SIZE_KB}"

partprobe  /dev/${OTHER_DEVICE}

sleep 3

### fdisk (shrink partition)
# fdisk: (d)elete partition 2 ; (c)reate new partiton 2 ; specify start posirion and size of new partiton
set +e
echo -e "d\n2\nn\np\n2\n${START}\n+${NEW_PARTITION_SIZE_KB}K\nw\n" | fdisk /dev/${OTHER_DEVICE}
set -e


partprobe  /dev/${OTHER_DEVICE}

set +e
resize2fs /dev/${OTHER_DEVICE}${OTHER_DEV_SUFFIX}2
set -e

# does not show the new size
fdisk -l /dev/${OTHER_DEVICE}

# shows the new size (-b for bytes)
partx --show /dev/${OTHER_DEVICE}${OTHER_DEV_SUFFIX}2


e2fsck -f /dev/${OTHER_DEVICE}${OTHER_DEV_SUFFIX}2

# add size of boot partition
COMBINED_SIZE_KB=`echo "${NEW_PARTITION_SIZE_KB} + ${FRONT_SIZE_KB}" | bc` ; echo "COMBINED_SIZE_KB: ${COMBINED_SIZE_KB}"

#export BLOCK_SIZE=`blockdev --getbsz /dev/${OTHER_DEVICE}`


# from kb to mb
export BLOCKS_TO_WRITE=`echo "${COMBINED_SIZE_KB}/1024" | bc` ; echo "BLOCKS_TO_WRITE: ${BLOCKS_TO_WRITE}"





dd if=/dev/${OTHER_DEVICE} bs=1M count=${BLOCKS_TO_WRITE} | xz -1 --stdout - > ${NEW_IMAGE}.xz
# xz -1 creates a 560MB file in 18.5 minutes


if [ -e ./waggle-id_rsa ] ; then
  md5sum ${NEW_IMAGE}.xz > ${NEW_IMAGE}.xz.md5sum 
  scp -o "StrictHostKeyChecking no" -v -i ./waggle-id_rsa ${NEW_IMAGE}.xz ${NEW_IMAGE}.xz.md5sum waggle@terra.mcs.anl.gov:/mcs/www.mcs.anl.gov/research/projects/waggle/downloads
  
  if [ -e ${NEW_IMAGE}.report.txt ] ; then 
    scp -o "StrictHostKeyChecking no" -v -i ./waggle-id_rsa ${NEW_IMAGE}.report.txt waggle@terra.mcs.anl.gov:/mcs/www.mcs.anl.gov/research/projects/waggle/downloads
  fi
fi



###################################################

# Variant A: create archive on ODROID and push final result to remote location
# or
# Variant B: Pull disk dump from ODROID and create image archive on PC 
 


###  Variant A  ###
# on ONDROID
#  create diskdump 
#dd if=/dev/${OTHER_DEVICE} of=./newimage.img bs=1M count=${BLOCKS_TO_WRITE}

# compress (xz --keep option to save space)
#xz newimage.img
#md5sum newimage.img.xz > newimage.img.xz.md5sum
#scp report.txt newimage.img.xz newimage.img.xz.md5sum <to_somewhere>

###  Variant A2  ###


###  Variant B  ###
# on your computer
#scp root@<odroid_ip>:/root/report.txt .
#ssh root@<odroid_ip> "dd if=/dev/${OTHER_DEVICE} bs=1M count=${BLOCKS_TO_WRITE}" | dd of="newimage.img" bs=1m
#xz --keep newimage.img
# Linux:
#md5sum newimage.img.xz > newimage.img.xz.md5sum
# OSX:
#md5 -r newimage.img.xz > newimage.img.xz.md5sum
