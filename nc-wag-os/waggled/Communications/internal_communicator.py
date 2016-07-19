#!/usr/bin/env python3

import socket, os, os.path, time, sys, logging, zmq
from multiprocessing import Process, Queue
import multiprocessing
sys.path.append('../../../')
from waggle_protocol.protocol.PacketHandler import *
sys.path.append('../NC/')
from NC_configuration import *
from crcmod.predefined import mkCrcFun


logging.basicConfig()
logger = logging.getLogger(__name__)



#TODO Could combine processes: one server and one client instead of two. Need to be able to distinguish between a pull request and a message push.
"""
    The internal communicator is the channel of communication between the GNs and the data cache. It consists of four processes: Push and pull unix socket client processes to communicate with the data cache
    and push and pull TCP server processes for communicating with the GNs. 
    
""" 
    

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
                        client_sock.sendall(data.encode('iso-8859-1'))
                        client_sock.close() #closes socket after each message is sent
                    except Exception as e:
                        logger.error(e)
                        #print e
                        client_sock.close()
                        time.sleep(1)
                        continue
                    logger.debug("Sending data from DC-push queue to Data_Cache socket")    
                else: 
                    logger.error('Internal client push unable to connect to DC...')
                    time.sleep(1)
            else: 
                time.sleep(1) #else, wait until messages are in queue
        except KeyboardInterrupt as k:
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
                    client_sock.send(request.encode('iso-8859-1'))
                    try:
                        msg = client_sock.recv(4028).decode('iso-8859-1') #arbitrary, can go in config file
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
                    sys.stderr.write(str(e))
                    logger.error(str(e))
                    
                    client_sock.close()
                    time.sleep(5)
            else:
                sys.stderr.write('Internal client pull unable to connect to DC.\n')
                time.sleep(1)
        except KeyboardInterrupt as k:
            logger.Info( "Internal client pull shutting down.")
            break
    client_sock.close()
    




""" 
    Server process that listens for connections from GNs. Once a GN connects and sends the message, the push server puts the message into the DC_Push queue, 
    where it will be pulled out and sent by the push client and pushed into the data cache.
"""

def push_server():
    
    comm = internal_communicator()
    HOST = NCIP 
    PORT = 9090
    # try:
    #   server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # except socket.error as msg:
    #   logger.info( "(socket.socket) Socket Error: %s\n" % msg )
      
    #   return 1
    # try:  
    #   server.bind((HOST,PORT))
    # except socket.error as msg:
    #   logger.info( "(server.bind) Socket Error: %s (%s, %s)\n" % (msg, HOST, PORT) )
    #   return 1
    # try:
    #   server.listen(5) #supports up to 5 threads, one for each GN
    # except socket.error as msg:
    #   logger.info( "(server.listen) Socket Error: %s\n" % msg )
    #   return 1
      
    nc_node_id_packed = bin_pack(nodeid_hexstr2int(NODE_ID),HEADER_BYTELENGTHS["s_uniqid"])
     
    
    
    logger.info('Internal push server process started...\n')

    # while True:
    #     client_sock, addr = server.accept()
    #     while True:
    #         try:
    #             data = client_sock.recv(4028) 
    #             if not data:
    #                 break #breaks the loop when the client socket closes
    #             elif data == 'Hello': #a handshake from a new guest node. 
    #                 client_sock.sendall('Hi') #NC sends 'Hi' to verify that it is the NC that the guest node is looking for.
    #                 client_sock.sendall(HOSTNAME)#sends unique ID to GN can send messages to NC if needed
    #             else:
    #                 # push data from guest node into data cache.
                    
    #                 # here we inject the nodecontroller ID as sender, overwriting the guestnode ID.
                    
    #                 # extract header so we can modify it
                    
    #                 if len(data) < HEADER_LENGTH:
    #                     logger.error("data fragment shorter than HEADER_LENGTH")
    #                     break
                    
    #                 header_bytearray = bytearray(data[:HEADER_LENGTH])
                    
    #                 # TODO: check crc
                    
    #                 # overwrite sender
    #                 try:
    #                     set_header_field(header_bytearray, 's_uniqid', nc_node_id_packed)
    #                 except Exception as e:
    #                     logger.error("set_header_field failed: %s" % (str(e)))
    #                     break
                        
    #                 #recompute header crc
    #                 try:
    #                     write_header_crc(header_bytearray)
    #                 except Exception as e:
    #                     logger.error("write_header_crc failed: %s" % (str(e)))
    #                     break
                        
    #                 # concatenate new header with old data
    #                 new_data = str(header_bytearray)+data[HEADER_LENGTH:]
                    
    #                 logger.debug("Sending data from GN into DC-push queue")
    #                 comm.DC_push.put(new_data)
    #                 logger.debug("(push_server) DC_push size: %d " % (comm.DC_push.qsize()))
                    
                
    #         except KeyboardInterrupt, k:
    #             logger.info("Internal push server shutting down.")
                
    #             break
    # server.close()

    context = zmq.Context()
    server_socket = context.socket(zmq.REP)
    server_socket.bind('tcp://%s:%s' % (HOST, PORT))

    while True:
        try:
            data = server_socket.recv()
            logger.debug("type is %s" % (type(data)))
