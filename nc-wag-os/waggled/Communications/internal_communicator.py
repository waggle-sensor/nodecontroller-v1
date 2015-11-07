#!/usr/bin/env python

import socket, os, os.path, time, sys, logging
from multiprocessing import Process, Queue
import multiprocessing
sys.path.append('../../../protocol/')
from protocol.PacketHandler import *
sys.path.append('../NC/')
from NC_configuration import *


#logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


#TODO Could combine processes: one server and one client instead of two. Need to be able to distinguish between a pull request and a message push.
"""
    The internal communicator is the channel of communication between the GNs and the data cache. It consists of four processes: Push and pull unix socket client processes to communicate with the data cache
    and push and pull TCP server processes for communicating with the GNs. 
    
""" 

def send(msg):
    """
        This function is used only if the guest node and node controller are being run on the same machine. 
        It skips the push server that is used to connect with external guestnodes and pushes the message directly into the data cache.
        Skipping the server eliminates the need for a network setup in order to get messages from sensors to the data cache, 
        allowing a bare-essentials version of waggle to be used anywhere. 
        
        :param string msg: The packed waggle message that needs to be sent.
    """
    while True:
        try:
            #connect to DC and send msg
            if os.path.exists('/tmp/Data_Cache_server'):
                client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                try:
                    client_sock.connect('/tmp/Data_Cache_server')
                    logger.info( "Connected to data cache... ")
                    
                    client_sock.sendall(msg)
                    client_sock.close() #closes socket after each message is sent 
                    break #break loop when message sent. Otherwise, keep trying to connect until successful.
                except Exception as e:
                    logger.error( e )
                    time.sleep(1)
                    client_sock.close()

            else: 
                time.sleep(1)
                logger.warning('Unable to connect to DC...')

        except KeyboardInterrupt, k:
            logger.Info("Shutting down.")
            
            break
    client_sock.close()
    

class internal_communicator(object):
    """
        This class stores shared variables among the processes.
    
    """ 
    
    def __init__(self):
        pass
    
    DC_push = Queue() #stores messages to be pushed to the DC
    incoming_request = Queue() #stores the unique ID of GNs currently connected
    
    #stores incoming msgs. Each guest node has a unique queue that corresponds to the location in the device dictionary.
    incoming_msg = [Queue(), Queue(), Queue(), Queue(), Queue()] 
        
        

""" 
    A client process that connects to the data cache and pushes outgoing messages. 
    When a GN connects to the push server, the push server puts the msg into the DC_push queue. 
    When the DC_push queue is not empty, the client process connects to the data cache server and pushes the message into the data cache. 
"""


def internal_client_push():
    
    #sys.stderr.write('internal_client_push')
    
    comm = internal_communicator()
    logger.info('Internal client push started...\n')

    while True:
        try:
            #if the queue is not empty, connect to DC and send msg
            if not comm.DC_push.empty(): 
                if os.path.exists('/tmp/Data_Cache_server'):
                    client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    try:
                        client_sock.connect('/tmp/Data_Cache_server')
                        data = comm.DC_push.get() #Gets message out of the queue and sends to data cache
                        client_sock.sendall(data)
                        client_sock.close() #closes socket after each message is sent
                    except Exception as e:
                        logger.error(e)
                        #print e
                        client_sock.close()
                        time.sleep(1)
                    
                else: 
                    time.sleep(1)
                    sys.stderr.write('Internal client push unable to connect to DC...\n')
            else: 
                time.sleep(1) #else, wait until messages are in queue
        except KeyboardInterrupt, k:
                logger.Info( "Shutting down.")
                break
    client_sock.close()


""" 
    A client process that connects to the data cache, sends a pull request, and retrieves the message from the data cache. 
    When a GN connects to the pull server, the device ID is put into an incoming requests queue. When the queue is not empty, this process
    pulls the device ID from the queue and sends it to the data cache as the pull request. When the data cache returns a message, the message is put into the device's 
    incoming messages queue where it is pulled out by the pull server and sent to the GN.
"""

def internal_client_pull():
    
    comm = internal_communicator()
    logger.info('Internal client pull started...\n')
    
    while True:
        while comm.incoming_request.empty(): #sleeps until a GN initiates a pull request
            time.sleep(1)
        try: 
            if os.path.exists('/tmp/Data_Cache_server'):
                client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                try:
                    client_sock.connect('/tmp/Data_Cache_server')#opens socket when there is an incoming pull request
                    dev = comm.incoming_request.get() #gets the dev ID that is initiating the pull request
                    #TODO this could probably be done a different way, but there has to be some distinction between a pull request and message push
                    request = '|' + dev #puts the request in the correct format for the DC 
                    client_sock.send(request)
                    try:
                        msg = client_sock.recv(4028) #arbitrary, can go in config file
                    except: 
                        client_sock.close()
                        time.sleep(1)
                        break
                    if not msg:
                        break
                    else:
                        comm.incoming_msg[int(dev) - 1].put(msg) #puts the message in the device's incoming queue. Message is pulled out of queue by pull server and sent to GN. 
                        client_sock.close() #closes socket after each message is sent 
                        
                                
                except Exception as e:
                    sys.stderr.write(e)
                    logger.error(e)
                    
                    client_sock.close()
                    time.sleep(5)
            else:
                sys.stderr.write('Internal client pull unable to connect to DC.\n')
                time.sleep(1)
        except KeyboardInterrupt, k:
            logger.Info( "Internal client pull shutting down.")
            break
    client_sock.close()
    

