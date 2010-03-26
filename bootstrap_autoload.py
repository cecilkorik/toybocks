import backend
import dblayer
import os

if os.path.exists('games.db'):
	os.remove('games.db')
dblayer.connect()
dblayer.create()
backend.initialize_emulator_table()
backend.load_emulators()


base = '/mnt/gamez/Games/Emulators/ROMs/'

for d in ('SNES', 'NES', 'Genesis'):
	system = None
	for gs in backend.gamesystem_table.values():
		if gs.name == d:
			system = gs
	backend.cur.execute("insert into playlist (name) values (?)", [d])
	path = os.path.join(base, d + ' ROMs')
	assert os.path.exists(path)
	
	backend.autoload_data(path, backend.Playlist(backend.cur.lastrowid, d))
	backend.db.commit()
