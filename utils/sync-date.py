import subprocess
import requests
from datetime import datetime


def get_system_date():
    output = subprocess.check_output(['date', '+%s']).decode()
    return int(output)


def get_wagman_date():
    output = subprocess.check_output(['wagman-client', 'date']).decode().strip()
    return int(datetime.strptime(output, '%Y %m %d %H %M %S').strftime('%s'))


def get_guest_node_date():
    output = subprocess.check_output(['ssh', '-i', '/usr/lib/waggle/SSL/guest/id_rsa_waggle_aot_guest_node', 'waggle@10.31.81.51', 'date', '+%s']).decode()
    return int(output)


def get_beehive_date():
    r = requests.get('http://beehive1.mcs.anl.gov/api/1/epoch')
    assert r.status_code == 200
    response = r.json()
    return int(response['epoch'])


dates = []

for get_date in [get_system_date, get_wagman_date, get_beehive_date, get_guest_node_date]:
    try:
        dates.append(get_date())
    except:
        pass

print('max date', max(dates))
