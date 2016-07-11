#!/usr/bin/env python3

import socket, os, os.path, time, pika, logging, datetime, sys
from multiprocessing import Process, Queue, Value
import multiprocessing
sys.path.append('../../../')
from waggle_protocol.protocol.PacketHandler import *
sys.path.append('../../../')
from waggle_protocol.utilities import packetmaker
sys.path.append('../NC/')
from NC_configuration import *

sys.path.append('../DataCache/')
from send2dc import send


logging.basicConfig()
logger = logging.getLogger(__name__)


""" 
    The external communicator is the communication channel between the cloud and the DC. It consists of four processes: two pika clients for pushing and pulling to the cloud and two clients for pushing 
    and pulling to the data cache.
"""
class external_communicator(object):
    """
        This class is a convenience class that stores shared variables amongst all instances. 
    """
    
    def __init__(self):
        pass
    
    incoming = Queue() #stores messages to push into DC 
    outgoing = Queue() #stores messages going out to cloud
    cloud_connected = Value('i') #indicates if the cloud is or is not connected. Clients only connect to DC when cloud is connected. 
    #params = pika.connection.URLParameters(CLOUD_ADDR) #SSL 




""" 
    A pika client for rabbitMQ to push messages to the cloud. When the cloud is connected, the pull client sends pull requests and puts messages into the outgoing queue. 
    When the outgoing queue is not empty, this pika client will connect and push those messages to the cloud.
""" 
def pika_push():
       
    comm = external_communicator()
    #params = comm.params
    logger.info('Pika push started...\n')
    while True:
        connection=None
        
        # try to connect to cloud
        try: 
            connection = pika.BlockingConnection(pika_params)
        except Exception as e: 
            logger.warning( 'Pika_push currently unable to connect to cloud (%s:%d) (queue: %s) : %s' % (pika_params.host, pika_params.port , conf['QUEUENAME'], str(e)) )
            comm.cloud_connected.value = 0 #set the flag to 0 when not connected to the cloud. I
            time.sleep(5)
            break
                
        logger.warning( 'Pika_push connected to cloud (%s:%d)' % (pika_params.host, pika_params.port) )
        
        # get channel
        try:    
            channel = connection.channel()
            comm.cloud_connected.value = 1 #set the flag to true when connected to cloud
            #Declaring the queue
            channel.queue_declare(queue=conf['QUEUENAME'])
            logger.info("Pika push got queue \"%s\"." % (conf['QUEUENAME']))
        except Exception as e:  
            logger.warning('Pika_push unable to get channel (%s:%d) (queue: %s) : %s' % (pika_params.host, pika_params.port , conf['QUEUENAME'], str(e)) )
            comm.cloud_connected.value = 0 #set the flag to 0 when not connected to the cloud. I
            time.sleep(5)
            break
        
        try:
            send_registrations() #sends registration for each node and node controller configuration file
        except Exception as e:  
            logger.error('registration failed: %s' % (str(e)) )   
            comm.cloud_connected.value = 0 #set the flag to 0 when not connected to the cloud. I
            time.sleep(5)
            break
            
        while True:
            
            #while comm.outgoing.empty(): #sleeps until there are messages to send
            #    time.sleep(1)
            
            time_0 = time.time()
            msg = comm.outgoing.get() # gets the first item in the outgoing queue
            time_1 = time.time()
            logger.debug('Pika_push: sending message to cloud. (waited %d seconds)' % (time_1 - time_0))
            
            try:
               
                channel.basic_publish(exchange='waggle_in', routing_key= 'in', body= msg) #sends to cloud 
                #connection.close()
                
            except pika.exceptions.ConnectionClosed:
                logger.debug("Pika push connection closed. Waiting and trying again " + str(datetime.datetime.now()) + '\n')
                comm.cloud_connected.value = 0
                time.sleep(5)
                break #need to break this loop to reconnect
            except Exception as e:
                logger.error("Pika push encounterd an unexpected error: %s" % (str(e)))
                comm.cloud_connected.value = 0
                time.sleep(5)
                break
            time_2 = time.time()
            logger.debug('Pika_push: sending message took %d seconds' % (time_2 - time_1))
            
        if connection:
            try:
                connection.close(0)
            except:
                pass



