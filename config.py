from utils import program_path
from inifile import inifile

config = inifile('settings.ini', path=[program_path()])
config.read()