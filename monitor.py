#!/usr/bin/python3

import zmq
import threading
import queue
import socket
from contextlib import closing
import time
import sys

#Based on Suzuki-Kasami algorithm
#Q - Queue storing the ID of processes waiting for the token
#LN - Last request Number - array of request numbers from j-process that was successfull
#RN - Request Number - array of request numbers from j-process

#Object to exchange data between processes
class Message():
    def __init__(self, sender, receiver, mode, message, LN, Q):
        
        self.mode = mode
        self.message = message
        self.LN = LN
        self.Q = Q

        self._receiver = receiver
        self._sender = sender
        
class Monitor():
    def __init__(self, my_id, token, proc_list):
      
        self.__my_id = my_id
        self.__proc_list = proc_list
        self._RN = {}
        self._LN = {}
        self.Q = []
        self._token = token
        self._in_CS = False
        self._message = None
        self._RN = {x: 0 for x in self.__proc_list}
        self._LN = {x: 0 for x in self.__proc_list}
        self.__receive_queue = queue.Queue(1)
        self.__is_running = True
        self.__lock = threading.Lock()

    #Creates publisher process on specified port 
    def init_publisher(self):
        publisher = zmq.Context()
        self.publisher = publisher.socket(zmq.PUB)
        try:
            self.publisher.bind(f"tcp://{self.__my_id}")
        except:
            print("Port already in use...\n")
            sys.exit(-1)

    def subscribe(self, proc_list):
        context = zmq.Context()
        subscriber = context.socket(zmq.SUB)

        #Connects with other publisher processes
        for process in proc_list:
            subscriber.connect(f"tcp://{process}")
        subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

        poller = zmq.Poller()
        poller.register(subscriber, zmq.POLLIN)

        while self.__is_running:
            socks = dict(poller.poll(1000))
            if subscriber in socks:
                with self.__lock:
                    msg_obj = subscriber.recv_pyobj()

                    #If current process sent message then discard it
                    if msg_obj._sender == self.__my_id:
                        continue
                    
                    if msg_obj._receiver == "update_RN":
                        self._RN[msg_obj._sender] = max(self._RN[msg_obj._sender], msg_obj.mode)

                        #Check if current process has token and knows that other process needs it
                        if self._token and \
                                self._in_CS == False and \
                                self._RN[msg_obj._sender] == self._LN[msg_obj._sender] + 1:
                            self.send_token(msg_obj._sender)
                    #Receive token
                    elif msg_obj._receiver == self.__my_id and msg_obj.mode == "token":
                        self.Q = msg_obj.Q
                        self._LN = msg_obj.LN
                        self.__receive_queue.put(msg_obj.message)
                        self._token = True
                    else:
                        pass

        subscriber.close()

    #Checks if all procesess are created 
    def test_socket(self, host):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                ip_ad = host.split(":")[0]
                port = int(host.split(":")[1])
                if sock.connect_ex((ip_ad, port)) == 0:
                    return True
                else:
                    return False
            finally:
                sock.close()

    def start(self):
        self.init_publisher()
        print("Waiting for procesess to connect...")

        tmp = [proc for proc in self.__proc_list if proc != self.__my_id]
        for process in tmp:
            while not self.test_socket(process): 
                time.sleep(1)

        #Creates thread that will respond to incoming packets
        thr = threading.Thread(target=self.subscribe, args=(self.__proc_list,))
        thr.setDaemon = True
        
        thr.start()
        time.sleep(2)

    def stop(self):
        self.publisher.close()
        self.__is_running = False

    #Creates the Message object containing RN update and sends it via publisher
    def update_RN(self, update_val):
        msg = Message(self.__my_id, "update_RN", update_val, None, None, None)
        self.publisher.send_pyobj(msg)

    #Creates the Message object containing token and sends it via publisher
    def send_token(self, receiver):
        self._token = False
        msg = Message(self.__my_id, receiver, "token", self._message, self._LN, self.Q)
        self.publisher.send_pyobj(msg)

    # Enter critical section
    def acquire(self):
        with self.__lock:
            if self._token:
                self._in_CS = True
                #return self._message
            else:
                self._RN[self.__my_id]+=1
                self.update_RN(self._RN[self.__my_id])

        self._message = self.__receive_queue.get()
        self._in_CS = True
        return self._message

    # Exit critical section
    def release(self, message):
        with self.__lock:
            self._message = message
            self._LN[self.__my_id] = self._RN[self.__my_id]

            #For every process k not in the token queue Q it appends k to Q if RN = LN+1
            q_list = [proc for proc in self.__proc_list if proc not in self.Q]

            for k in q_list:
                if self._RN[k] == self._LN[k] + 1:
                    self.Q.append(k)

            #If Q is nonempty pops a process j ID from Q and sends token to j
            if self.Q:
                self.send_token(self.Q.pop(0))
            self._in_CS = False
