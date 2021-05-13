"""
server.py
Author: Param Kapur

This server serves RTP and RTSP requests to the client. It first
processes the RTSP requests and then on the PLAY request it creates
the RTP socket and starts sending RTP packets over the wire.
"""

import random, math
import time
import sys, threading, socket

from video_stream import VideoStream
from packet import RtpPacket


class Server:
	SETUP = 'SETUP'
	PLAY = 'PLAY'
	PAUSE = 'PAUSE'
	TEARDOWN = 'TEARDOWN'

	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT

	def __init__(self, client):
		self.rtp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.client = client
		self.rtsp_socket = client.get('rtsp_socket')[0]
		self.client_addr = client.get('rtsp_socket')[1]

	def run(self):
		threading.Thread(target=self.recv_rtsp).start()

	# Request Handlers
	def recv_rtsp(self):
		while True:
			data = self.rtsp_socket.recv(256)
			if data:
				data = data.decode('utf-8').split('\n')
				request_type = data[0].split()[0]
				self.client['filename'] = data[0].split()[1]
				self.client['sequence_number'] = int(data[1].split()[0])
				self.client['rtp_port'] = data[2].split()[2]
				mapping = {"SETUP"   : self.setup,
				           "PLAY"    : self.play,
				           "PAUSE"   : self.pause,
				           "TEARDOWN": self.teardown}
				mapping[request_type]()

	def setup(self):
		if self.state == self.INIT:
			print("SETUP request recv")
			try:
				self.client['video_stream'] = VideoStream(self.client['filename'])
				self.state = self.READY
			except IOError:
				self.rtsp_socket.send(f"RTSP/1.0 404\n".encode('utf-8'))
			self.rtsp_socket.send(f"RTSP/1.0 200 OK\n{self.client['sequence_number']}\n".encode('utf-8'))

	def play(self):
		if self.state == self.READY:
			self.state = self.PLAYING
			self.client['event'] = threading.Event()
			self.client['worker'] = threading.Thread(target=self.send_rtp)
			self.client['worker'].start()

			self.rtsp_socket.send(f"RTSP/1.0 200 OK\n{self.client['sequence_number']}\n".encode('utf-8'))
		elif self.state == self.PAUSE:  # for resumptions
			self.state = self.PLAYING

	def pause(self):
		if self.state == self.PLAYING:
			self.state = self.READY
			self.client['event'].set()
			self.rtsp_socket.send(f"RTSP/1.0 200 OK\n{self.client['sequence_number']}\n".encode('utf-8'))

	def teardown(self):
		self.client['event'].set()
		self.rtsp_socket.send(f"RTSP/1.0 200 OK\n{self.client['sequence_number']}\n".encode('utf-8'))
		self.rtp_socket.close()
		sys.exit(0)

	# RTP Managers
	def send_rtp(self):
		"""
		This method sends RTP packets in a loop over the RTP wire. It
		simulates jitter and packet loss using random number generators
		for the purposes of this project. In any real-world usage
		these sections of the code would need to be removed.
		:return:
		"""
		while True:
			jitter = math.floor(random.uniform(-13, 5.99)) / 1000
			self.client['event'].wait(0.05 + jitter)  # Adding to 0.05 to cause timeout
			jitter += 0.020

			if self.client['event'].isSet():  # Stop thread exec on pause or teardown
				break

			data = self.client['video_stream'].next_frame()
			if data:
				frame_number = self.client['video_stream'].get_frame_number()
				simulated_loss = math.floor(random.uniform(1, 100))
				if simulated_loss > 5.0:
					rtp_packet = RtpPacket()
					rtp_packet.encode(26, frame_number, 0, data)
					self.rtp_socket.sendto(rtp_packet.get_packet(),
					                       (self.client_addr[0], int(self.client['rtp_port'])))
					time.sleep(jitter)


if __name__ == "__main__":
	rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	rtsp_socket.bind(('', int(sys.argv[1])))
	print("RTSP server started waiting for requests...")
	rtsp_socket.listen(5)
	while True:
		Server({'rtsp_socket': rtsp_socket.accept()}).run()
