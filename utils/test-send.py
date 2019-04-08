import beehive
# ANL:waggle-license
#  This file is part of the Waggle Platform.  Please see the file
#  LICENSE.waggle.txt for the legal details of the copyright and software
#  license.  For more details on the Waggle project, visit:
#           http://www.wa8.gl
# ANL:waggle-license
import datetime


connection = beehive.Connection(
    host='beehive',
    port=23181,
    node='0000000000AAAAAA',
    keyfile='SSL/node/key.pem',
    certfile='SSL/node/cert.pem',
    caroot='SSL/waggleca/cacert.pem')


def send_message(sensor, data):
    timestamp_utc = datetime.datetime.utcnow()
    timestamp_date = timestamp_utc.date()
    timestamp_epoch = int(float(timestamp_utc.strftime("%s.%f"))) * 1000

    message_data = [
        str(timestamp_date),
        'testplugin',  # <- can change name
        '1',
        'default',
        '%d' % timestamp_epoch,
        sensor,
        'meta.txt',
        data,
    ]

    connection.send_data(message_data)


send_message('testsensor', [
    'key1:value1',
    'key2:value2',
])
