#!/usr/bin/env python


import subprocess
from subprocess import call
import commands, os.path, sys, argparse
import re
from tabulate import tabulate


class Service:
    
    service_commands = ['start', 'stop', 'restart', 'status']
    
    def __init__(self, id):
        self.id = id
    
    def status(self):
        print "nothing"
        pass
        
    def start(self):
        pass
         
    def stop(self):        
        pass
        
    def restart(self):        
        pass
        
    def command(self, cmd):
        #print "command got" , cmd
        text2function = {
            'start' : self.start,
            'stop' : self.stop,
            'restart' : self.restart,
            'status' : self.status
        }
        
        result = None
        try:
            func = text2function[cmd]
        except Exception as e:
            print "error: command unknown: ", str(e)
            return None
        
        try:
            result = func()
        except Exception as e:
            print "error executing command: ", str(e)
            return None
        
        return result
        
        
     
class UpStartService(Service):
    
    # from http://upstart.ubuntu.com/cookbook/#job-states
    upstart_states = ['waiting' , 'killed', 'post-start', 'post-stop', 'pre-start', 'pre-stop', 'running', 'security', 'spawned', 'starting', 'stopping', 'waiting'] 
    upstart_goals = ['start', 'stop']
    upstart_states_dict = {}
    upstart_goals_dict = {}
    
    for i in upstart_states:
        upstart_states_dict[i]=1
    
    for i in upstart_goals:
        upstart_goals_dict[i]=1
    
    
    def parse_status_line(self, line):
        
        
        if not line:
            return {'status' : 0, 'text' : 'status line empty', 'error' : 1}
        
        if 'Job is already running' in line:
            return {'status' : 1, 'text' : 'Job is already running'}
        
        
        if 'Unknown instance' in line:
            return {'status' : 0, 'text' : 'Unknown instance', 'error' : 1}
        
        
        status_parsed_array = re.findall("(\S+) (\S+),(.*)", line)
        if not status_parsed_array:
            status_parsed_array = re.findall("(\S+) (\S+)", line)
        
        #print str(status_parsed_array)
        if not status_parsed_array:
            return {'error' : 1, 'text' : 'Could not parse status line: ' + line}
            
        status_parsed = status_parsed_array[0]
        if len(status_parsed) < 2:
            return {'error' : 1, 'text' : 'Could not parse status line: ' + line}
        
        
        result = status_parsed[1]
        
        state_goal_array = re.findall("^(\S+)/(\S+)$", result)
       
        goal = ''
        state = ''
        
        
        if state_goal_array and len(state_goal_array[0]) == 2:
            goal, state  = state_goal_array[0]
            
        
        #print result, "\n"
        
        if state in self.upstart_states_dict:   
        
            if "wait" in result:
                return {'status' : 0, 'text' : result, 'state': state, 'goal': goal}
        
            if "running" in result:
                return {'status' : 1, 'text' : result, 'state': state, 'goal': goal}
        
        
        print 'state: ', state
        print 'self.upstart_states_dict: ', str(self.upstart_states_dict)
        
        return {'error' : 1, 'text' : 'status unknown: '+ result, 'state': state, 'goal': goal}
        
        
    
    def status(self):
        status_line = "\n".join(subprocess.Popen(["service", self.id, "status"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate())
        return self.parse_status_line(status_line)
        
        
    def start(self):
        command = ["service", self.id, "start"]
        #print "command: ", ' '.join(command)
        status_line = "\n".join(subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate())
        return self.parse_status_line(status_line)
         
    def stop(self):
        command = ["service", self.id, "stop"]
        #print "command: ", ' '.join(command)
        status_line = "\n".join(subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate())
        return self.parse_status_line(status_line)
        
    def restart(self):
        command = ["service", self.id, "restart"]
        #print "command: ", ' '.join(command)
        status_line = "\n".join(subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate())
        return self.parse_status_line(status_line)
        
        
   
        
        
class InitService(Service):


    def status(self):
        #print "/etc/init.d/"+self.id, "status"
        #call(["/etc/init.d/"+self.id, "status"])
    
        if not os.path.isfile("/etc/init.d/"+self.id):
            return -10
    
        result = commands.getstatusoutput("/etc/init.d/"+self.id+" status")
        #print result, "\n"
        if "Stopped" in result:
            return 1
    
        if "Running" in result:
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
    



    
    
    
    

class UpStart:
    
    def __init__(self):
        
        self.services = []
        self.services_all = subprocess.Popen(["initctl", "list"], stdout=subprocess.PIPE).communicate()[0]
        for line in self.services_all.split("\n"):
            if line.startswith("waggle_"):
                #print line
                result = re.findall("^\S+", line)
                if result:
                    #print result[0] + "\n"
                    self.services.append(UpStartService(result[0]))
    
        # dict to find service by name
        self.services_dict={}    
        for s in self.services:
            self.services_dict[s.id.lower()] = s
            
    def execute(self, cmd_array):
        
        #print "command I got:", ','.join(cmd_array)
        
        if not cmd_array:
            print "error: cmd_array empty"
            return 0
        
        command = cmd_array[0].lower()
        if not command:
            print "error: no command"
            return 0
    
        if command == 'list' or command == 'l':
            self.overview()
            return 1
    
        if len(cmd_array)==2:
            service_string = cmd_array[1].lower()
        else:
            print "error: not sure what to do"
            return 0
        
        if not service_string:
            print "error: service_string empty"
            return 0
        
        if not command in Service.service_commands:
            print "error: command %s unknown" % (command)
            return 0
            
        try:
            service = self.services_dict[service_string]
        except:
            service = None
        
        if not service:
            print "error: service '{}' not found".format(service_string)
            return 0
        
        result_obj = service.command(command)
    
        if not result_obj:
            print "error: no result"
            return 0
        
        if 'error' in result_obj:
            print "error performing command %s on service %s" % (command, service_string)
            if 'text' in result_obj:
                print result_obj['text']
            return 0
    
        if 'state' in result_obj:
            print 'State: ', result_obj['state'] 
            print '(Goal: %s)' % ( result_obj['goal'] )
            return 1
        
        if 'text' in result_obj:
            print 'Status: ', result_obj['text']
        else:
            print "no text found"
            return 0
    
        return 1
        if not result:
            return 0
        
        
        
        
    def overview(self):
        header = ['id', 'name', 'goal', 'state']
        data = []
        for i, s in enumerate(self.services):
        
            status_obj = s.status()
        
            state = 'n/a'
            goal = 'n/a'
        
            status = status_obj['text']
            if 'state' in status_obj:
                state = status_obj['state']
            if 'goal' in status_obj:
                goal = status_obj['goal']
        
            if not status:
                status='error'
        
            #print "(%d) %s  %s\n" % (i, s.id, status.ljust(10, ' '))
            data.append([i, s.id, goal, state])

        print tabulate(data, header, tablefmt="psql")

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    
    
    parser.add_argument('commands',nargs='*')
    
    args = parser.parse_args()
    
    
    
    
    
    #if args.help: 
    #    print "usage: {} list".format(basename(__file__))
    #    print "       {} start|stop|restart <service>".format(basename(__file__))
    #    sys.exit(0)
    
    
    upstart = UpStart()
    
    
    if args.commands:
        if upstart.execute(args.commands):
            sys.exit(0)
        
        sys.exit(1)
        
        
    
            
    try:
        while True:
            
            print "\nList of services: \n"
            upstart.overview()
            
            
            command = raw_input('\nMain menu\nEnter your command: ')
            #print "got '%s' \n" % (command)
            print ''
            if (not command):
                continue
                
            upstart.execute(re.split(r"\s+", command)) 
            
            
            # if (command == "l"):
    #             overview(services)
    #         elif (command == "q"):
    #              sys.exit(0)
    #         elif (command in "0123456789"):
    #             index = int(command)
    #             s=services[index]
    #             print "service selected: "+s.id+"\n"
    #             subcommand = raw_input('1=Start, 2=Stop, 3=Restart, 4=Status, 0=Return:')
    #             print ''
    #             if (subcommand == '1'):
    #                 s.start()
    #             elif (subcommand == '2'):
    #                 s.stop()
    #             elif (subcommand == '3'):
    #                 s.restart()
    #             elif (subcommand == '4'):
    #                 status_int = s.status()
    #                 status = status_code_2_text(status_int)
    #                 print "(%d) %s  %s\n" % (index,  '', status.ljust(10, ' '))
                    
            
        
    except KeyboardInterrupt:
        print "exiting..."
    except Exception as e:
        print "error: "+str(e)
