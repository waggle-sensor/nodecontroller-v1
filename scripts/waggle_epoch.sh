#!/bin/bash


try_set_time()
{
  local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  local wagman_date=0
  unset date

  # get epoch from server
  local exit_code
  echo "Getting the epoch from Beehive..."
  local server_hostname_file="/etc/waggle/server_host"
  while [ ! -e $server_hostname_file ]; do
    echo "The Beehive hostname has not been set. Retrying in 1 hour..."
    sleep 1h
  done
  local server_host=`cat $server_hostname_file`
  local curl_out=$(curl -s --max-time 10 --connect-timeout 10 http://${server_host}/api/1/epoch)
  exit_code=$?
  if [ ${exit_code} -eq 0 ] ; then
    date_json=$(echo $curl_out | tr '\n' ' ')
    date=$(python -c "import json; print(json.loads('${date_json}')['epoch'])") || unset date
    echo "Got date '${date} from Beehive."
  else
    echo "Warning: could not get the epoch from Beehive."
    unset date
  fi

  # if date is not empty, set date
  if [ ! "${date}x" == "x" ] ; then
    echo "Setting the date/time update interval to 24 hours..."
    CHECK_INTERVAL='24h'
    echo "Setting the system epoch to ${date}..."
    date -s@${date}
    exit_code=$?
    if [ ${exit_code} -ne 0 ] ; then
      echo "Error: failed to set the Node Controller system date/time."
       return ${exit_code}
    fi

    # Update the WagMan date
    echo "Setting the Wagman date/time..."
    wagman-client date $(date +"%Y %m %d %H %M %S") || true


    # Update the Edge Processor date
    echo "Setting the Edge Processor date/time..."
    ${script_dir}/eplogin /usr/lib/waggle/edge_processor/scripts/sync_date.sh ${date}
    exit_code=$?
    if [ ${exit_code} -ne 0 ] ; then
      echo "Error: failed to set the Edge Processor system date/time."
       return ${exit_code}
    fi
  else
    echo "Setting the date/time update interval to 10 seconds..."
    CHECK_INTERVAL='10'  # seconds
    wagman_date=$(wagman-client epoch) || wagman_date=0
    echo "Wagman epoch: ${wagman_date}"
    system_date=$(date +%s)
    echo "System epoch: ${system_date}"
    wagman_build_date=$(wagman-client ver | sed -n -e 's/time //p') || wagman_build_date=0
    echo "Wagman build epoch: ${wagman_build_date}"
    guest_node_date=$(${script_dir}/eplogin date +%s) || guest_node_date=0
    echo "Guest Node epoch: ${guest_node_date}"
    dates=($system_date $wagman_date $wagman_build_date $guest_node_date)
    IFS=$'\n'
    date=$(echo "${dates[*]}" | sort -nr | head -n1)
    echo "Setting the system epoch to ${date}..."
    date -s @$date
  fi

  # Sync the system time with the hardware clock
  echo "Syncing the Node Controller hardware clock with the system date/time..."
  hwclock -w

  return 0
}

main() {
  set +e

  echo "entering main time check loop..."
  while [ 1 ] ; do
    local retry=1
    while [ ${retry} -eq 1 ] ; do
      echo "attempting to set the time..."
      try_set_time check_interval
      if [ $? -eq 0 ] ; then
        echo "Successfully updated dates/times."
        retry=0
      else
        # did not set time, will try again.
        echo "failed to set time. retrying in 10 seconds..."
        sleep 10
      fi
    done

    echo "Waiting for next date/time update cycle..."
    sleep ${CHECK_INTERVAL}
  done
}

CHECK_INTERVAL='24h'

main