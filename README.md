# video-streaming
This is my final project for CS396. I'm going to be implementing  RTSP and RTP
in Python from scratch. 

## Usage
You will need to start 2 processes to build this project. The first is the
server and then you will need to start the client. Please note that this 
project does use the Tkinter library to create the GUI, you'll need to pip
that if you don't already have it. This is the only external dependency.

### Server
```python server.py <port_number>``` eg.  
```python server.py 1025```

### Client
```python client.py <server_addr> <server_port> <client_port> <filename>``` eg.   
```python client.py 127.0.0.1 1025 5008 video.mjpeg```

### GUI
Once the GUI has rendered you'll see the following four buttons:
Connect, Play, Pause, Exit. First, click 'Connect' then click 'Play',
'Pause' and 'Exit' as you wish.

## Note:
From the RFC for RTP (https://datatracker.ietf.org/doc/html/rfc3550) this
project uses payload type 26 and will accept files with a .mjpeg or
'Motion JPEG' extension.

