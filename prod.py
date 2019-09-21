#!/usr/bin/python3

import signal
import time
import sys
from monitor import Message, Monitor
import random

def abort(signal, frame):
        mon.stop()
        sys.exit(0)

signal.signal(signal.SIGINT, abort)

host = "127.0.0.1"
ports = ["8000", "8001", "8002"]

try:
   act_port = int(sys.argv[1])
except(ValueError):
    print("Value error...\n")
    sys.exit(-1)

if act_port > len(ports):
    print("Out of bounds...\n")
    sys.exit(-1)

if act_port == 0:
    token = True
else:
    token = False

_id = host + ':' + ports[act_port]
proc_list = []

for i in ports:
    if i != ports[act_port]:
        proc_list.append(host + ":" + i)

proc_list.append(_id)

mon = Monitor(_id, token, proc_list)
mon.start()

i = 1 
while True:
    prod = mon.acquire()
    if not prod:
        prod = [0]
    else:
        prod.append(prod[-1] + 1)
        i+=1
            
    print("Buffer: ", prod)
    time.sleep(random.randint(1,3))
    mon.release(prod)

    if (i > 10):
    	print("Produced:", i-1)
    	mon.stop()
    	sys.exit(0)
    
    time.sleep(random.randint(1,3))
