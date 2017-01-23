import fileinput
import json
import os
import socket

def process_loop():
  script_dir = '/usr/lib/waggle/nodecontroller/scripts'
  for line in fileinput.input():
    try:
      instruction=json.loads(line)
    except:
      print(json.dumps({"rc":99, "pythonError":"invalid instruction: json parsing failed"}))
      continue

    if "args" not in instruction:
      print(json.dumps({"rc":99, "pythonError":"invalid instruction: missing args list"}))

    if len(instruction["args"]) == 0:
      print(json.dumps({"rc":99, "pythonError":"invalid instruction: empty args list"}))
      continue

    command = instruction["args"][0]

    args = []
    if len(instruction["args"]) > 1:
      args = instruction["args"][1:]

    if command == "quit":
      print(json.dumps({"rc":0}))
      return
    elif command == "type":
      print(json.dumps({"rc":0, "type":"C1+"}))
    elif command == "nodeid":
      print(json.dumps({"rc":0, "nodeid":socket.gethostname()[:12]}))
    elif command == "disk":
      print(json.dumps({"rc":0, "disk":socket.gethostname()[12:15]}))
    elif command == "test":
      return_value = os.system(''.join((script_dir, "/run-tests")))
      test_log = subprocess.check_output('cat', '/home/waggle/test.log')
      print(json.dumps({"rc":return_value.to_bytes(2, byteorder='big')[0], "test":test_log}))
    elif command == "boot":
      disk = args[0]
      device = args[1]
      return_value = os.system(''.join((script_dir, "/boot ", disk, ' ', device)))
      print(json.dumps({"rc":return_value.to_bytes(2, byteorder='big')[0]}))
    elif command == "shutdown":
      return_value = os.system(''.join((script_dir, "/shutdown-node")))
      print(json.dumps({"rc":return_value.to_bytes(2, byteorder='big')[0]}))
    elif command == "lockdown":
      return_value = os.system(''.join((script_dir, "/lockdown")))
      print(json.dumps({"rc":return_value.to_bytes(2, byteorder='big')[0]}))
    else:
      print(json.dumps({"rc":99, "pythonError":"invalid instruction: unrecognized command"}))

if __name__ == '__main__':
  process_loop()
