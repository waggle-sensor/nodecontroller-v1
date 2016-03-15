#!/usr/bin/env python

import os, os.path, pika, datetime, sys, logging, argparse, re
import logging.handlers
sys.path.append('../NC/')
#from multiprocessing import Process
from NC_configuration import *
from external_communicator import *
from internal_communicator import *
import urllib2

sys.path.append('../../..')
from waggle_protocol.utilities.pidfile import PidFile, AlreadyRunning





#pika is a bit too verbose...
logging.getLogger('pika').setLevel(logging.ERROR)




loglevel=logging.DEBUG
#loglevel=logging.ERROR


logging.getLogger('external_communicator').setLevel(loglevel)
logging.getLogger('internal_communicator').setLevel(loglevel)

LOG_FILENAME="/var/log/waggle/communications.log"
LOG_FORMAT='%(asctime)s - %(name)s - %(levelname)s - line=%(lineno)d - %(message)s'
pid_file = "/var/run/waggle/communications.pid"

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
    reverse_ssh_port_file = '/etc/waggle/reverse_ssh_port'
    
    
    loop=-1
    while True:
        loop=(loop+1)%20
        CA_ROOT_FILE_exists = os.path.isfile(CA_ROOT_FILE)
        CLIENT_KEY_FILE_exists = os.path.isfile(CLIENT_KEY_FILE)
        CLIENT_CERT_FILE_exists = os.path.isfile(CLIENT_CERT_FILE)
    
        #check if cert server is available
        if not (CA_ROOT_FILE_exists and CLIENT_KEY_FILE_exists and CLIENT_CERT_FILE_exists):
        
            if (loop == 0):
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
                if (loop == 0):
                    logger.error('Have not found certificate files and can not connect to certificate server (%s): %s' % (CERT_SERVER, str(e)))
                    logger.error('Either copy certificate files manually or activate certificate sever.')
                    logger.error('Will silently try to connect to certificate server in 30 second intervals from now on.')
                
                time.sleep(30)
                continue
            
            if html != 'This is the Waggle certificate server.':
                if (loop == 0):
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
    
    
            priv_key_start = "-----BEGIN RSA PRIVATE KEY-----"
            position_rsa_priv_key_start = html.find(priv_key_start)
            if position_rsa_priv_key_start == -1:
                logger.error("Could not parse PEM data from server. (position_rsa_priv_key_start)")
                time.sleep(5)
                continue
            logger.info("position_rsa_priv_key_start: "+str(position_rsa_priv_key_start))
            
            priv_key_end = "-----END RSA PRIVATE KEY-----"
            position_rsa_priv_key_end = html.find(priv_key_end)
            if position_rsa_priv_key_end == -1:
                logger.error("Could not parse PEM data from server. (position_rsa_priv_key_end)")
                time.sleep(5)
                continue
            logger.info("position_rsa_priv_key_end: "+str(position_rsa_priv_key_end))
                
            position_priv_cert_start = html.find("-----BEGIN CERTIFICATE-----")
            if position_priv_cert_start == -1:
                logger.error("Could not parse PEM data from server. (position_priv_cert_start)")
                time.sleep(5)
                continue
            logger.info("position_priv_cert_start: "+str(position_priv_cert_start))
            
            end_cert = "-----END CERTIFICATE-----"
            position_priv_cert_end = html.find(end_cert)
            if position_priv_cert_end == -1:
                logger.error("Could not parse PEM data from server. (position_priv_cert_end)")
                time.sleep(5)
                continue
            logger.info("position_priv_cert_end: "+str(position_priv_cert_end))
            
            
            html_tail = html[position_priv_cert_end+len(end_cert):]
            
            
            
        
            CLIENT_KEY_string = html[position_rsa_priv_key_start:position_rsa_priv_key_end+len(priv_key_end)]
            CLIENT_CERT_string = html[position_priv_cert_start:position_priv_cert_end+len(end_cert)]
        
            PORT_int = re.find("PORT=(\d+)", html_tail)
        
            logger.debug("CLIENT_KEY_FILE: "+CLIENT_KEY_string)
            logger.debug("CLIENT_CERT_FILE: "+CLIENT_CERT_string)
            
            logger.debug("PORT: "+str(PORT_int))
        
            with open(CLIENT_KEY_FILE, 'w') as f:
                f.write(CLIENT_KEY_string)
        
            with open(CLIENT_CERT_FILE, 'w') as f:
                f.write(CLIENT_CERT_string)
            
            
            with open(reverse_ssh_port_file, 'w') as f:
                f.write(str(PORT_int))
        
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
    
    
    
   
    try:
        
        with PidFile(pid_file):
        
            get_certificates()
        
            get_queuename()
    
    
            logger.debug('QUEUENAME: "' + conf['QUEUENAME'] + '"')
        
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
       
                
    except AlreadyRunning as e:
        logger.error(str(e))
        logger.error("Please use supervisorctl to start and stop this script.")    
    except KeyboardInterrupt, k:
        #terminate the external communication processes
        for name, subhash in name2func.iteritems():
            logger.info( '(KeyboardInterrupt) shutting down ' + name)
            name2process[name].terminate()
    except Exception as e:
        logger.error("Error (%s): %s" % ( str(type(e)), str(e)))
       

        
       
