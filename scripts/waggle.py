#!/usr/bin/env python


import subprocess
from subprocess import call
import commands, os.path, sys
import re



class Service:
    
    def __init__(self, id):
        self.id = id
    
    def status(self):
        pass
        
    def start(self):
        pass
         
    def stop(self):        
        pass
        
    def restart(self):        
        pass
        
     
class UpStartService(Service):
    
    def status(self):
        status_line = subprocess.Popen(["service", self.id, "status"], stdout=subprocess.PIPE).communicate()[0]
        status_parsed_array = re.findall("(\S+) (\S+),(.*)", status_line)
        if not status_parsed_array:
            status_parsed_array = re.findall("(\S+) (\S+)", status_line)
        
        #print str(status_parsed_array)
        result = status_parsed_array[0][1]
        
        #print result, "\n"
        if "wait" in result:
            return 1
        
        if "running" in result:
            return 0
        
        return -1
        
    def start(self):
        pass
         
    def stop(self):        
        pass
        
    def restart(self):        
        pass   
        
class InitService(Service):

    
        

    def status(self):
        #print "/etc/init.d/"+self.id, "status"
        #call(["/etc/init.d/"+self.id, "status"])
        
        #waggle_wagman start/running, process 640
        status_line = subprocess.Popen(["service", self.id, "status"], stdout=subprocess.PIPE).communicate()[0]
        status_parsed_array = re.findall("(\S+) (\S+),?(.*)")
        
        print str(status_parsed_array)
        result = status_parsed_array[0][1]
        
        #print result, "\n"
        if "wait" in result:
            return 1
        
        if "running" in result:
            return 0
        
        return -1
    
    def start(self):
        call(["/etc/init.d/"+self.id, "start"])
    
    
    def stop(self):
        call(["/etc/init.d/"+self.id, "stop"])
        
    def restart(self):
        call(["/etc/init.d/"+self.id, "restart"])
    

def status_code_2_text(status_int):
    if (status_int == 0):
        status = 'active'
    elif (status_int == 1):
        status = 'inactive'
    elif (status_int == -10):
        status = 'not found'    
    else:
        status = 'unknown'
    return status
    

def overview(services):
    for i, s in enumerate(services):
        
        status_int = s.status()
        
        status = status_code_2_text(status_int)
        
        print "(%d) %s  %s\n" % (i, s.id, status.ljust(10, ' '))



if __name__ == "__main__":
    
    services = []
    services_all = subprocess.Popen(["initctl", "list"], stdout=subprocess.PIPE).communicate()[0]
    for line in services_all.split("\n"):
        if line.startswith("waggle_"):
            #print line
            result = re.findall("^\S+", line)
            if result:
                #print result[0] + "\n"
                services.append(UpStartService(result[0]))
            
    #print str(services) 
    #sys.exit(1)
    
    #services[0].status()
    overview(services)
    
    
            
    try:
        while True:
            
            print "\nList of services: \n"
            overview(services)
            
            
            command = raw_input('\nMain menu\nEnter your command: ')
            #print "got '%s' \n" % (command)
            print ''
            if (not command):
                continue
            if (command == "l"):
                overview(services)
            elif (command == "q"):        
                 sys.exit(0)  
            elif (command in "0123456789"):
                index = int(command)
                s=services[index]
                print "service selected: "+s.id+"\n"
                subcommand = raw_input('1=Start, 2=Stop, 3=Restart, 4=Status, 0=Return:')
                print ''
                if (subcommand == '1'):
                    s.start()
                elif (subcommand == '2'):
                    s.stop()
                elif (subcommand == '3'):
                    s.restart()    
                elif (subcommand == '4'):
                    status_int = s.status()
                    status = status_code_2_text(status_int)
                    print "(%d) %s  %s\n" % (index,  '', status.ljust(10, ' '))
                    
                continue
        
    except KeyboardInterrupt:
        print "exiting..."
    except Exception as e:
        print "error: "+str(e)
