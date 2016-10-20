#!/usr/bin/python3
import subprocess
import logging
import waggle.logging
import json


logger = waggle.logging.getLogger('wagman')
logger.setLevel(logging.DEBUG)


def wagman_output(args):
    command = 'wagman-client {}'.format(args)
    return subprocess.check_output(command, shell=True).decode().strip()


def catlines(s):
    return ' '.join(s.strip().split())


for attempt in range(10):
    try:
        results = {}

        results['id'] = wagman_output('id').lower()
        results['version'] = catlines(wagman_output('ver'))
        results['uptime'] = int(wagman_output('up'))
        results['date'] = list(map(int, wagman_output('date').split()))
        results['current'] = list(map(int, wagman_output('cu').split()))
        results['therm'] = list(map(int, wagman_output('th').split()))
        results['heartbeat'] = list(map(int, wagman_output('hb').split()))
        results['fails'] = list(map(int, wagman_output('fc').split()))
        results['media'] = [wagman_output('bs 0'),
                            wagman_output('bs 1')]

        logger.info(json.dumps(results))
        break
    except:
        pass
else:
    raise RuntimeError('failed to collect results')