#                .decode('iso-8859-1')
            if data == "time":
                t = int(time.time())
                res = '{"epoch": %d}' % (t)
                server_socket.send(res.encode('iso-8859-1'))
            else:
                server_socket.send("ack".encode('iso-8859-1'))
                if len(data) < HEADER_LENGTH:
                    logger.error("data fragment shorter than HEADER_LENGTH")
                    break
                
                header_bytearray = bytearray(data[:HEADER_LENGTH].encode('iso-8859-1'))
                
                # TODO: check crc
                
                # overwrite sender
                try:
                    set_header_field(header_bytearray, 's_uniqid', nc_node_id_packed)
                except Exception as e:
                    logger.error("set_header_field failed: %s" % (str(e)))
                    break
                    
                #recompute header crc
                try:
                    write_header_crc(header_bytearray)
                except Exception as e:
                    logger.error("write_header_crc failed: %s" % (str(e)))
                    break
                    
                # concatenate new header with old data
                #new_data = str(header_bytearray)+data[HEADER_LENGTH:]
                new_data = bytes(header_bytearray).decode('iso-8859-1')+data[HEADER_LENGTH:]
                
                logger.debug("Sending data from GN into DC-push queue")
                comm.DC_push.put(new_data)
                logger.debug("(push_server) DC_push size: %d " % (comm.DC_push.qsize()))
        except zmq.error.ZMQError as e:
            logger.debug("zmq.error.ZMQError: (%s) %s" % (str(type(e)), str(e)))
            continue
        except Exception as e:
            logger.debug("error recv message: (%s) %s" % (str(type(e)), str(e)))
            continue

    server_socket.close()

        

""" 
    Server process that listens for connections from GNs. When a guest node connects, it sends its unique ID. The pull server puts that ID into a queue. The ID gets pulled out by the pull client and sent
    to the data cache. The client pull recieves a message from the data cache, puts it into the corresponding GN's queue. When the queue is not empty, the pull server pulls the message out and sends it to
    GN. If the GN disconnects before this process is complete, the pull server puts the message back into the DC_push queue to be put back into the data cache.
    
"""

def pull_server():
   
    comm = internal_communicator()
    HOST = NCIP
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
                data = client_sock.recv(4028).decode('iso-8859-15') #Guest nodes connect and send their uniq_ID (non-blocking call)
                if not data:
                    time.sleep(1)
                    continue
                else:
                    for i in range(2): 
                        try:
                            dev_loc = DEVICE_DICT[data] #gets the device queue location from dictionary
                            comm.incoming_request.put(str(dev_loc)) #Unique ID goes into incoming requests queue. These get pulled out by the pull_client as pull requests
                            while comm.incoming_msg[int(dev_loc)-1].empty():
                                time.sleep(1) #sleeps until queue is no longer empty. Data cache returns 'False' if no messages are available.
                            msg = comm.incoming_msg[int(dev_loc)-1].get() #returns incoming messages. 
                            try: 
                                client_sock.sendall(msg.encode('iso-8859-15')) #sends the msg to the GN 
                            except: 
                                #puts the message back into the DC_push queue if the GN disconnects before the message is sent.
                                comm.DC_push.put(str(dev_loc))
                            #If the device is registered and the push is successful, no need to try again, break the loop
                            break 
                        except Exception as e:
                            #The device dictionary may not be up to date. Need to update and try again.
                            #If the device is still not found after first try, move on.
                            DEVICE_DICT = update_dev_dict() #this function is in the NC_configuration module
                            client_sock.sendall('False'.encode('iso-8859-15'))
                        
            except KeyboardInterrupt as k:
                logger.info("Internal pull server shutting down.")
                
                server.close()
                break
            except Exception as e:
                logger.error("(pull_server) error receiving data: %s" % (str(e)))
                
                    
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
        
 
        for name, function in list(internal_communicator_name2func.items()):
            new_process = multiprocessing.Process(target=function, name=name)
            new_process.start()
            name2process[name]=new_process
            logger.info(name+' has started.')
                

        
    except KeyboardInterrupt as k:
        for name, subhash in list(internal_communicator_name2func.items()):
            logger.info( '(KeyboardInterrupt) shutting down ' + name)
            name2process[name].terminate()
      
        logger.info('Done.')
    
                
