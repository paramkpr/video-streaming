"""
video_stream.py
Author: Param Kapur

This class interacts with the .mjgep file to get the data for
each frame from it.
"""
class VideoStream:
	def __init__(self, filename):
		self.filename = filename
		self.file = open(filename, 'rb')
		self.frame_number = 0

	def next_frame(self):
		data = self.file.read(5)
		data = bytearray(data)
		# convert all the data into an integer
		data_int = (data[0] - 48) * 10000 + (data[1] - 48) * 1000 + (data[2] - 48) * 100 + (data[3] - 48) * 10 + (data[4] - 48)

		if data:
			frame_length = data_int  # int(data) #final_data_int/8  # xx bytes
			# Read the current frame
			frame = self.file.read(frame_length)
			if len(frame) != frame_length:
				raise ValueError('incomplete frame data')
			self.frame_number += 1
			print(f"\nNext Frame (#{str(self.frame_number)}) Length: {str(frame_length)} ")
			return frame

	def get_frame_number(self):
		"""Get frame number."""
		return self.frame_number
