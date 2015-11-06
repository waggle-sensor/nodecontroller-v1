#!/usr/bin/env python

import os, os.path, pika, datetime, sys, logging
sys.path.append('../NC/')
#from multiprocessing import Process
from NC_configuration import *
from external_communicator import *
from internal_communicator import *



logging.getLogger('pika').setLevel(logging.ERROR)

#loglevel=logging.DEBUG
loglevel=logging.DEBUG

#logging.basicConfig(level=loglevel, format='%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s', filename="/var/log/waggle/communicator/communications_main.log")
logging.basicConfig(level=loglevel, format='%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

#handler
#handler = logging.FileHandler('')
#handler.setLevel(logging.DEBUG)

#formatter
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#handler.setFormatter(formatter)

# add the handlers to the logger
#logger.addHandler(handler)


#TODO if the pika_push and pika_pull clients can be combined into one process, add an if statement to that process that checks for initial contact with the cloud
"""

    Communications main starts the internal and external communication processes. 
    It then continuously monitors each of the processes. It restarts the processes of it ever crashes.
"""

if __name__ == "__main__":
    try:
        #checks if the queuename has been established yet
        #The default file is empty. So, if it is empty, make an initial connection to get a unique queuename.
        if not QUEUENAME:
            logger.debug('QUEUENAME is empty')
            #get the connection parameters
            params = pika.connection.URLParameters(CLOUD_ADDR)
            #make the connection
            connection = pika.BlockingConnection(params)
            #create the channel
            channel = connection.channel()
            #queue_declare is left empty so RabbitMQ assigns a unique queue name
            result = channel.queue_declare()
            #get the name of the randomly assigned queue
            queuename = result.method.queue
            #close the connection
            connection.close()
            
            #strip 'amq.gen-' from queuename 
            junk, queuename = queuename.split('-', 1)
            
            #write the queuename to a file
            with open('/etc/waggle/queuename', 'w') as file_: 
                file_.write(queuename)
    
            logger.debug('wrote new queuename "' + queuename+  '" to /etc/waggle/queuename')
        else:
            logger.debug('QUEUENAME: "' + QUEUENAME + '"')
       
        
        
        name2process={}
        
        name2func = dict(external_communicator_name2func.items() + internal_communicator_name2func.items())
        
        for name, function in name2func.iteritems():
            new_process = multiprocessing.Process(target=function, name=name)
            new_process.start()
            name2process[name]=new_process
            logger.info(name+' has started.')
        
        time.sleep(3)
        
  
        
        
        while True:
            
            for name, function in name2func.iteritems():
                if not name2process[name].is_alive():
                    logger.warning( name + ' has crashed. Restarting...', str(datetime.datetime.now()) )
                    new_process = multiprocessing.Process(target=function, name=name)
                    new_process.start()
                    name2process[name]=new_process
                    logger.info(name+' has started.')
                   
                
                
            time.sleep(3)

        #terminate the external communication processes
        for name, subhash in name2func.iteritems():
            logger.info( 'shutting down ' + name)
            name2process[name].terminate()
       
       # external_push_client.terminate()
       # external_pull_client.terminate()
        logger.info( 'External communications shut down.')

        #terminate the internal communication processes
        #pull_serv.terminate()
        #push_serv.terminate()
        internal_push_client.terminate()
        internal_pull_client.terminate()
        logger.info( 'Internal communications shut down.' )
       
                
        
    except KeyboardInterrupt, k:
        #terminate the external communication processes
        for name, subhash in name2func.iteritems():
            logger.info( '(KeyboardInterrupt) shutting down ' + name)
            name2process[name].terminate()
        #pull_pika.terminate()
        #push_pika.terminate()
       # external_push_client.terminate()
       # external_pull_client.terminate()
       # print 'External communications shut down.'
        
        #terminate the internal communication processes
        #pull_serv.terminate()
        #push_serv.terminate()
        #internal_push_client.terminate()
        #internal_pull_client.terminate()
        #print 'Internal communications shut down.'

        
       