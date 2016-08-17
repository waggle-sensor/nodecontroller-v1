import subprocess
import requests
from datetime import datetime


def get_system_date():
    output = subprocess.check_output(['date', '+%Y %m %d %H %M %S']).decode()
    year, month, day, hour, minute, second = map(int, output.split())
    return datetime(year, month, day, hour, minute, second)


def get_wagman_date():
    output = subprocess.check_output(['python3', 'wagman_client.py', 'date'])
    year, month, day, hour, minute, second = map(int, output.split())
    return datetime(year, month, day, hour, minute, second)


def get_beehive_date():
    try:
        r = requests.get('http://beehive1.mcs.anl.gov/api/1/epoch')
        assert r.status_code == 200
        response = r.json()
        timestamp = int(response['epoch'])
        return datetime.fromtimestamp(timestamp)
    except:
        return None


beehive_date = get_beehive_date()

if beehive_date:
    print('choosing beehive', beehive_date)
else:
    latest_date = max(get_wagman_date(), get_system_date())
    print(latest_date)
