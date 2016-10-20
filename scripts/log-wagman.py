#!/usr/bin/python3
import subprocess
import time
import logging
import waggle.logging


logger = waggle.logging.getLogger('wagman')
logger.setLevel(logging.DEBUG)


template = '''
id={id}
version={version}
uptime={uptime}
date={date}
current={current}
therm={therm}
heartbeat={heartbeat}
fails={fails}
media={media}
'''.strip()


def catlines(s):
    return ' '.join(s.strip().split())


results = {}

for attempt in range(10):
    try:
        results['id'] = subprocess.check_output('wagman-client id', shell=True).decode().strip().lower()
        results['version'] = catlines(subprocess.check_output('wagman-client ver', shell=True).decode())
        results['uptime'] = subprocess.check_output('wagman-client up', shell=True).decode().strip()
        results['date'] = subprocess.check_output('wagman-client date', shell=True).decode().strip()
        results['current'] = catlines(subprocess.check_output('wagman-client cu', shell=True).decode())
        results['therm'] = catlines(subprocess.check_output('wagman-client th', shell=True).decode())
        results['heartbeat'] = catlines(subprocess.check_output('wagman-client hb', shell=True).decode())
        results['fails'] = catlines(subprocess.check_output('wagman-client fc', shell=True).decode())

        media = [subprocess.check_output('wagman-client bs 0', shell=True).decode().strip(),
                 subprocess.check_output('wagman-client bs 1', shell=True).decode().strip()]
        results['media'] = ' '.join(media)
    except Exception as e:
        print(e)
        continue
    else:
        logger.info(template.format(**results))
        break