""" 
     A pika client for pulling messages from the cloud. If messages are sent from the cloud, this client will put them into the incoming queue.
"""       
def pika_pull():
    

    logger.info('Pika pull started...\n')
    comm = external_communicator()
    #params = comm.params
    #params = pika.connection.URLParameters("amqps://waggle:waggle@10.10.10.108:5671/%2F") #SSL
    
    if not conf['QUEUENAME']:
        logger.warning("QUEUENAME is not defined... waiting..")
        time.sleep(5)
        return
        
    
    while True: 
        
        try:
            connection = pika.BlockingConnection(pika_params)
        except Exception as e:
            logger.warning('(pika.BlockingConnection) Pika_pull currently unable to connect to cloud. Waiting before trying again. ' + str(e))
            comm.cloud_connected.value = 0 #set the flag to 0 when not connected to the cloud
            time.sleep(5)
            continue
        
        try:
            channel = connection.channel()
        except Exception as e:
            logger.warning('(pika.BlockingConnection) Could not create channel. ' + str(e))
            comm.cloud_connected.value = 0 #set the flag to 0 when not connected to the cloud
            time.sleep(5)
            continue
        
        logger.info('Pika pull connection successful.\n')
        comm.cloud_connected.value = 1 #sets indicator flag to 1 so clients will connect to data cache
        
        try:
            channel.queue_declare(queue=conf['QUEUENAME'])
        except Exception as e:
            logger.debug('Cannot declare queuename (%s) : %s' % (conf['QUEUENAME'], str(e)))
            pass

        try:
            channel.basic_consume(callback, queue=conf['QUEUENAME'])
        except:
            logger.warning('(channel.basic_consume) failed: '+ str(e))
            comm.cloud_connected.value = 0 #set the flag to 0 when not connected to the cloud
            time.sleep(5)   
            continue
            
                        
        try:
            #loop that waits for data 
            channel.start_consuming() #TODO Can this process still publish to RabbitMQ while this is continuously looping? If so, The pika_pull and pika_push processes can and should be combined. 
        except:
            logger.warning('(channel.start_consuming) something wrong:' + str(e))
            comm.cloud_connected.value = 0 #set the flag to 0 when not connected to the cloud
            
        time.sleep(5)    

    connection.close()
                
                
#pulls the message from the cloud and puts it into incoming queue 
def callback(ch, method, properties, body):
    comm = external_communicator()
    logger.debug('Callback received message from cloud, length %d ' % (len(body)))
    comm.incoming.put(body) 
    ch.basic_ack(delivery_tag=method.delivery_tag) #RabbitMQ will not delete message until ack received
                
            
        

""" 
    A client process that connects to the data cache if the cloud is currently connected.  Once a message is recieved, it is put into the outgoing queue. 
    
"""

def external_client_pull():
  
    logger.info('External client pull started...\n')
    comm = external_communicator()
    while True:
        try:
            if comm.cloud_connected.value == 1: #checks if the cloud is connected
                try:
                    if os.path.exists('/tmp/Data_Cache_server'):
                        client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                        client_sock.connect('/tmp/Data_Cache_server') #connects to server
                        #logger.debug("Client_pull connected to data cache... ")
                        #sends the pull request indicating that it is an outgoing pull request. 
                        #TODO This can be improved (both clients combined into one) if there is a better way to distinguish incoming vs outgoing pull and pull vs push requests. 
                        data = '|o' 
                        client_sock.send(data)
                        msg = client_sock.recv(4028) #can be changed 
                        if msg:
                            if msg != 'False':
                                logger.debug("put message from DC in outgoing queue")
                                comm.outgoing.put(msg) #puts the message in the outgoing queue
                            else:
                                #logger.debug("DC has no message for me.")
                                time.sleep(1)
                        else:
                            logger.debug("DC has no message for me. (msg==None !?)")
                            time.sleep(1)
                            
                        client_sock.close()
                    else:
                        logger.warning('External client pull unable to connect to the data cache... path does not exist!\n')
                        time.sleep(5)
                except:
                    logger.info('External client pull disconnected from data cache. Waiting and trying again.\n')
                    client_sock.close()
                    time.sleep(5)
            else:
                logger.debug('External client pull...cloud is not connected. Waiting and trying again.')
                time.sleep(5)
        except KeyboardInterrupt as k:
                logger.info("External client pull shutting down.\n")
                break
    client_sock.close()
        
        

