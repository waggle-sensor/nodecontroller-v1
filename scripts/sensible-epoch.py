#!/usr/bin/env python3
import subprocess
import requests
import re


def get_system_date():
    output = subprocess.check_output(['date', '+%s']).decode()
    return int(output)


def get_wagman_date():
    output = subprocess.check_output(['wagman-client', 'epoch']).decode()
    return int(output)


def get_wagman_build_time():
    output = subprocess.check_output(['wagman-client', 'ver']).decode()
    return int(re.search('time (\d+)', output).group(1))


def get_guest_node_date():
    output = subprocess.check_output(['ssh', '-i', '/usr/lib/waggle/SSL/guest/id_rsa_waggle_aot_guest_node', 'waggle@10.31.81.51', 'date', '+%s']).decode()
    return int(output)


def get_beehive_date():
    r = requests.get('http://beehive1.mcs.anl.gov/api/1/epoch')
    assert r.status_code == 200
    response = r.json()
    return int(response['epoch'])


def get_dates(sources):
    for source in sources:
        try:
            yield source()
        except:
            pass


sources = [
    get_system_date,
    get_wagman_date,
    get_wagman_build_time,
    get_guest_node_date,
]

try:
    date = get_beehive_date()
    print(date)
except:
    dates = list(get_dates(sources))
    print(max(dates))
