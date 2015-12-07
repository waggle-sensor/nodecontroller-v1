#!/usr/bin/env python

import os, os.path, pika, datetime, sys, logging, argparse
import logging.handlers
sys.path.append('../NC/')
#from multiprocessing import Process
from NC_configuration import *
from external_communicator import *
from internal_communicator import *
import urllib2

#pika is a bit too verbose...
logging.getLogger('pika').setLevel(logging.ERROR)




loglevel=logging.DEBUG
#loglevel=logging.ERROR


logging.getLogger('external_communicator').setLevel(loglevel)
logging.getLogger('internal_communicator').setLevel(loglevel)

LOG_FILENAME="/var/log/waggle/communications.log"
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



def createDirForFile(file):
    file_dir = os.path.dirname(file)
    if not os.path.exists(file_dir):
        try:
            os.makedirs(file_dir)
        except Exception as e:
            logger.error("Could not create directory '%s' : %s" % (file_dir,str(e)) )
            sys.exit(1)



def get_certificates():
    
    while True:
        CA_ROOT_FILE_exists = os.path.isfile(CA_ROOT_FILE)
        CLIENT_KEY_FILE_exists = os.path.isfile(CLIENT_KEY_FILE)
        CLIENT_CERT_FILE_exists = os.path.isfile(CLIENT_CERT_FILE)
    
        #check if cert server is available
        if not (CA_ROOT_FILE_exists and CLIENT_KEY_FILE_exists and CLIENT_CERT_FILE_exists):
        
            if not CA_ROOT_FILE_exists:
                logger.info("File '%s' not found." % (CA_ROOT_FILE))
            if not CLIENT_KEY_FILE_exists:
                logger.info("File '%s' not found." % (CLIENT_KEY_FILE))
            if not CLIENT_CERT_FILE_exists:
                logger.info("File '%s' not found." % (CLIENT_CERT_FILE))
            try:
                response = urllib2.urlopen(CERT_SERVER)
                html = response.read()
            except Exception as e:
                logger.error('Could not connect to certificate server: '+str(e))
                time.sleep(5)
                continue
            
            if html != 'This is the Waggle certificate server.':
                logger.error("Did not find certificate server.")
                time.sleep(5)
                continue
        else:
            logger.info("All certificate files found.")
            break
            
        # make sure certficate files exist.
        if not CA_ROOT_FILE_exists:
            createDirForFile(CA_ROOT_FILE)
            certca_url= CERT_SERVER+"/certca"
            logger.info("trying to get server certificate from certificate server %s..." % (certca_url))
            try:
                response = urllib2.urlopen(certca_url)
                html = response.read()
            except Exception as e:
                logger.error('Could not connect to certificate server: '+str(e))
                time.sleep(5)
                continue
            
            if html.startswith( '-----BEGIN CERTIFICATE-----' ) and html.endswith('-----END CERTIFICATE-----'):
                logger.info('certificate downloaded')
            else:
                logger.error('certificate parsing problem')
                #logger.debug('content: '+str(html))
                time.sleep(5)
                continue
        
            with open(CA_ROOT_FILE, 'w') as f:
                f.write(html)
    
            logger.debug("File %s written." % (CA_ROOT_FILE))
        
        if not (CLIENT_KEY_FILE_exists and CLIENT_CERT_FILE_exists):
            createDirForFile(CLIENT_KEY_FILE)
            createDirForFile(CLIENT_CERT_FILE)
            cert_url= CERT_SERVER+"/node?"+NODE_ID
            logger.info("trying to get node key and certificate from certificate server %s..." % (cert_url))
            try:
                response = urllib2.urlopen(cert_url)
                html = response.read()
            except Exception as e:
                logger.error('Could not connect to certificate server: '+str(e))
                time.sleep(5)
                continue
    
            split_region = html.find("-----END RSA PRIVATE KEY-----\n-----BEGIN CERTIFICATE-----")
            if split_region == -1:
                logger.error("Could not parse PEM data from server.")
                time.sleep(5)
                continue
            
            logger.info("Found split: "+str(split_region))
        
            CLIENT_KEY_string = html[0:split_region+30]
            CLIENT_CERT_string = html[split_region+30:]
        
            logger.debug("CLIENT_KEY_FILE: "+CLIENT_KEY_string)
            logger.debug("CLIENT_CERT_FILE: "+CLIENT_CERT_string)
        
            with open(CLIENT_KEY_FILE, 'w') as f:
                f.write(CLIENT_KEY_string)
        
            with open(CLIENT_CERT_FILE, 'w') as f:
                f.write(CLIENT_CERT_string)
        
            logger.info("Files '%s' and '%s' have been written" % (CLIENT_KEY_FILE, CLIENT_CERT_FILE))

def get_queuename():
    sleep_duration = 10
    #checks if the queuename has been established yet
    #The default file is empty. So, if it is empty, make an initial connection to get a unique queuename.
    while not conf['QUEUENAME']:
        logger.debug('QUEUENAME is empty')
        #get the connection parameters
        
        #make the connection
        connection = None
        try:
            connection = pika.BlockingConnection(pika_params)
        except Exception as e:
            logger.error("Could not connect to Beehive server (%s): %s" % (pika_params.host, str(e)))
            time.sleep(sleep_duration)
            continue
    
        logger.info("Connected to Beehive server (%s): " % (pika_params.host))
            
        #create the channel
        channel = connection.channel()
        #queue_declare is left empty so RabbitMQ assigns a unique queue name
        
        
        new_queuename = 'node_'+id_generator()
        try:
            result = channel.queue_declare(queue=new_queuename)
        except Exception as e:
            logger.error("channel.queue_declare: "+str(e))
            time.sleep(sleep_duration)
            continue
        #get the name of the randomly assigned queue
        queuename = result.method.queue
        #close the connection
        connection.close()
        
        if not queuename:
            logger.debug('got no queuename')
            time.sleep(sleep_duration)
            continue
        
        logger.info("Reported queuename: " + queuename)
        #strip 'amq.gen-' from queuename 
        #junk, queuename = queuename.split('-', 1)
        
        #write the queuename to a file
        with open('/etc/waggle/queuename', 'w') as file_: 
            file_.write(queuename)

        logger.debug('wrote new queuename "' + queuename+  '" to /etc/waggle/queuename')
        
        conf['QUEUENAME'] = queuename
        break
        

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
    
    
    get_certificates()
        
    get_queuename()
    
    
    logger.debug('QUEUENAME: "' + conf['QUEUENAME'] + '"')
   
    try:
        
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
       

        
       
