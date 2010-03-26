# ini reader/writer
__doc__ = """
reads and writes config files using the microsoft windows 'ini' format.
(author's note: I don't think there IS any official 'ini' format. Some
artistic licence may have been used)

Provides class 'inifile', which is a dict-like object that can be read
from a file or written out to a file (or both!)
"""

__license__ = """
Copyright (c) 2006-2007 Bradley Lawrence <bradley@eltanin.net>

This is licensed under the Modified BSD License, as follows:

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


import os.path
from utils import program_path

def sanitize_for_subst(key):
	"""
	replaces open and close brackets with tokens, to ensure the brackets
	do not interfere with the %(dict_key)s string formatting syntax.
	
	'=' is used as a token delimiter because we know an equals can never
	appear in a keyname, since it is interpreted by this reader as the
	end of the key and the start of the value.
	"""
	return key.replace('(', '=o=').replace(')', '=c=')
	
	
	
		
class inisubsec(object):
	def __init__(self, name, owner):
		self.owner = owner
		self.name = name
		self.data = {}
		self.verbatim_hdr = "[%(sec_title)s]\n"
		self.verbatim = ["%(=new_data=)s"]
		self.verbatim_ftr = "\n"
		self.verbatim_fields = []
		self.new_fields = []
		self.initializing = True
		
	def __getitem__(self, key):
		return self.data[key.lower()]
		
	def __setitem__(self, key, value):
		if not self.data.has_key(key.lower()):
			if self.initializing:
				self.verbatim_fields += [key]
			else:
				self.new_fields += [key]
		self.data[key.lower()] = value
		
	def __delitem__(self, key):
		del self.data[key.lower()]
		
	def __iter__(self):
		return self.data.__iter__()
	def items(self):
		return self.data.items()
		
	
		
class inifile(object):
	def __init__(self, fname, path=None):
		self.data = {}
		sep = os.path.sep
		
		if not path:
			fs = os.path.split(fname)
			self.fname = os.path.split(fname)[1]
			if not fs[0]:
				self.path = (program_path() + sep, '')
			else:
				self.path = (fs[0] + sep,)
		else:
			if type(path) == str:
				self.path = (path,)
			else:
				self.path = []
				for p in path:
					if p and (p[-1] != sep):
						p += sep
					self.path += [p]
			self.fname = fname
			
		self.last_opened_file = None	
		self.cur_section = None
		self.activepath = None
		self.verbatim_hdr = []
		self.section_order = []
	
	def set_section(self, section):
		self.cur_section = section.lower()
		
	def unset_section(self):
		self.cur_section = None
	
	def get_current_file(self):
		return 
	def read(self):
		fd = None
		for p in self.path:
			if os.path.exists(p + self.fname):
				self.activepath = p
				fd = file(p + self.fname, 'r')
				break
		if not fd:
			return False
			
		act_section = 'default'
		section_init = False
		for line in fd:
			verbatimline = line
			keyvalue_line = False
			line = line.lstrip()
			if not line:
				# blank line, ignore
				pass
			elif line[0] == ';':
				# comment! ignore
				pass
			elif line[0] == '[':
				# section header
				line = line.rstrip()
				if line[-1] == ']':
					act_section = line[1:-1]
					section_init = True
					if not self.data.has_key(act_section.lower()):
						"add specified section"
						actsec = inisubsec(act_section, self)
						self.data[act_section.lower()] = actsec
						actsec.verbatim_hdr = verbatimline
						actsec.verbatim_ftr = ""
						verbatimline = None
						self.section_order += [act_section]
				else:
					# garbage line, don't understand it
					pass
			else:
				peq = line.find('=')
				if peq == -1:
					# garbage line, don't understand it
					pass
				else:
					k = line[:peq]
					v = line[peq+1:].rstrip('\n\r')
					if not self.data.has_key(act_section.lower()):
						"add default section"
						assert not section_init
						
						actsec = inisubsec('default', self)
						self.data[act_section.lower()] = actsec
						
						
					self.data[act_section.lower()][k] = v
					verbatimline = "".join([k, '=%(', sanitize_for_subst(k.lower()), ')s\n'])
					keyvalue_line = True
			
			if verbatimline:
				if section_init or keyvalue_line:
					"keyvalue lines always go under the default section, regardless of initialized state"
					actsec = self.data[act_section.lower()]
					actsec.verbatim += [verbatimline]
				else:
					self.verbatim_hdr += [verbatimline]
			
		
		if section_init:
			actsec = self.data[act_section.lower()]
			actsec.verbatim += ["\n"]
		else:
			self.verbatim_hdr += ["\n"]
		
		if self.data.has_key('default'):
			"has a default section. make sure it's added to the section_order"
			try:
				self.section_order.index('default')
			except:
				self.section_order += ['default']
			
		for secdict in self.data.values():
			secdict.initializing = False
					
	def write(self):
		p = self.path[0]
		if self.activepath:
			p = self.activepath
			
		fd = file(p + self.fname, 'w')
		first = True
		
		fd.write("".join(self.verbatim_hdr))
		
		for sec in self.section_order:
			secdict = self.data[sec.lower()]
			
			new_lines = []
			for k in secdict.new_fields:
				new_lines += ["%s=%s\n" % (k, secdict[k])]
			new_lines = "".join(new_lines)
			verbatim_dict = {'=new_data=': new_lines}
			for k in secdict.verbatim_fields:
				verbatim_dict[sanitize_for_subst(k.lower())] = secdict[k]
			
			fd.write(secdict.verbatim_hdr % {'sec_title': secdict.name})
			fd.write("".join(secdict.verbatim) % verbatim_dict)
			fd.write(secdict.verbatim_ftr)
	
	def add_section(self, key):
		if not self.data.has_key(key):
			self.data[key.lower()] = inisubsec(key, self)
			self.section_order += [key]
		

	def __getitem__(self, key):
		if type(key) != str:
			raise TypeError, "Ini files can only contain string keys"
			
		if self.cur_section != None:
			if self.data[self.cur_section].has_key(key.lower()):
				return self.data[self.cur_section][key.lower()]
			else:
				raise KeyError, "Section '%s' does not contain a key named '%s'" % (self.cur_section, key)
		else:
			#if not self.data.has_key(key.lower()):
			#	self.data[key.lower()] = inisubsec(key, self)
			return self.data[key.lower()]
	def __setitem__(self, key, value):
		if self.cur_section != None:
			if not self.data.has_key(self.cur_section):
				raise KeyError, "Section '%s' does not exist" % (self.cur_section)
			self.data[self.cur_section][key.lower()] = value
		else:
			raise ValueError, "Cannot set the value of a section header"

	def __delitem__(self, key):
		del self.data[key.lower()]
		
	def __iter__(self):
		return self.data.__iter__()

	def items(self):
		return self.data.items()
		
