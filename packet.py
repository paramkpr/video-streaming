"""
packet.py
Author: Param Kapur

This file contains the RtpPacket class that defines the RTP packet
structure as defined in RFC 3550:

  0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |V=2|P|X|  CC   |M|     PT      |       sequence number         |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                           timestamp                           |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |           synchronization source (SSRC) identifier            |
   +=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+
   |            contributing source (CSRC) identifiers             |
   |                             ....                              |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

https://datatracker.ietf.org/doc/html/rfc3550#section-5.1
"""

from time import time


HEADER_SIZE = 24

class RtpPacket:
	def __init__(self):
		self.packet = ''
		self.payload = ''
		self.version = self.padding = self.extension = self.cc_count \
			= self.marker = self.payload_type = self.sequence_number \
			= self.timestamp = self.ssrc = 0

	def encode(self, pt, seq, ssrc, payload, v=2, p=0, x=0, cc=0, m=0):
		"""
		This method assigns the payload to the RtpPacket object
		and sets all relevant headers in a string to prepare
		the object to be serialized and sent over the socket.

		:param v: version
		:param p: padding
		:param x: extension
		:param cc: CSRC count
		:param m: marker
		:param pt: payload type
		:param seq: sequence number
		:param ssrc: random synchronization source to avoid collisions
			   ccrc: not required for single source
		:param payload: the actual data being sent
		:return:
		"""

		chunk_1 = format(int((str(format(v, 'b').zfill(2)) + str(p) + str(x) + str(format(cc, 'b').zfill(4))), 2),
		                 'x').zfill(2)
		chunk_2 = format(int((str(m) + str(format(pt, 'b').zfill(7))), 2), 'x').zfill(2)
		sequence_number = format(seq, 'x').zfill(4)
		timestamp = format(int(time()), 'x').zfill(8)
		ssrc = str(format(ssrc, 'x').zfill(8))

		header = chunk_1 + chunk_2 + sequence_number + timestamp + ssrc
		self.header = bytearray(header, 'utf-8')
		self.payload = payload


	def decode(self, bytestream):
		"""
		Accepts a bytestream from the server and deserializes
		the packet into it's headers and payload.

		:param bytestream:
		:return:
		"""
		self.header = bytearray(bytestream[:HEADER_SIZE]).decode('utf-8')

		chunk_1 = format(int(self.header[0:2], 16), 'b')
		self.version = int(chunk_1[0:2], 2)
		self.padding = int(chunk_1[2:3])
		self.extension = int(chunk_1[3:4])
		self.cc_count = int(chunk_1[4:8], 2)

		chunk_2 = format(int(self.header[2:4], 16), 'b').zfill(8)
		self.marker = int(chunk_2[0:1])
		self.payload_type = int(chunk_2[1:8], 2)

		self.sequence_number = int(str(self.header[4:8]), 16)
		self.timestamp = int(str(self.header[8:16]), 16)
		self.ssrc = int(str(self.header[16:24]), 16)

		self.payload = bytestream[HEADER_SIZE:]

	def get_sequence_number(self):
		return int(str(self.header[4:8]), 16)

	def get_payload(self):
		return self.payload

	def get_packet(self):
		return self.header + self.payload
