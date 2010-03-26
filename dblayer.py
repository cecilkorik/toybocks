import sqlite3

class ObjectProxy(object):
	def __init__(self):
		self._realobj = None
	def __setattr__(self, name, value):
		if name in ("_realobj",) or hasattr(self, name):
			object.__setattr__(self, name, value)
		else:
			self._realobj.__setattr__(name, value)
	def __getattribute__(self, name):
		try:
			return object.__getattribute__(self, name)
		except:
			return self._realobj.__getattribute__(name)
	def __repr__(self):
		return """<Proxy for "%s">""" % (repr(self._realobj),)
		
	def __iter__(self):
		return self._realobj.__iter__()

db = ObjectProxy()
cur = ObjectProxy()

def connect():
	if db._realobj != None:
		return
	db._realobj = sqlite3.connect("games.db")
	cur._realobj = db.cursor()

def create():
	cur.execute("""create table playlist (id integer primary key autoincrement, name text)""")
	cur.execute("""create table emulator (id integer primary key autoincrement, name text, path text, options text)""")
	cur.execute("""create table gamesystem (id integer primary key autoincrement, name text, fileext text)""")
	cur.execute("""create table gamesystem_emulator (id integer primary key autoincrement, emulator_id integer, gamesystem_id integer, foreign key (emulator_id) references emulator(id), foreign key (gamesystem_id) references gamesystem(id))""")
	cur.execute("""create table game (id integer primary key autoincrement, name text, path text, emu_id integer, gamesystem_id integer, foreign key (emu_id) references emulator(id), foreign key (gamesystem_id) references gamesystem(id))""")
	cur.execute("""create table playlist_game (id integer primary key autoincrement, game_id integer, playlist_id integer, foreign key (game_id) references game(id), foreign key (playlist_id) references playlist(id))""")
	
