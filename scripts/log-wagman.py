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


def intlist(s):
    return list(map(int, s.split()))


def parse_version(s):
    result = {}

    for line in s.splitlines():
        key, _, value = line.partition(' ')
        result[key.strip()] = value.strip()

    return result

for attempt in range(10):
    try:
        results = {}

        results['id'] = wagman_output('id').lower()
        results['version'] = parse_version(wagman_output('ver'))
        results['uptime'] = int(wagman_output('up'))
        results['date'] = intlist(wagman_output('date'))
        results['current'] = intlist(wagman_output('cu'))
        results['therm'] = intlist(wagman_output('th'))
        results['heartbeat'] = intlist(wagman_output('hb'))
        results['fails'] = intlist(wagman_output('fc'))
        results['media'] = [wagman_output('bs 0'),
                            wagman_output('bs 1')]

        logger.info(json.dumps(results))
        break
    except:
        pass
else:
    raise RuntimeError('failed to collect results')
