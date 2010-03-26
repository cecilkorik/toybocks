import sys
import os

def program_path():
	p = os.path.split(sys.argv[0])[0]
	p = os.path.abspath(p)
	p = os.path.realpath(p)
	return p