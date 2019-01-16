#!/bin/bash

wagman_get_epoch() {
    echo "getting wagman epoch"
    wagman_date=$(wagman-client date)
    echo "wagman date is $wagman_date"
    date -d"$(printf '%04d/%02d/%02d %02d:%02d:%02d\n' $wagman_date)" +'%s' || echo 0
}

get_beehive_epoch() {
    echo "getting beehive epoch"
    nodeid=$(hostname)
    bootid=$(sed 's/-//g' /proc/sys/kernel/random/boot_id)
    beehive_url=http://beehive/epoch?nodeid="$nodeid"_bootid="$bootid"
    echo "request $beehive_url"
    beehive_date=$(curl -s -I "$beehive_url" | grep -i 'Date:' | cut -d' ' -f 2-)
    echo "beehive date is $beehive_date"
    date --date "$beehive_date" +%s
}

try_set_time() {
    local wagman_date=0
    unset date

    # get epoch from server
    local exit_code=0

    if [ $(($(date +%s) - $GOT_BH_TIME)) -gt 82800 ]; then
        date=$(get_beehive_epoch)
        GOT_BH_TIME=${date}
        echo "Got date ${date} from Beehive."

        if [ $? -ne 0 ]; then
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
            ssh ep /usr/lib/waggle/edge_processor/scripts/sync_date.sh $(date +%s)
            SET_EP_TIME=$(date +%s)
             # Sync the system time with the hardware clock
            ssh ep hwclock -w
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
        guest_node_date=$(ssh ep date +%s) || guest_node_date=0
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
while true ; do
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