""" 
    Server process that listens for connections from GNs. Once a GN connects and sends the message, the push server puts the message into the DC_Push queue, 
    where it will be pulled out and sent by the push client and pushed into the data cache.
"""

def push_server():
    
    comm = internal_communicator()
    #HOST = NCIP 
    HOST = socket.gethostname()
    PORT = 9090
    try:
      server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as msg:
      logger.info( "(socket.socket) Socket Error: %s\n" % msg )
      
      return 1
    try:  
      server.bind((HOST,PORT))
    except socket.error as msg:
      logger.info( "(server.bind) Socket Error: %s (%s, %s)\n" % (msg, HOST, PORT) )
      return 1
    try:
      server.listen(5) #supports up to 5 threads, one for each GN
    except socket.error as msg:
      logger.info( "(server.listen) Socket Error: %s\n" % msg )
      return 1
      
    logger.info('Internal push server process started...\n')

    while True:
        client_sock, addr = server.accept()
        while True:
            try:
                data = client_sock.recv(4028) 
                if not data:
                    break #breaks the loop when the client socket closes
                elif data == 'Hello': #a handshake from a new guest node. 
                    client_sock.sendall('Hi') #NC sends 'Hi' to verify that it is the NC that the guest node is looking for.
                    client_sock.sendall(HOSTNAME)#sends unique ID to GN can send messages to NC if needed
                else:
                    comm.DC_push.put(data)
                
            except KeyboardInterrupt, k:
                logger.info("Internal push server shutting down.")
                
                break
    server.close()
        

""" 
    Server process that listens for connections from GNs. When a guest node connects, it sends its unique ID. The pull server puts that ID into a queue. The ID gets pulled out by the pull client and sent
    to the data cache. The client pull recieves a message from the data cache, puts it into the corresponding GN's queue. When the queue is not empty, the pull server pulls the message out and sends it to
    GN. If the GN disconnects before this process is complete, the pull server puts the message back into the DC_push queue to be put back into the data cache.
    
"""

def pull_server():
   
    comm = internal_communicator()
    #HOST = NCIP
    HOST = socket.gethostname()
    PORT = 9091
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    logger.debug("try to bind host=%s port=%s"%(HOST,PORT))
    try:
        server.bind((HOST,PORT))
    
        server.listen(5) #supports up to 5 threads, one for each GN
    except socket.error as msg:    
        server.close()
        server = None
        logger.error(msg)
        return
        
    logger.info('Internal pull server process started...\n')
    while True:
        client_sock, addr = server.accept()
        while True:
            try:
                data = client_sock.recv(4028) #Guest nodes connect and send their uniq_ID
                if not data:
                    break
                else:
                    for i in range(2): 
                        try:
                            dev_loc = DEVICE_DICT[data] #gets the device queue location from dictionary
                            comm.incoming_request.put(str(dev_loc)) #Unique ID goes into incoming requests queue. These get pulled out by the pull_client as pull requests
                            while comm.incoming_msg[int(dev_loc)-1].empty():
                                time.sleep(1) #sleeps until queue is no longer empty. Data cache returns 'False' if no messages are available.
                            msg = comm.incoming_msg[int(dev_loc)-1].get() #returns incoming messages. 
                            try: 
                                client_sock.sendall(msg) #sends the msg to the GN 
                            except: 
                                #puts the message back into the DC_push queue if the GN disconnects before the message is sent.
                                comm.DC_push.put(str(dev_loc))
                            #If the device is registered and the push is successful, no need to try again, break the loop
                            break 
                        except Exception as e:
                            #The device dictionary may not be up to date. Need to update and try again.
                            #If the device is still not found after first try, move on.
                            DEVICE_DICT = update_dev_dict() #this function is in the NC_configuration module
                            client_sock.sendall('False')
                        
            except KeyboardInterrupt, k:
                logger.info("Internal pull server shutting down.")
                
                server.close()
                break
    server.close()


internal_communicator_name2func = {} 
internal_communicator_name2func["internal_client_push"]=internal_client_push
internal_communicator_name2func["internal_client_pull"]=internal_client_pull
internal_communicator_name2func["push_server"]=push_server
internal_communicator_name2func["pull_server"]=pull_server


##uncomment for testing
if __name__ == "__main__":
    name2process={}
    try:
        
 
        for name, function in internal_communicator_name2func.iteritems():
            new_process = multiprocessing.Process(target=function, name=name)
            new_process.start()
            name2process[name]=new_process
            logger.info(name+' has started.')
                

        
    except KeyboardInterrupt, k:
        for name, subhash in internal_communicator_name2func.iteritems():
            logger.info( '(KeyboardInterrupt) shutting down ' + name)
            name2process[name].terminate()
      
        logger.info('Done.')
    
                
