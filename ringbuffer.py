try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO



class RingBuffer(object):
	def __init__(self, size):
		self.size = size
		self.buffer = StringIO()
		self.buffer_pos = 0
		self.read_pos = 0
		self.bytes_written = 0
		self.first_read = True
		self.fullclass = RingBufferFull
	
	def write(self, data):
		if self.buffer_pos + len(data) >= self.size:
			self.__class__ = self.fullclass
			split = self.size - self.buffer_pos
			self.buffer.write(data[:split])
			self.buffer.seek(0, 0)
			self.buffer_pos = 0
			self.bytes_written += split
			self.write(data[split:])
		else:
			self.buffer.write(data)
			self.buffer_pos += len(data)
			self.bytes_written += len(data)
		
	def read(self, bytes=0):
		self.buffer.seek(self.read_pos, 0)
		rb = self.buffer.read(bytes)
		self.read_pos = self.buffer.tell()
		self.buffer.seek(self.buffer_pos, 0)
		return rb


class SplitRingBuffer(RingBuffer):
	def __init__(self, size, split):
		RingBuffer.__init__(self, size)
		self.fullclass = SplitRingBufferFull
		self.splitpos = split
		self.read_pos = split
	
	def read_head():
		self.buffer.seek(0, 0)
		rb = self.buffer.read()
		self.buffer.seek(self.buffer_pos, 0)
		return (True, rb)
		

class RingBufferFull(object):
	def __init__(self, size):
		raise NotImplementedError, "You should not create this class manually, use RingBuffer() instead"
	
	def overflow_buffer():
		self.buffer_pos = 0
		self.seek_to_start()
		
	def seek_to_start():
		self.buffer.seek(0, 0)
		
	
	def write(self, data):
		di = 0
		ld = len(data)
		while (ld - di) + self.buffer_pos >= self.size:
			self.buffer.write(data[di:di + (self.size - self.buffer_pos)])
			if self.read_pos != None and self.read_pos > self.buffer_pos:
				# our read pos has been overwritten, we've lost our place
				self.read_pos = None
			self.overflow_buffer()
			di += (self.size - self.buffer_pos)
		self.buffer.write(data[di:])
		if self.read_pos != None and self.buffer_pos <= self.read_pos and (self.buffer_pos + ld - di) > self.read_pos:
			self.read_pos = None
		self.buffer_pos += ld - di
		self.bytes_written += ld
	
	def read(self, bytes=0):
		pos = self.read_pos
		fullread = False
		if pos == None:
			pos = self.buffer_pos
			fullread = True
			
		if pos == self.buffer_pos and fullread:
			maxlen = self.size
		elif pos == self.buffer_pos and not fullread:
			maxlen = 0
		else:
			maxlen = self.buffer_pos - pos
			if maxlen < 0:
				maxlen += self.size
		self.buffer.seek(pos, 0)
		if bytes > 0 and maxlen > bytes:
			maxlen = bytes
		
		if maxlen == 0:
			return ''
		
		split = self.size - pos
		if split >= maxlen:
			self.buffer.seek(pos, 0)
			rb = self.buffer.read(maxlen)
			self.read_pos = self.buffer.tell()
			self.buffer.seek(self.buffer_pos, 0)
		else:
			self.buffer.seek(pos, 0)
			rb = self.buffer.read(split)
			self.seek_to_start()
			rb += self.buffer.read(maxlen - split)
			self.read_pos = self.buffer.tell()
			self.buffer.seek(self.buffer_pos, 0)
		
		return rb


class SplitRingBufferFull(RingBufferFull):
	def read(self, bytes=0):
		pass

	def overflow_buffer():
		self.buffer_pos = self.split_pos
		
	def seek_to_start():
		self.buffer.seek(self.split_pos, 0)

	def read_head():
		self.buffer.seek(0, 0)
		rb = self.buffer.read(self.split_pos)
		self.buffer.seek(self.buffer_pos, 0)
		return (False, rb)
		
		