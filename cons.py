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
proc_list = []

try:
    act_port = int(sys.argv[1])
except(ValueError):
    print("Value error...\n")
    sys.exit(-1)

if act_port > len(ports):
    print("Out of bounds...\n")
    sys.exit(-1)

_id = host + ":" + ports[act_port]

for i in ports:
    if i != ports[act_port]:
        proc_list.append(host + ":" + i)

proc_list.append(_id)

mon = Monitor(_id, False, proc_list)
mon.start()

i = 0 
while True:
    prod = mon.acquire()
    if prod:
        i = 0
        print("Received:", prod.pop(0))
    else:
        print("Empty buffer")
        
        i+=1
    time.sleep(random.randint(1,3))
    mon.release(prod)

    if (i>=3):
        print("Timedout")
        mon.stop()
        sys.exit(0)
    
    time.sleep(random.randint(1,5))
