#!/usr/bin/env python3

from multiprocessing import Queue
#from daemon import Daemon
import sys, os, os.path, time, atexit, socket, datetime, argparse
sys.path.append('../../../')
from waggle.protocol.PacketHandler import *
sys.path.append('../NC/')
from NC_configuration import *
sys.path.append('../NC/')
from msg_handler import msg_handler
from glob import glob
import logging, logging.handlers
import signal


from waggle.protocol.utils.pidfile import PidFile, AlreadyRunning



""" 
    The Data Cache stores messages between the nodes and the cloud. The main function is a unix socket server. The internal and external facing communication classes connect to
    the data cache to push or pull messages. The data cache consists of two buffers, which are matrixes of queues. Each queue cooresponds to a device location and message priority within the matrix. 
    The data cache stores messages in the queues until the available memory runs out. When the number of messages exceeds the available memory, the messages queues are cleared and the messages are written to a file. 
"""

#TODO make improvements. Suggestions for improvements are written as TODOs

loglevel=logging.DEBUG
LOG_FILENAME="/var/log/waggle/data_cache_logging.log"
LOG_FORMAT='%(asctime)s - %(name)s - %(levelname)s - line=%(lineno)d - %(message)s'
pid_file = "/var/run/waggle/data_cache.pid"

logger = logging.getLogger(__name__)
logger.setLevel(loglevel)



root_logger = logging.getLogger()
root_logger.setLevel(loglevel)
formatter = logging.Formatter(LOG_FORMAT)

handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)

root_logger.handlers = []
root_logger.addHandler(handler)

dc = None

   #dummy variables. These buffers are created when the data cache starts.

stop_process = False



    
    
def signal_term_handler(signal, frame):
    logger.debug('got SIGTERM')
    
    if dc:
        logger.debug('execute dc.stop()')
        dc.stop()
    # Can't exit here, the flush fiunction has to exit using variable "stop_process" 
    #sys.exit(0)
 
# this would interrupt IO. Need to run everything in separate thread/process 
def signal_info_handler(signal, frame):
    logger.debug('got SIGUSR1')
    #print "status: ", str(dc.get_status())

signal.signal(signal.SIGTERM, signal_term_handler)

#signal.signal(signal.SIGUSR1, signal_info_handler)
  
            
         


