#!/usr/bin/env python



from subprocess import call
import commands


class Service:

    def __init__(self, type, id):
        self.type = type
        self.id = id
        


    def status(self):
        #print "/etc/init.d/"+self.id, "status"
        #call(["/etc/init.d/"+self.id, "status"])
        result = commands.getstatusoutput("/etc/init.d/"+self.id+" status")
        #print result, "\n"
        if "Stopped" in result:
            return 0
        
        if "Running" in result:
            return 0
        
        return -1
    
    def start(self):
        call(["/etc/init.d/"+self.id, "start"])
    
    
    def stop(self):
        call(["/etc/init.d/"+self.id, "stop"])
        
    def restart(self):
        call(["/etc/init.d/"+self.id, "restart"])
    


def overview(services):
    for i, s in enumerate(services):
        
        status_int = s.status()
        
        if (status_int == 0):
            status = 'active'
        elif (status_int == 1):
            status = 'inactive'
        else:
            status = 'unknown'
        
        print "(%d) %s  %s\n" % (i, s.id.ljust(max_length+4, ' '), status.ljust(10, ' '))



if __name__ == "__main__":
    services = []
    
    max_length = 0
    for file in ['data_cache.sh', 'communications.sh', 'start_sensor.sh']:
        services.append(Service('init', file))
        if (len(file) > max_length):
            max_length = len(file)
            
    try:
        while True:
            
            print "\nList of services: \n"
            overview(services)
            
            
            command = raw_input('\nMain menu\nEnter your command: ')
            print ''
            if (not command):
                continue
            if (command == "l"):
                overview(services)
                    
                    
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
                    s.status()
                
                continue
        
    except KeyboardInterrupt:
        print "exiting..."
    except Exception as e:
        print "error: "+str(e)