#!/usr/bin/python3
import subprocess
import logging
import waggle.logging


logger = waggle.logging.getLogger('wagman')
logger.setLevel(logging.DEBUG)


def wagman_output(args):
    command = 'wagman-client {}'.format(args)
    return subprocess.check_output(command, shell=True).decode().strip()


def catlines(s):
    return ' '.join(s.strip().split())


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

for attempt in range(10):
    try:
        results = {}

        results['id'] = wagman_output('id').lower()
        results['version'] = catlines(wagman_output('ver'))
        results['uptime'] = wagman_output('up')
        results['date'] = wagman_output('date')
        results['current'] = catlines(wagman_output('cu'))
        results['therm'] = catlines(wagman_output('th'))
        results['heartbeat'] = catlines(wagman_output('hb'))
        results['fails'] = catlines(wagman_output('fc'))
        results['media'] = ' '.join([wagman_output('bs 0'),
                                     wagman_output('bs 1')])

        logger.info(template.format(**results))
        break
    except Exception as e:
        print(e)
        continue