class DataCache:
    def __init__(self):
        #self.data = []
        
        self.socket_file = '/tmp/Data_Cache_server'
        
        self.incoming_bffr = []

        self.outgoing_bffr = []

        self.flush = 0 #value that indicates if the DC is flushing or not
        self.msg_counter = 0 #keeps track of total messages in queues
        #If the data cache flushed messages to files, this stores the the current outgoing file that messages are being read from
        self.outgoing_cur_file = '' #empty string if there are no files
        #If the data cache flushed messages to files, this stores a list of current files for each device 
        self.incoming_cur_file =  ['', '', '', '', ''] #empty string if there are no files
        
        self.outgoing_available_queues = list() 
        self.incoming_available_queues = list()
    
    def run(self):
        
        logger.info("Starting DataCache...")

    
        #Each buffer is a matrix of queues for organization and indexing purposes.
        #make incoming buffer
        self.incoming_bffr = self.make_bffr(len(PRIORITY_ORDER))
        #make outgoing buffer 
        self.outgoing_bffr = self.make_bffr(len(PRIORITY_ORDER))
    
       
        #the main server loop
        while True:
            
            #indicates that the server is flushing the buffers. Shuts down the server until the all queues have been written to a file
            while self.flush ==1:
                logger.debug("Cache is in flush state")
                time.sleep(1)
            if os.path.exists(self.socket_file): #checking for the file
                os.remove(self.socket_file)
            logger.debug("Opening server socket...")
        
            #creates a UNIX, STREAMing socket
            server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) # TODO should this not be a class variable ?
            server_sock.bind(self.socket_file) #binds to this file path
        
            #become a server socket and start listening for clients
            server_sock.listen(6)
            
            while True:
               
                if self.flush==1: #shuts down the server until the all queues have been written to a file
                    logger.debug('Server flush!')
                
                    server_sock.close()
                    os.remove(self.socket_file)
                    logger.debug('Server flush closed socket')
                
                    break
            
                #accept connections from outside
                try:
                    client_sock, address = server_sock.accept()
                except KeyboardInterrupt:
                    logger.info("Shutdown requested...exiting")
                    self.stop()
                    sys.exit(0)
                except Exception as e:
                    logger.info("server_sock.accept: "+str(e))
                    self.stop()
                    sys.exit(1)
                    
                
                
                try:
                    data = client_sock.recv(2048) #arbitrary
                    
                    if logger.isEnabledFor(logging.DEBUG):
                        if data != '|o'.encode('iso-8859-1'):
                            logger.debug('(DataCache) received data.')
                    if not data:
                        break
                    else:
                        #'Flush' means that there is an external flush request or if WagMan is about to shut down the node controller
                        if data == 'Flush'.encode('iso-8859-1'):
                            #flush all stored messages into files
                            logger.debug('External flush request made.')
                        
                            self.DC_flush()
                            
                            
                            if stop_process:
                                logger.info("DC has been flushed. Process will stop now.")
                                sys.exit(0)
                            
                                
                        #Indicates that it is a pull request ( somebody want data from the DC)
                        elif data[0] == ord('|'): #TODO This could be improved if there is a better way to distinguish between push and pull requests and from incoming and outgoing requests
                            logger.debug('Somebody wants data')
                            #data, dest = data.decode('iso-8859-1').split('|', 1) #splits to get either 'o' for outgoing request or the device location for incoming request
                            dest = data[1:]
                            if dest != 'o'.encode('iso-8859-1'):
                                logger.debug('Somebody wants data, without o')
                                msg = self.incoming_pull(int(dest)) #pulls a message from that device's queue
                                if not msg:
                                    logger.debug("no message")
                                    msg = 'False'.encode('iso-8859-1')
                                else:
                                    logger.debug("incoming_pull message: %s" %(msg))
                                try:
                                    client_sock.sendall(msg) #sends the message
                                except:
                                    #pushes it back into the incoming queue if the client disconnects before the message is sent
                                    try: #Will pass if data is a pull request instead of a full message 
                                        #TODO default msg_p is 5 for messages pushed back into queue. Improvement recommended.
                                        incoming_push(int(dest),5, msg) 
                                    except: 
                                        pass
                            else:
                                logger.debug('Somebody wants data, using o')
                                msg = self.outgoing_pull() #pulls the highest priority message
                                if not msg: 
                                    msg = 'False'.encode('iso-8859-15')
                                    logger.debug("have no message for external_client_pull")
                                else:
                                    logger.debug("sending message to external_client_pull, length %d" % (len(msg)))
                                    
                                try:
                                    client_sock.sendall(msg) #sends the message
                                except Exception as e:
                                    logger.error("client_sock.sendall: "+str(e))
                                    #pushes it back into the outgoing queue if the client disconnects before the message is sent
                                    try:#Will pass if data is a pull request instead of a full message
                                        #TODO default msg_p is 5 for messages pushed back into queue. Improvement recommended.
                                        self.outgoing_push(int(dest),5,msg)
                                    except Exception as e: 
                                        logger.error("outgoing_push: "+str(e))
                                        pass
                    
                            
                        
                        else:
                            # somebody sends data to the DataCache
                            #logger.debug("datacache got: \""+str(data)+"\"")
                            logger.debug('Somebody sends data')
                            try:
                                header = get_header(data) #uses the packet handler function get_header to unpack the header data from the message
                                flags = header['flags'] #extracts priorities
                                order = flags[2] #lifo or fifo
                                msg_p = flags[1] 
                                recipient_int = header['r_uniqid'] #gets the recipient ID
                                sender_int = header['s_uniqid']
                                logger.debug("sender_int: %s recipient_int: %s" % (sender_int, recipient_int))
                                sender = nodeid_int2hexstr(sender_int)
                                recipient = nodeid_int2hexstr(recipient_int)
                                logger.debug("sender: %s recipient: %s NODE_ID: %s" % (sender, recipient, NODE_ID))
                                for i in range(2): #loops in case device dictionary is not up-to-date
                                    # message for the cloud
                                    if recipient_int == 0: #0 is the default ID for the cloud. Indicates an outgoing push.
                                        try: 
                                            dev_loc = DEVICE_DICT[sender] #looks up the location of the sender device ("location" refers to priority!)
                                        except KeyError as e: 
                                            logger.error("Rejecting message. Sender %s is unknown: %s" % ( sender, str(e)) )
                                            continue  # do not send message from unknown sender
                                        
                                        try:     
                                            if order==False: #indicates lifo. lifo has highest message priority
                                                msg_p=5
                                            #pushes the message into the outgoing buffer to the queue corresponding to the device location and message priority
                                            self.outgoing_push(int(dev_loc), msg_p, data)
                                            #If the device is registered and the push is successful, no need to try again, break the loop
                                            
                                            break 
                                        except Exception as e: 
                                            logger.error("outgoing_push2: "+str(e))
                                            #The device dictionary may not be up to date. Need to update and try again.
                                            #If the device is still not found after first try, move on.
                                            update_dev_dict() #this function is in NC_configuration.py
                                        
                                    #indicates an incoming push
                                    # message for the nodecontroller
                                    elif recipient == NODE_ID or recipient_int == 1:
                                        try:
                                            #An error will occur if a guestnode registers and then tries to deregister before the device dictionary has been updated
                                            #This may be unlikely but is still possible
                                            #If that occurs, need to update the device dictionary and try again
                                            msg_handler(data,DEVICE_DICT)
                                            break #break the loop if this is successful
                                        except Exception as e:
                                            logger.error(e)
                                            update_dev_dict()
                                    # message for a guestnode ?
                                    else:
                                        try:
                                            dev_loc = DEVICE_DICT[recipient] #looks up the location of the recipient device
                                            #If the device is registered and the push is successful, no need to try again, break the loop
                                            self.incoming_push(int(dev_loc),msg_p,data)
                                            break
                                        except Exception as e: 
                                            #The device dictionary may not be up to date. Need to update and try again.
                                            #If the device is still not found after first try, move on.
                                            update_dev_dict()
                            except Exception as e:
                                logger.error('Message corrupt. Will not store in data cache.')
                                logger.error(e)
                    
                except KeyboardInterrupt as k:
                    logger.info("Data Cache server shutting down...")
                    self.stop()
                    continue
                    
            #server_sock.close()
            #os.remove(self.socket_file)
            #break
        if os.path.exists(self.socket_file): #checking for the file for a smooth shutdown
            server_sock.close()
            os.remove(self.socket_file)


    def stop(self):
        stop_process = True
        self.DC_flush()
        
        logger.info("DC has been flushed. Process will stop now.")
        sys.exit(0)   
        
        #try:
        #    logger.debug('Flushing data cache....')
        #    self.external_flush()
            #The data cache needs time to flush the messages before stopping the process
            #time.sleep(5)
            #Daemon.stop(self) 
        #except Exception as e:
        #   logger.error(e)

    def external_flush(self):
        """
            This function is called to force a flush of the data cache from an external source (i.e. before a system reboot). 
            It connects to the server socket of the data cache to request a flush. 
        """
         #connect to DC and send 'Flush'
        if os.path.exists(self.socket_file):
            client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                client_sock.connect(self.socket_file)
                client_sock.sendall('Flush'.encode('iso-8859-15'))
                client_sock.close()
            except Exception as e:
                logger.error(e)
                client_sock.close()
            logger.debug("Sent flush command.")
        else: 
            logger.debug('Data cache running?')
    

    def outgoing_push(self,dev, msg_p, msg): 
        """
            Function that pushes outgoing messages into the outgoing buffer.
        
            :param int dev: Specifies the device location in the matrix.
            :param int msg_p: Specifies the message priority location in the matrix
            :param int self.msg_counter: Keeps track of the number of total messags currently being stored in the buffers.
            :param int flush: Value indicating if the data cache needs to flush the buffers into files.
        """ 
        logger.debug("outgoing_push: dev=%d msg_p=%d" % (dev, msg_p))
        #If the msg counter is greater than or equal to the available memory, flush the outgoing queues into a file
        if self.msg_counter>= AVAILABLE_MEM:
        
            #Calls the data cache flush method and passes in the neccessary params
            logger.debug("(outgoing_push) flush because of self.msg_counter>= AVAILABLE_MEM")
            self.DC_flush() #Flushes all messages into a file
            self.msg_counter = 0 #resets the message counter after all buffers have been saved to a file
    
        #Increments the self.msg_counter by 1 each time a message is pushed into the data cache
        self.msg_counter += 1 
        logger.debug("self.msg_counter: "+str(self.msg_counter))
        try:
            #pushes the message into the queue at the specified location in the matrix
            self.outgoing_bffr[(dev - 1)][(msg_p - 1)].put(msg)
        
            #adds the queue to the list of available queues
            try:
                self.outgoing_available_queues.index((dev, msg_p)) #throws an error if this is not already in the list
            except: 
                self.outgoing_available_queues.append((dev, msg_p)) #prevents duplicates
        except:
            logger.error('Outgoing push unable to store in data cache...') #TODO Should an error message be sent back to the recipient?
       
    def incoming_push(self,device, msg_p, msg):
        """ 
            Function that pushes incoming messages to the incoming buffer.
        
            :param int dev: Specifies the device location in the matrix.
            :param int msg_p: Specifies the message priority location in the matrix
            :param int self.msg_counter: Keeps track of total messages in the data cache.
            :param int flush: Value indicating if the data cache needs to flush the buffers into files.
        """ 
        #print 'msg counter: ',self.msg_counter
        #print 'available mem: ', AVAILABLE_MEM
        #if the msg counter is greater than or equal to the available memory, flush the buffers into files
        if self.msg_counter >= AVAILABLE_MEM: 
            #Calls the data cache flush method
            logger.debug("(incoming_push) flush because of (self.msg_counter >= AVAILABLE_MEM)")
            self.DC_flush()
            self.msg_counter = 0 #resets the message counter after all buffers have been saved to a file
        else:
            pass 
        #increments the counter by 1 each time a message is put into the buffer
        self.msg_counter += 1
    
        #pushes the message into the queue at the specified location in the matrix
        self.incoming_bffr[device - 1][msg_p - 1].put(msg)
    
        #adds the queue to the list of available queues
        try:
            self.incoming_available_queues.index(device) #checks if the device is already in the list #TODO improve this
        except:
            self.incoming_available_queues.append(device) #adds it to the list if it is not already there

    def outgoing_pull(self):
        """ 
            Function that retrieves and removes outgoing messages from the outgoing buffer. Retrieves the highest priority messages first. Highest priority messages are determined based on message priority and device priority.
        
            :param int self.msg_counter: Keeps track of total messages in the data cache.
            :rtype string: Returns a packed message or 'False' if no messages are available. 
        """ 
    
        #TODO implement fairness, avoid starvation
        #TODO might want to find a better way to remove empty queues from list 
    
    
        #continues until a message is sent. 
        #Neccessary to check for empty queues whose index has not yet been removed from the list or files whose messages have all been read and sent
        #while True:
    
        #are there outgoing messages stored as files?
        #if so, those need to be sent to the cloud first without needing to load all messages from the file and taking up too much RAM
        #so, send the messages one by one using a file generator object.
        #when all messages have been read from file and sent to cloud, close and delete that file from the directory.
        outgoing_msg_files = glob('/var/dc/outgoing_msgs/*')
        if len(outgoing_msg_files) > 0 and self.flush == 0: #prevents the flush from pulling messages from files
            logger.debug('Getting messages from /var/dc/outgoing_msgs/')
            #is there a file generator object already stored as the current file?
            if self.outgoing_cur_file == '':
                #print 'cur_file is empty string.'
                #set the first file in the outgoing_stored directory as the current file generator object
                logger.debug('opening file %s' % (outgoing_msg_files[0]))
                self.outgoing_cur_file = open(outgoing_msg_files[0]) 
                #print 'opened file'
                try: 
                    #print 'trying to read from file'
                    msg = next(self.outgoing_cur_file).strip() #reads the next message in file, strips the \n
                    #print 'returning msg'
                    return msg
                except:
                    self.outgoing_cur_file.close() #close the file if stop iterator error occurs
                    if os.path.isfile(self.outgoing_cur_file.name): #make sure the file exists
                        os.remove(self.outgoing_cur_file.name)#delete the file
                    self.outgoing_cur_file = '' #reset to empty string
            else:
                logger.debug('reading from exsiting file handle (data from /var/dc/outgoing_msgs/*)')
                try: 
                    msg = next(self.outgoing_cur_file).strip() #reads the next message in file, strips the \n
                    return msg
                except:
                    self.outgoing_cur_file.close() #close the file if stop iterator error occurs
                    if os.path.isfile(self.outgoing_cur_file.name): #make sure the file exists
                        os.remove(self.outgoing_cur_file.name) #delete the file
                    self.outgoing_cur_file = '' #reset to empty string
                
        #If there are no messages stored as files, pull messages from the queues
        else:
            logger.debug('trying to get message from queue...')
            #Are there any messages available?
            if len(self.outgoing_available_queues) == 0: #no messages available
                #logger.debug('No messages available.')
                return None 
            else:
                #Calls the function that returns the highest priority tuple in the list
                cache_index = self.get_priority() #returns the index of the highest priority queue in fifo buffer
                
                sender_p, msg_p = cache_index
                logger.debug("sender_p: %s msg_p: %s" % (str(sender_p), str(msg_p) ))
                
                current_q = self.outgoing_bffr[sender_p - 1][msg_p - 1]
            
                #checks if the queue is empty
                if current_q.empty():
                    logger.debug("current_q.empty")
                    #removes it from the list of available queues 
                    self.outgoing_available_queues.remove(cache_index) 
                else:
                    logger.debug("getting message from current_q, size: %d" % (current_q.qsize()))
                    self.msg_counter -= 1 #decrements the counter by 1
                    return current_q.get()
                    
        return None
                        
        
    def incoming_pull(self,dev):
        """ 
            Function that retrieves and removes incoming messages from the incoming buffer. Searches through all of the message priority queues for the specified device to return the highest priority message first. 
        
            :param int dev: Specifies the device location in the matrix.
        """ 
    
        #continues until something is returned. 
        #Neccessary to check for files whose messages have all been read and sent but have not yet been deleted
        while True:
            #are there incoming messages stored as files for the specified dev?
            #if so, those need to be sent first without needing to load all messages from the file and taking up too much RAM
            #so, send the messages one by one using a file generator object.
            #when all messages have been read from file and sent to device, close and delete that file from the directory.
            incoming_msg_files = glob('/var/dc/incoming_msgs/' + str(dev) + '/*')
            if len(incoming_msg_files) > 0 and self.flush == 0: #only pulls messages from file if DC is not flushing
                #is there a file generator object already stored as the current file?
                if self.incoming_cur_file[dev - 1] == '':
                    #set the first file in the incoming_stored/dev directory as the current file generator object
                    self.incoming_cur_file[dev -1] = open(incoming_msg_files[0]) 
                    try: 
                        msg = next(self.incoming_cur_file[dev -1]).strip() #reads the next message in file, strips the \n
                        return msg
                        
                    except:
                        self.incoming_cur_file[dev -1].close() #close the file if stop iterator error occurs
                        if os.path.isfile(self.incoming_cur_file[dev -1].name): #make sure the file exists
                            os.remove(self.incoming_cur_file[dev -1].name)#delete the file
                        self.incoming_cur_file[dev -1] = '' #reset to empty string
                else:
                    try: 
                        msg = next(self.incoming_cur_file[dev -1]).strip() #reads the next message in file, strips the \n
                        return msg
                        
                    except:
                        self.incoming_cur_file[dev -1].close() #close the file if stop iterator error occurs
                        if os.path.isfile(self.incoming_cur_file[dev -1].name): #make sure the file exists
                            os.remove(self.incoming_cur_file[dev -1].name)#delete the file
                        self.incoming_cur_file[dev -1] = '' #reset to empty string
        
            #if no messages are stored in files, check for messages in queues
            else:
                try: 
                    #checks to see if there are messages for the device
                    #results in an error if that dev isn't in the list
                    self.incoming_available_queues.index(dev) #TODO Probably need a better way to do this
                    msg = 'False' #default 
                    for i in range(4,-1,-1): # loop to search for messages starting with highest priority
                        if self.incoming_bffr[dev - 1][i].empty(): #checks for an empty queue 
                            pass #do nothing
                        else: 
                            #decrements the counter by 1 each time a message is removed
                            self.msg_counter -= 1 
                            msg = self.incoming_bffr[dev - 1][i].get() #sets to message and breaks the loop
                            break
                    #if the message is still false (i.e. no messages are actually available for that device), remove dev from list
                    if msg == 'False':
                        self.incoming_available_queues.remove(dev)
                    return msg
                    
                except:
                    #returns false if no messages are available
                    return None
                    
           
    def DC_flush(self):
        """ 
            Function that temporary closes the Data Cache server to write the outgoing and incoming queues into files.
            This function is called when the data cache reaches its maximum number of messages it can store in RAM or before the NC is shutdown by WagMan
        """ 
        self.flush = 1
        cur_date = str(datetime.datetime.now().strftime('%Y%m%d%H:%M:%S'))
        logger.debug('Flushing at ' + cur_date)
        try:
        
            filename = '/var/dc/outgoing_msgs/' + cur_date #file name is date of flush
            f = open(filename, 'w')
            logger.debug('Flushing outgoing')
            while True: #write all outgoing messages to outgoing file
                #messages are written to file with highest priority at the top
                msg = self.outgoing_pull() #returns false when all queues are empty
                if not msg: #no more messages available. break and close file
                    break
                else:
                    #write the message to the file
                    f.write(msg + '\n') 
            f.close()
            logger.debug('Flushing incoming')
            for i in PRIORITY_ORDER: #write all incoming messages to file
                #each device has a separate folder. This prevents needing to loop through all messages or all files to find messages for only the connected devices.
                #TODO Change this to /etc/waggle/dc/outgoing or something
                pathname = '/var/dc/incoming_msgs/' + str(i) + '/' #set the path
                logger.debug('pathname: '+ pathname)
                if not os.path.exists(pathname): #make sure the directory exists
                    os.makedirs(pathname)
                filename = pathname + cur_date #set the file name to the date and time of flush
                f = open(filename, 'w')
                while True:
                    #for each device, messages are stored with highest priority on the top of the file
                    msg = self.incoming_pull(i)
                    if not msg:  #No more messages available. break and close file.
                        f.close()
                        break
                    elif msg =='None': #No messages currently available for device. Close and remove file
                        f.close()
                        if os.path.isfile(f.name):
                            os.remove(f.name)
                        break
                    else:
                        #write the message to the file
                        f.write(msg + '\n')
                        
            if not stop_process:        
                self.flush = 0 #restart server
                logger.debug('Data cache restarted')
        except Exception as e:
            logger.error(e)

    def get_status(self):
    #TODO This doesn't work. Needs to be a unix socket to communicate with the data cache as it is running. 
    #TODO Socket needs to send a status request message and data cache needs to respond with Data_cache.self.msg_counter
        """
    
            Function that returns the number of messages currently stored in the data cache. 
    
        """
    
        return self.msg_counter


    def make_bffr(self, length):
        """ 
            Generates a buffer, which is a matrix containing queues. 
    
            :param int length: Specifies the number of rows in the matrix
            :rtype list buff: The matrix containing queues
        """
        buff = []
        #device priority
        for i in range(length):
            buff_in = []
            for j in range(5): #Assuming that messages can only have priority 1-5
                buff_in.append(Queue())
            buff.append(buff_in)
        return buff
                

    def get_priority(self):
        """ 
            Function that finds the highest priority queue in the list. Highest priority is determined by comparing message priority and device priority.
        
            :rtype: tuple(device_priority, message_priority) or string 'False'
        """ 
        #returns False if there are no messages available
        if len(self.outgoing_available_queues) == 0:
            return 'False'
        else:
            highest_de_p = PRIORITY_ORDER[(len(PRIORITY_ORDER)-1)] #sets it to the lowest priority as default
            highest_msg_p = 0 #default
            for i in range(len(self.outgoing_available_queues)): #i has to be an int
                device_p, msg_p = self.outgoing_available_queues[i]
                if msg_p >= highest_msg_p: #if the msg_p is higher or equal to the current highest
                    if PRIORITY_ORDER.index(device_p) < PRIORITY_ORDER.index(highest_de_p): #and the device_p is higher
                        highest_de_p = device_p #then that element becomes the new highest_p
                        highest_msg_p = msg_p
                    else: #but, if the device_p is lower, the element should still be the new highest_p that gets checked next
                        highest_de_p = device_p #then that element becomes the new highest_p
                        highest_msg_p = msg_p
                else:
                    pass
            return (highest_de_p, highest_msg_p)


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--logging', dest='enable_logging', help='write to log files instead of stdout', action='store_true')
    parser.add_argument('--force', dest='force', help='kill other processes and start', action='store_true')
    args = parser.parse_args()
    
        
    if args.enable_logging:
        # 5 times 10MB
        sys.stdout.write('logging to '+LOG_FILENAME+'\n')
        log_dir = os.path.dirname(LOG_FILENAME)
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=1485760, backupCount=5)
    
        handler.setFormatter(formatter)
        root_logger.handlers = []
        root_logger.addHandler(handler)
   
        
    
    try:
        
        with PidFile(pid_file, force=args.force, name=os.path.basename(__file__) ):
            dc = DataCache()
    
            dc.run()
            
    except AlreadyRunning as e:
        logger.error(str(e))
        logger.error("Please use supervisorctl to start and stop this script.")    
    except KeyboardInterrupt as k:
        #terminate the external communication processes
        #for name, subhash in name2func.iteritems():
        #    logger.info( '(KeyboardInterrupt) shutting down ' + name)
        #    name2process[name].terminate()
        logger.info('exiting...')
    except Exception as e:
        logger.error("Error (%s): %s" % ( str(type(e)), str(e)))
  
    #lists keeping track of which queues currently have messages stored in them
    
