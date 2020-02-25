#Description
```
Implementation of remote monitor using Suzuki-Kasami algorithm. Uses pyznq library for communication. 

cons.py - consumer thread getting values from buffer
prod.py - producer thread putting values into buffer
monitor.py - monitor module
```

#Usage
```
./producent.py 0
./consumer.py 1
./consumer.py 2
```

#Prerequisites
```
zmq
```
