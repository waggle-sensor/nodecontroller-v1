#!/bin/bash

wagman_get_epoch() {
date -d"$(printf '%d/%d/%d %d:%d:%d\n' $(wagman-client date))" +'%s' || echo 0
}

get_beehive_epoch() {
# TODO Compare to old endpoint. This *only* uses nginx server and doesn't require
# yet another cron job to run and update an epoch file.
echo "Getting the epoch from Beehive..."
date --date "$(curl -s -I http://beehive | grep 'Date:' | cut -d' ' -f 2-)" +%s
}

try_set_time()
{
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local wagman_date=0
    unset date

    # get epoch from server
    local exit_code=0

    if [ $(($(date +%s) - $GOT_BH_TIME)) -gt 82800 ]; then

        echo "Getting the epoch from Beehive..."
        local curl_out=$(curl -s --max-time 10 --connect-timeout 10 http://beehive/api/1/epoch?nodeid=$(hostname)_bootid=$(cat /proc/sys/kernel/random/boot_id | sed "s/-//g"))
        exit_code=$?
        if [ ${exit_code} -eq 0 ] ; then
            date_json=$(echo $curl_out | tr '\n' ' ')
            date=$(python -c "import json; print(json.loads('${date_json}')['epoch'])") || unset date
            GOT_BH_TIME=${date}
            echo "Got date '${date} from Beehive."
        else
            echo "Warning: could not get the epoch from Beehive."
            unset date
        fi
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
            GOT_BH_TIME=0
            return ${exit_code}
        fi



        if [ $(($(date +%s) - $SET_WAGMAN_TIME)) -gt 82800 ]; then
            # Update the WagMan date
            echo "Setting the Wagman date/time..."
            wagman-client date $(date +"%Y %m %d %H %M %S") || true
            SET_WAGMAN_TIME=$(date +%s)
        fi


        if [ $(($(date +%s) - $SET_EP_TIME)) -gt 82800 ]; then
            # Update the Edge Processor date
            echo "Setting the Edge Processor date/time..."
            ${script_dir}/eplogin /usr/lib/waggle/edge_processor/scripts/sync_date.sh $(date +%s)
            SET_EP_TIME=$(date +%s)
             # Sync the system time with the hardware clock
            ${script_dir}/eplogin hwclock -w
            exit_code=$?
            if [ ${exit_code} -ne 0 ] ; then
                SET_EP_TIME=0
                echo "Error: failed to set the Edge Processor system date/time."
    #             return ${exit_code}
            fi
        fi

    else
        echo "Setting the date/time update interval to 60 seconds..."
        CHECK_INTERVAL='60'  # seconds
        wagman_date=$(wagman_get_epoch)
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

    return ${exit_code}
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
echo "failed to set time. retrying in 60 seconds..."
sleep 60
fi
done

echo "Waiting for next date/time update cycle..."${CHECK_INTERVAL}
echo "NC time set at-"${GOT_BH_TIME}
echo "EP time set at-"${SET_WAGMAN_TIME}
echo "Wagman time set at-"${GOT_BH_TIME}
sleep ${CHECK_INTERVAL}
done
}

CHECK_INTERVAL='24h'

GOT_BH_TIME=0
SET_WAGMAN_TIME=0
SET_EP_TIME=0

main
