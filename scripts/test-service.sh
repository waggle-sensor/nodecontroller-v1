#!/bin/bash

# Determine root and alternate boot medium root device paths
. /usr/lib/waggle/core/scripts/detect_disk_devices.sh

wait_for_gn_reboot() {
  local rebooting=0
  while [ $rebooting -eq 0 ]; do
    last_hb=$(wagman-client hb | sed -n '2p')
    if [ $last_hb -gt 10000 ]; then
      rebooting=1
    fi
  done

  while [[ $rebooting -eq 1 ]]; do
    last_hb=$(wagman-client hb | sed -n '2p')
    if [ $last_hb -lt 10000 ]; then
      # reboot succeeded
      rebooting=0
    elif [ $last_hb -gt 70000 ]; then
      # reboot failed
      return 1
    fi
  done
}

run_gn_tests() {
  # Run tests on the SD or eMMC
  ssh -i /usr/lib/waggle/SSL/guest/id_rsa_waggle_aot_guest_node waggle@10.31.81.10 \
    -o "StrictHostKeyChecking no" -o "PasswordAuthentication no" -o "ConnectTimeout 2" \
    /usr/lib/waggle/guestnode/scripts/run_tests.sh

  # FIXME: reboot is happening too fast

  # Reboot to the alternate disk medium to continue the test cycle
  local current_gn_device_type=$(wagman-client bs 1)
  local other_gn_device_type=''
  if [ "${current_gn_device_type}" == "sd" ]; then
    other_gn_device_type='emmc'
  fi
  wagman-client bs 1 $other_gn_device_type
  wagman-client stop 1 0
  wait_for_gn_reboot

  # Run tests on the eMMC or SD
  ssh -i /usr/lib/waggle/SSL/guest/id_rsa_waggle_aot_guest_node waggle@10.31.81.10 \
    -o "StrictHostKeyChecking no" -o "PasswordAuthentication no" -o "ConnectTimeout 2" \
    /usr/lib/waggle/guestnode/scripts/run_tests.sh

  # Reboot to SD if we started the GN test cycle on the eMMC
  if [ "$current_gn_device_type" == "sd" ]; then
		wagman-client bs 1 $current_gn_device_type
		wagman-client stop 1 0
    wait_for_gn_reboot
	fi
}

run_tests() {
  if [ "${CURRENT_DISK_DEVICE_TYPE}" == "SD" ]; then
    run_gn_tests
  fi
  /usr/lib/waggle/nodecontroller/scripts/test_node.sh \
    > /home/waggle/test_node_NC_${CURRENT_DISK_DEVICE_TYPE}.log
}

generate_report() {
  # Retrieve the eMMC test log
  cp /media/test/home/waggle/test_node_NC_${OTHER_DISK_DEVICE_TYPE}.log /home/waggle/

  local report_file="/home/waggle/test-report.txt"
  echo "Node Controller SD Test Results" >> $report_file
  echo "-------------------------------" >> $report_file
  cat /home/waggle/test_node_NC_SD.log >> $report_file

  echo >> $report_file
  echo "Node Controller eMMC Test Results" >> $report_file
  echo "---------------------------------" >> $report_file
  cat /home/waggle/test_node_NC_MMC.log >> $report_file

  # wait a reasonable amount of time for the GN to finish its tests
  local tries=0
  local max_tries=6
  local gn_done=0
  while [ $tries -lt $max_tries ]; do
    if [[ ! -e /home/waggle/test_node_XU3_SD.log || ! -e /home/waggle/test_node_XU3_MMC.log ]]; then
      tries=$(expr $tries + 1)
      echo "Waiting for GN test logs..."
      sleep 10
    else
      gn_done=1
      tries=$max_tries
    fi
  done

  if [ $gn_done -eq 1 ]; then
    echo >> $report_file
    echo "Guest Node SD Test Results" >> $report_file
    echo "--------------------------" >> $report_file
    cat /home/waggle/test_node_GN_SD.log >> $report_file

    echo >> $report_file
    echo "Guest Node eMMC Test Results" >> $report_file
    echo "----------------------------" >> $report_file
    cat /home/waggle/test_node_GN_MMC.log >> $report_file
  else
    echo >> $report_file
    echo "########################" >> $report_file
    echo "Guest Node Tests Failed!" >> $report_file
    echo "########################" >> $report_file
  fi
}

mount | grep '/media/test' && true
if [ $? -eq 1 ]; then
  mount "${OTHER_DISK_DEVICE}p2" /media/test
fi

start_file=/home/waggle/start_test
continue_file=/home/waggle/continue_test
finish_file=/home/waggle/finish_test
if [ -e ${start_file} ] ; then
  run_tests
  if [ "${CURRENT_DISK_DEVICE_TYPE}" == "SD" ]; then
    wagman-client bs 0 emmc
  else
    wagman-client bs 0 sd
  fi
  touch /media/test${continue_file}
  rm ${start_file}
  #wagman-client stop 0 0
elif [ -e ${continue_file} ]; then
  run_tests
  if [ "${CURRENT_DISK_DEVICE_TYPE}" == "MMC" ]; then
    touch /media/test${finish_file}
  elif [ "${CURRENT_DISK_DEVICE_TYPE}" == "SD" ]; then
    generate_report
  fi
  rm ${continue_file}
  wagman-client bs 0 sd
  #wagman-client stop 0 0
elif [ -e ${finish_file} ]; then
  generate_report
  rm ${finish_file}
fi
