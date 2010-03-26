import dblayer
from dblayer import db, cur
import subprocess, shlex
import os
from zipfile import ZipFile
from threading import Thread
from ringbuffer import SplitRingBuffer
import time

class EmulatorHandlerThread(Thread):
	def __init__(self, game, proc):
		Thread.__init__(self)
		self.buffer = SplitRingBuffer(1024*1024, 512*1024)
		self.game = game
		self.proc = proc

	
	def run(self):
		while True:
			data = self.proc.stdout.read(4096)
			self.proc.poll()
			if not data and self.proc.returncode != None:
				break
			self.buffer.write(data)
			time.sleep(0.4)

		
emulator_table = {}
gamesystem_table = {}
playlist_list = []
playlist_table = {}

class GamesystemInfo(object):
	def __init__(self, id, name, fileext):
		self.id = id
		self.name = name
		self.fileexts = fileext.split(';')
		self.emu_id = None

class EmulatorInfo(object):
	def __init__(self, id, name, path, options):
		self.id = id
		self.name = name
		self.path = path
		self.options = options
		self.system_id = None
		
	def start_game(self, game):
		args = shlex.split(self.options)
		emu = subprocess.Popen([self.path] + args + [game.path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		return emu

class GameInfo(object):
	def __init__(self, id, name, path, emu, syst):
		self.id = id
		self.name = name
		self.path = path
		self.emu_id = emu
		self.system_id = syst

class AllGames_Playlist(object):
	def __init__(self):
		self.id = None
		self.name = '(All Games)'

	def lookup(self):
		pass
		
	def gamelist(self):
		cur.execute("select game.id, game.name, game.path, game.emu_id, game.gamesystem_id from game order by game.name")
		
		gl = []
		
		for r in cur:
			i, n, p, e, s = r
			gl.append(GameInfo(i, n, p, e, s))
		
		return gl

class Playlist(object):
	def __init__(self, id=None, name=None):
		if id == None and name == None:
			raise ValueError, "Either name or id must be specified"
		self.id = id
		self.name = name
		self.gamelist_cache = None
		
	def lookup(self):
		if self.name != None:
			cur.execute("select id from playlist where name = ?", [self.name])
		else:
			cur.execute("select name from playlist where id = ?", [self.id])
		
		rs = cur.fetchall()
		if len(rs) > 1:
			raise ValueError, "Non unique name for playlist"
		else:
			raise ValueError, "Playlist not found"
		
		if self.name == None:
			self.name = rs[0][0]
		else:
			self.id = rs[0][0]
		
	def gamelist(self):
		if self.gamelist_cache != None:
			return self.gamelist_cache
			
		cur.execute("select game.id, game.name, game.path, game.emu_id, game.gamesystem_id from game, playlist_game where playlist_game.game_id = game.id and playlist_game.playlist_id = ? order by game.name", [self.id])
		
		gl = []
		
		for r in cur:
			i, n, p, e, s = r
			gl.append(GameInfo(i, n, p, e, s))
		
		# enabling this could cause huge memory usage, but make things faster
		#self.gamelist_cache = gl
		return gl
		
def load_playlists():
	global playlist_list
	dblayer.connect()
	cur.execute("select id, name from playlist order by name")
	pl = [AllGames_Playlist()]
	playlist_table[-1] = pl[0]
	for r in cur:
		id, name = r
		p = Playlist(id, name)
		pl.append(p)
		playlist_table[id] = p
	
	playlist_list = pl	

def load_emulators():
	dblayer.connect()
	cur.execute("select id, name, path, options from emulator")
	for r in cur:
		id, name, path, options = r
		ei = EmulatorInfo(id, name, path, options)
		emulator_table[id] = ei
		
	cur.execute("select id, name, fileext from gamesystem")
	for r in cur:
		id, name, fileext = r
		gsi = GamesystemInfo(id, name, fileext)
		gamesystem_table[id] = gsi
		
	cur.execute("select gamesystem_id, emulator_id from gamesystem_emulator")
	for r in cur:
		gsid, eid = r
		gamesystem_table[gsid].emu_id = eid
		emulator_table[eid].system_id = gsid

def find_emu(emu):
	if not os.environ.has_key('PATH'):
		paths = ['.']
	else:
		paths = os.environ['PATH'].split(os.pathsep) + ['.']
	
	for path in paths:
		if os.path.exists(os.path.join(path, emu)):
			return os.path.abspath(os.path.join(path, emu))
	return None

def initialize_emulator_row(emulator, gamesystem):
	cur.execute("insert into emulator (name, path, options) values (?, ?, ?)", [emulator.name, emulator.path, emulator.options])
	emulator.id = cur.lastrowid
	cur.execute("insert into gamesystem (name, fileext) values (?, ?)", [gamesystem.name, ';'.join(gamesystem.fileexts)])
	gamesystem.id = cur.lastrowid
	cur.execute("insert into gamesystem_emulator (gamesystem_id, emulator_id) values (?, ?)", [gamesystem.id, emulator.id])
	
def initialize_emulator_table():
	emulist = [(('SNES','.SMC'),'snes9x','snes9x-sdl','snes9x-x11','snes9x-gtk','zsnes'),(('NES','.NES'),'fceu'),(('Genesis','.BIN'),'dgen'),(('MAME','**MAME**'),'xmame')]
	for emutype in emulist:
		system, fileext = emutype[0]
		for emu in emutype[1:]:
			emupath = find_emu(emu)
			if emupath:
				initialize_emulator_row(EmulatorInfo(None, emu, emupath, ''), GamesystemInfo(None, system, fileext))

def scan_zip(path):
	zf = ZipFile(path, "r")
	zfl = zf.namelist()
	zf.close()
	if len(zfl) > 1:
		return "**MAME**"
	elif zfl:
		return os.path.splitext(zfl[0])[1].upper()
	else:
		return None

def autoload_data(path, playlist, system=None, emulator=None):
	fileext_map = {}
	if system == None:
		for gsi in gamesystem_table.values():
			for fe in gsi.fileexts:
				fileext_map[fe.upper()] = gsi
	print fileext_map
	for base, dirs, files in os.walk(path):
		for file in files:
			fn, fe = os.path.splitext(file)
			feu = fe.upper()

			if feu == '.ZIP':
				feu = scan_zip(os.path.join(path, base, file))
				if not feu:
					continue
			autosystem = None
			if feu in fileext_map:
				autosystem = fileext_map[feu]
			if system != None:
				autosystem = system
			if autosystem != None:
				"We have a valid game, we know what system it's for, and we will use that system's default emulator"
				emuid = None
				if emulator != None:
					emuid = emulator.id
				sysid = None
				if autosystem != None:
					sysid = autosystem.id
				cur.execute("insert into game (name, path, emu_id, gamesystem_id) values (?, ?, ?, ?)", [fn, os.path.join(path, base, file), emuid, sysid])
				gameid = cur.lastrowid
				cur.execute("insert into playlist_game (game_id, playlist_id) values (?, ?)", [gameid, playlist.id])
					
					
def get_game(idnum):
	cur.execute("select game.id, game.name, game.path, game.emu_id, game.gamesystem_id from game where game.id = ? order by game.name", [idnum])
	
	rs = cur.fetchall()
	if len(rs) > 1:
		raise ValueError, "Non unique id for game, multiple games matched"
	elif len(rs) == 0:
		raise ValueError, "Game not found"
	i, n, p, e, s = rs[0]
	gi = GameInfo(i, n, p, e, s)

	return gi
