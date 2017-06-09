#!/usr/bin/env python3
"""
This file stores all of the configurable variables for the node controller.
"""
import sys
import pika
import ssl
import string
import random
from multiprocessing import Manager
import json
import netifaces
from waggle.protocol.utils.packetmaker import *


def read_file( str ):
    if not os.path.isfile(str) :
        return ""
    with open(str,'r') as file_:
        return file_.read().strip()
    return ""


NODE_ID = read_file('/etc/waggle/node_id')

if not NODE_ID:
    sys.stdout.write("error: NODE_ID is not defined")
    sys.exit(1)



manager = Manager()

conf = manager.dict()

conf['QUEUENAME'] = read_file('/etc/waggle/queuename')


#Get node controller IP
NCIP = read_file('/etc/waggle/NCIP')
if NCIP == "":
  NCIP = netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']


#get server IP from file
#CLOUD_IP = read_file('/etc/waggle/server_ip') #TODO: deprecate this
BEEHIVE_HOST='beehive'

# the certificate server is optional and may only be accessible in an internal network
CERT_SERVER_PORT=24181


def create_dev_dict():
    """
        This function creates the device dictionary that maps each node with its location/ priority in the data cache.
    """

    # write a default devices file if one doesn't already exist
    devices_filename = '/etc/waggle/devices'
    if not os.path.isfile(devices_filename):
        with open(devices_filename,'w') as devices_file:
            devices_file.write("%s, \n" % NODE_ID)
            devices_file.write("1,2,3,4, \n")
            devices_file.write("%s:5, \n" % NODE_ID)

    #Registered devices, available locations/priorities, and current device:location/priority maps are stored in this file
    #This file is updated in msg_handler.py when a GN registers or de-registers
    with open('/etc/waggle/devices', 'r') as file_:
        lines = file_.readlines()

    #the third line in the devices file contains a mapping of devices to their priority
    #that is used to contruct the dictionary
    mapping = []
    while True:
        if not lines[2].find(',') == -1:
            device, lines[2] = lines[2].split(',', 1)
            device, priority = device.split(':',1)
            mapping.append((device,int(priority)))
        else:
            break
    return dict(mapping)


DEVICE_DICT = create_dev_dict()

#if new devices were registered after the initial start up, the device dictionary will occasionally need to be updated
def update_dev_dict():
    """
        This function updates the device dictionary when a GN registers or de-registers.
    """
    DEVICE_DICT = create_dev_dict()
    return DEVICE_DICT

#lists the order of device priority. Each device corresponds with a location in the data cache
#The highest priority position is at the front of the list, the lowest priority is at the end.
#The node controller is 5
PRIORITY_ORDER = [5,4,3,2,1]

#This specifies the maximum RAM available to the data cache
#Here, we assume that each message stored is no larger than 1K
AVAILABLE_MEM = 256000

#The params used to connect to the cloud are stored here
# [deprecated] CLOUD_ADDR = 'amqps://waggle:waggle@' + BEEHIVE_HOST + ':5671/%2F'



USE_SSL=True
RABBITMQ_PORT=23181

CLIENT_KEY_FILE="/usr/lib/waggle/SSL/node/key.pem"
CLIENT_CERT_FILE="/usr/lib/waggle/SSL/node/cert.pem"
CA_ROOT_FILE="/usr/lib/waggle/SSL/waggleca/cacert.pem"


pika_credentials = pika.PlainCredentials('node', 'waggle')

pika_params=pika.ConnectionParameters(  host=BEEHIVE_HOST,
                                        credentials=pika_credentials,
                                        virtual_host='/',
                                        port=RABBITMQ_PORT,
                                        ssl=USE_SSL,
                                        ssl_options={"ca_certs": CA_ROOT_FILE , 'certfile': CLIENT_CERT_FILE, 'keyfile': CLIENT_KEY_FILE, 'cert_reqs' : ssl.CERT_REQUIRED},
                                        socket_timeout=10
                                         )
#else:
#    pika_params=pika.ConnectionParameters(host=BEEHIVE_HOST, credentials=pika_credentials, virtual_host='/', port=RABBITMQ_PORT, ssl=USE_SSL)



def get_config():
    """
    This function sends all of the stored information to the cloud.

    """
    #  node_id ascii PRIMARY KEY,
    #                        timestamp timestamp,
    #                        queue ascii,
    #                        config_file ascii,
    #                        extra_notes list<ascii>,
    #                        sensor_names list<ascii>,
    #                        height double,
    #                        latitude double,
    #                        longitude double,
    #                        name ascii
    config_dict = { 'node_id': NODE_ID,
                    'queue' : conf['QUEUENAME'],
                    'name': NODE_ID,
                    'device_dict' : DEVICE_DICT,
                    'priority_order' : PRIORITY_ORDER
                    }

    return json.dumps(config_dict)

    #deprecated stuff below
    #add all the configuration
    config ='Node ID: ' + NODE_ID + '\n'
    config = config + 'Queuename: ' + conf['QUEUENAME'] + '\n'
   # config = config + 'Node Controller IP: ' + NCIP + '\n' # deprecated
    config = config + 'Device dictionary: ' + str(DEVICE_DICT) + '\n'
    config = config + 'Priority order: ' + str(PRIORITY_ORDER) + '\n'
    config = config + 'Available memory for data cache: ' + str(AVAILABLE_MEM) + '\n'
    #config = config + 'Cloud IP address and parameters: ' + CLOUD_ADDR + '\n'

    return config



def id_generator(size=30, chars=string.ascii_letters + string.digits + ".-_"):
    return ''.join(random.choice(chars) for _ in range(size))
