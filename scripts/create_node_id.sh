#!/bin/bash

set -e
set -x


export ODROIDMODEL=`head -n 1 /media/boot/boot.ini | cut -d '-' -f 1`

if [ $(echo $ODROIDMODEL | grep -c "^ODROID") -eq 0 ] ; then
  echo "error: could not detect ODROID model"
  return 2
fi

### Node ID
export NODE_ID=""

# try MAC address (some older models do not have unique MAC addresses)
if [ $(echo $ODROIDMODEL | grep -c "^ODROIDC") -eq 1 ] ; then
  # try to detect network device, e.g. "eth0"
  export NETWORK_DEVICE=$(ifconfig -a | grep "Ethernet" | grep "^eth" | sort | head -n 1 | grep -o "^eth[0-9]" | tr -d '\n')
  export MACADDRESS=`ifconfig ${NETWORK_DEVICE} | head -n 1 | grep -o "[[:xdigit:]:]\{17\}" | sed 's/://g'`
  if [ ! ${#MACADDRESS} -ge 12 ]; then
    echo "warning: could not extract MAC address"
  else
    NODE_ID="waggle_mac_${MACADDRESS}"  
  fi
fi

# try memory card serial number
export CID_FILE="/sys/block/mmcblk0/device/cid"
if [ "${NODE_ID}x" == "x" ] && [ -e ${CID_FILE} ]; then
  # use serial number from SD-card
  # some devices do not have a unique MAC address, they could use this code
 
  export SERIAL_ID=`python -c "cid = '$(cat ${CID_FILE})' ; len=len(cid) ; mid=cid[:2] ; psn=cid[-14:-6] ; print mid+'_'+psn"`
  if [ ! ${#SERIAL_ID} -ge 11 ]; then
    echo "warning: could not create unique identifier from SD-card serial number"
  else
    NODE_ID="waggle_serial_${SERIAL_ID}" 
  fi
fi

# try random number
if [ "${NODE_ID}x" = "x" ] ; then
  NODE_ID="waggle_random_${RANDOM}"
fi

#save node ID
mkdir -p /etc/waggle/
echo ${NODE_ID} > /etc/waggle/node_id
echo ${NODE_ID} > /etc/hostname