""" 
    A client process that connects to the data cache and pushes incoming messages.
"""

def external_client_push():
    
    
    logger.info('External client push started...\n')
    comm = external_communicator()
    
    
    while True:
        while comm.incoming.empty(): #sleeps until a message arrives in the incoming queue 
            time.sleep(1)
        try: 
            if os.path.exists('/tmp/Data_Cache_server'):
                client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                client_sock.connect('/tmp/Data_Cache_server') #opens socket when a message is in the queue
                logger.debug("Client_push connected to data cache... ")
                msg = comm.incoming.get() #gets the incoming message from the queue
                client_sock.send(msg) #sends msg
                client_sock.close()
            else:
                logger.info("External client push-Unable to connect to Data Cache.\n")
                time.sleep(5)
        except KeyboardInterrupt as k:
            logger.info("External client push shutting down.\n")
            break
    client_sock.close()
        
        

def send_registrations():
    """ 
        Sends registration message for NC and GNs and configuration file for node controller.
    """
    #loops through the list of nodes and send a registration for each one
    #logger.debug("number of devices: "+str(len(DEVICE_DICT.keys())))
    
    #for device in DEVICE_DICT.keys():
    #    logger.debug("try to send registration for device "+device)
    #    header_dict = {
    #        "msg_mj_type" : ord('r'),
    #        "msg_mi_type" : ord('r'),
    #        "s_uniqid"    : int("0x" + device, 0)
    #        }
    #    msg = str(conf['QUEUENAME'])
    #    try: 
    #        packet = pack(header_dict, message_data = msg)
    #    except Exception as e: 
    #        logger.error("pack failed: "+str(e))
    #        raise
    #            
    #    
    #    try:
    #        for pack_ in packet:
    #            try:
    #                send(pack_)
    #            except Exception as e: 
    #                logger.error("send(pack_) failed: "+str(e))
    #                raise
    #                
    #    except Exception as e: 
    #        logger.error("for loop send(pack_) failed: "+str(e))
    #        raise
    #        
    #    logger.debug("sent registration for device "+device)
            
    #send nodecontroller configuration file
    config = get_config() #this function is in NC_configuration
    logger.info("Sending config for registration: "+config)
    try:
        packet = make_config_reg(config) # this is major, minor: "rn"
        for pack_ in packet:
            send(pack_)
    except Exception as e:
        logger.error(str(e))
        raise   


 
external_communicator_name2func = {} 

external_communicator_name2func["pika_pull"]=pika_pull
external_communicator_name2func["pika_push"]=pika_push
external_communicator_name2func["client_push"]=external_client_push
external_communicator_name2func["client_pull"]=external_client_pull
                    

if __name__ == "__main__":
    name2process={}
    
    try:
        
        for name, function in external_communicator_name2func.items():
            new_process = multiprocessing.Process(target=function, name=name)
            new_process.start()
            name2process[name]=new_process
            logger.info(name+' has started.')
        
        while True:
            pass
        
    except KeyboardInterrupt as k:
      
        for name, subhash in external_communicator_name2func.items():
            logger.info( '(KeyboardInterrupt) shutting down ' + name)
            name2process[name].terminate()
        logger.info('Done.')
