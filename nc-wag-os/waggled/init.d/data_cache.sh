#!/bin/sh
### BEGIN INIT INFO
# Provides:          Data Cache
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start daemon at boot time
# Description:       Enable service provided by daemon.
### END INIT INFO

dir="/usr/lib/waggle/nodecontroller/nc-wag-os/waggled/DataCache"
cmd_start="python Data_Cache.py --logging"
user=""

name="data_cache_initd"
pid_file="/var/run/Data_Cache.pid" 
stdout_log="/var/log/waggle/$name.stdout"
stderr_log="/var/log/waggle/$name.stderr"

get_pid() {
    cat "$pid_file"
}

is_running() {
    [ -f "$pid_file" ] && ps `get_pid` > /dev/null 2>&1
}

case "$1" in
    start)
    if is_running; then
        echo "Already started"
    else
        echo "Starting $name"
        rm -f $pid_file
        cd "$dir"
        if [ -z "$user" ]; then
            sudo $cmd_start >> "$stdout_log" 2>> "$stderr_log" &
        else
            sudo -u "$user" $cmd_start >> "$stdout_log" 2>> "$stderr_log" &
        fi
        echo $! > "$pid_file" # data_cache writes its own pid file
        sleep 1
        if ! is_running; then
            echo "Unable to start, see $stdout_log and $stderr_log"
            exit 1
        fi
    fi
    ;;
    stop)
    if is_running; then
        echo -n "Stopping $name.."
        cd "$dir"
        pid=`get_pid`
        kill ${pid}
        echo
        for i in . . . . . . . . . . . . . . . . . ; do
            if ! is_running; then
                echo "stopped."
                break
            fi

            echo -n "."
            sleep 2
        done
        
        if is_running; then
          echo "Trying kill -9"
          kill -9 $pid
          sleep 2
        fi

        if is_running; then
            echo "Not stopped; may still be shutting down or shutdown may have failed"
            exit 1
        else
            echo "Stopped"
            rm  -f ${pid_file}
        fi

    else
        echo "Not running"
    fi
    ;;
    restart)
    $0 stop
    if is_running; then
        echo "Unable to stop, will not attempt to start"
        exit 1
    fi
    $0 start
    ;;
    status)
    if is_running; then
        echo "Running"
    else
        echo "Stopped"
        exit 1
    fi
    ;;
    *)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 1
    ;;
esac

exit 0
