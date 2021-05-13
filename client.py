"""
client.py
Author: Param Kapur

This file contains the Tkinter client that renders the video stream.
The client uses RTP to receive the actual video data and uses RTSP
to manage the controls for the video stream.

"""
from tkinter import *
from tkinter import messagebox
from tkinter import Tk
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os

from packet import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"


class Client:
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT

	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3

	counter = 0

	def __init__(self, root, server_address, server_port, rtp_port, filename):
		self.root = root
		self.exit = Button(self.root, width=15, padx=5, pady=5)
		self.pause = Button(self.root, width=15, padx=5, pady=5)
		self.play = Button(self.root, width=15, padx=5, pady=5)
		self.connect = Button(self.root, width=15, padx=5, pady=5)
		self.build_gui()
		self.server_address = server_address
		self.server_port = int(server_port)
		self.rtp_port = int(rtp_port)
		self.filename = filename
		self.request_state = -1
		self.teardown_flag = 0
		self.rtsp_sequence_number = 0
		self.rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.rtsp_socket.connect((self.server_address, self.server_port))
		except:
			messagebox.showwarning('Connection Not Established', 'Could not connect to the server')

		self.frame_number = 0
		self.rtp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	def build_gui(self):
		self.connect['text'] = 'Connect'
		self.connect['command'] = self.init_connection
		self.connect.grid(row=1, column=0, padx=2, pady=2)

		self.play['text'] = 'Play'
		self.play['command'] = self.play_video
		self.play.grid(row=1, column=1, padx=2, pady=2)

		self.pause['text'] = 'Pause'
		self.pause['command'] = self.pause_video
		self.pause.grid(row=1, column=2, padx=2, pady=2)

		self.exit['text'] = 'Exit'
		self.exit['command'] = self.exit_client
		self.exit.grid(row=1, column=3, padx=2, pady=2)

		self.label = Label(self.root, height=19)
		self.label.grid(row=0, column=0, columnspan=4, sticky=W + E + N + S, padx=5, pady=5)

	# GUI Action Handlers
	def init_connection(self):
		if self.state == self.INIT:
			threading.Thread(target=self.recv_rtsp).start()
			self.rtsp_sequence_number = 1
			self.rtsp_socket.send(f"SETUP {str(self.filename)}\n{str(self.rtsp_sequence_number)}\nRTSP/1.0 RTP/UDP {self.rtp_port}".encode('utf-8'))
			self.request_state = self.SETUP

	def exit_client(self):
		if not self.state == self.INIT:
			self.rtsp_sequence_number += 1
			self.rtsp_socket.send(f"TEARDOWN {str(self.filename)}\n{str(self.rtsp_sequence_number)}\nRTSP/1.0 RTP/UDP {self.rtp_port}".encode('utf-8'))
		print("Exit request sent")
		self.request_state = self.TEARDOWN
		self.root.destroy()
		sys.exit(0)

	def play_video(self):
		if self.state == self.READY:
			print("Starting Video Playback")
			threading.Thread(target=self.rtp_listen).start()
			self.play_event = threading.Event()
			self.play_event.clear()
			self.rtsp_sequence_number += 1
			self.rtsp_socket.send(f"PLAY {str(self.filename)}\n{str(self.rtsp_sequence_number)}\nRTSP/1.0 RTP/UDP {self.rtp_port}".encode('utf-8'))
			self.request_state = self.PLAY

	def pause_video(self):
		if self.state == self.PLAYING:
			self.rtsp_sequence_number += 1
			self.rtsp_socket.send(f"PAUSE {str(self.filename)}\n{str(self.rtsp_sequence_number)}\nRTSP/1.0 RTP/UDP {self.rtp_port}".encode('utf-8'))
			self.request_state = self.PAUSE

	# RTSP Managers
	def recv_rtsp(self):
		while True:
			reply = self.rtsp_socket.recv(1024)

			if reply:
				self.parse_rtsp(reply)

			# Close the RTSP socket upon requesting Teardown
			if self.request_state == self.TEARDOWN:
				self.rtsp_socket.shutdown(socket.SHUT_RDWR)
				self.rtsp_socket.close()
				break

	def parse_rtsp(self, data):
		headers = data.decode('utf-8').split('\n')
		sequence_number = int(headers[1].strip())
		status_code = int(headers[0].split()[1])
		if sequence_number == self.rtsp_sequence_number:
			if self.request_state == self.SETUP:
				if status_code == 200:
					self.state = self.READY
					self.rtp_socket.settimeout(0.5)
					try:
						self.rtp_socket.bind((self.server_address, self.rtp_port))
						print("RTP Port bind success")
					except:
						print("RTP Port bind falied")
					print('Opened port for video stream')
			elif self.request_state == self.PLAY:
				self.state = self.PLAYING
			elif self.request_state == self.PAUSE:
				self.state = self.READY
			elif self.request_state == self.TEARDOWN:
				self.teardown_flag = 1

	# RTP Managers
	def rtp_listen(self):
		while True:
			try:
				data, addr = self.rtp_socket.recvfrom(20480)
				if data:
					rtp_packet = RtpPacket()
					rtp_packet.decode(data)
					print(f"Received Rtp Packet #{str(rtp_packet.get_sequence_number())}")

					if self.frame_number + 1 != rtp_packet.get_sequence_number():
						self.counter += 1
						print(f"Packet Loss Event")
					current_frame_number = rtp_packet.get_sequence_number()
					if current_frame_number > self.frame_number:
						self.frame_number = current_frame_number
						self.update_video(rtp_packet.get_payload())
			except:
				print('No data received from rtp socket')
				if self.play_event.isSet():
					break

				if self.teardown_flag:
					self.rtp_socket.close()
					break

	def update_video(self, payload):
		"""Creates a temp cached image in the dir from the payload
		 and then actually places that next frame on the Tkinter GUI"""
		with open("cache.jpg", "wb") as f:
			f.write(payload)

		img = ImageTk.PhotoImage(Image.open("cache.jpg"))
		self.label.configure(image=img, height=288)
		self.label.image = img


if __name__ == "__main__":
	root = Tk()
	app = Client(root,sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4])
	root.mainloop()
