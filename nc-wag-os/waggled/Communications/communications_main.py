#!/usr/bin/env python

import os, os.path, pika, datetime, sys, logging, argparse
import logging.handlers
sys.path.append('../NC/')
#from multiprocessing import Process
from NC_configuration import *
from external_communicator import *
from internal_communicator import *


#pika is a bit too verbose...
logging.getLogger('pika').setLevel(logging.ERROR)




loglevel=logging.DEBUG
#loglevel=logging.ERROR


logging.getLogger('external_communicator').setLevel(loglevel)
logging.getLogger('internal_communicator').setLevel(loglevel)

LOG_FILENAME="/var/log/waggle/communicator/communications_main.log"
LOG_FORMAT='%(asctime)s - %(name)s - %(levelname)s - line=%(lineno)d - %(message)s'

#logging.basicConfig(level=loglevel, format=, filename=LOG_FILENAME)
#logging.basicConfig(level=loglevel, format='%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s', stream=sys.stdout)
logger = logging.getLogger("communications_main.py") #__name__

root_logger = logging.getLogger()
root_logger.setLevel(loglevel)
formatter = logging.Formatter(LOG_FORMAT)


# from: http://www.electricmonk.nl/log/2011/08/14/redirect-stdout-and-stderr-to-a-logger-in-python/
class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger, log_level=logging.INFO, prefix=''):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''
        self.prefix = prefix
 
    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, self.prefix+line.rstrip())

    def flush(self):
        pass


#TODO if the pika_push and pika_pull clients can be combined into one process, add an if statement to that process that checks for initial contact with the cloud
"""

    Communications main starts the internal and external communication processes. 
    It then continuously monitors each of the processes. It restarts the processes of it ever crashes.
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--logging', dest='enable_logging', help='write to log files instead of stdout', action='store_true')
    args = parser.parse_args()
    
        
    if args.enable_logging:
        # 5 times 10MB
        sys.stdout.write('logging to '+LOG_FILENAME+'\n')
        handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=10485760, backupCount=5)
        
        #stdout_logger = logging.getLogger('STDOUT')
        sl = StreamToLogger(logger, logging.INFO, 'STDOUT: ')
        sys.stdout = sl
 
        #stderr_logger = logging.getLogger('STDERR')
        sl = StreamToLogger(logger, logging.ERROR, 'STDERR: ')
        sys.stderr = sl
        
    else:
        handler = logging.StreamHandler(stream=sys.stdout)
        
    handler.setFormatter(formatter)
    root_logger.handlers = []
    root_logger.addHandler(handler)
    
   # sys.stderr.write('hello world')
        
    try:
        #checks if the queuename has been established yet
        #The default file is empty. So, if it is empty, make an initial connection to get a unique queuename.
        connection = None
        if not QUEUENAME:
            logger.debug('QUEUENAME is empty')
            #get the connection parameters
            
            
            
            
            #make the connection
            try:
                connection = pika.BlockingConnection(pika_params)
            except Exception as err:
                logger.error("Could not connect to Beehive server (%s): " % (pika_params.host))
                logger.error(err)
                sys.exit(1)
            
            logger.info("Connected to Beehive server (%s): " % (pika_params.host))
                
            #create the channel
            channel = connection.channel()
            #queue_declare is left empty so RabbitMQ assigns a unique queue name
            
            
            new_queuename = 'node_'+id_generator()
            result = channel.queue_declare(queue=new_queuename)
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
                    logger.warning( 'Process "%s" has crashed. Restarting...' % (name) )
                    new_process = multiprocessing.Process(target=function, name=name)
                    new_process.start()
                    name2process[name]=new_process
                    logger.info(name+' has started.')
                   
                
                
            time.sleep(3)

        #terminate the external communication processes
        for name, subhash in name2func.iteritems():
            logger.info( 'shutting down ' + name)
            name2process[name].terminate()
       
      
        logger.info( 'External communications shut down.')

        
        internal_push_client.terminate()
        internal_pull_client.terminate()
        logger.info( 'Internal communications shut down.' )
       
                
        
    except KeyboardInterrupt, k:
        #terminate the external communication processes
        for name, subhash in name2func.iteritems():
            logger.info( '(KeyboardInterrupt) shutting down ' + name)
            name2process[name].terminate()
       

        
       