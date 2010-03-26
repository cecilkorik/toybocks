import mainwnd
import wx
import backend

class customListCtrl(wx.ListCtrl):
	def GetItemBackgroundColour(self, item):
		return None

	def OnGetItemText(self, item, col):
		return self.gamelist[item].name

	def GetItemData(self, item):
		if hasattr(self, "gamelist"):
			return self.gamelist[item].id
		else:
			return wx.ListCtrl.GetItemData(self, item)

mainwnd.customListCtrl = customListCtrl

class ToybocksMainWindow(mainwnd.MainWindow):
	def __init__(self, *args, **kwds):
		mainwnd.MainWindow.__init__(self, *args, **kwds)
		
		self.emulator_thread = None
		

		self.playlists.InsertColumn(0, "Selection")
#		self.playlists.InsertStringItem(0, "(All Games)")
#		self.playlists.InsertStringItem(1, "(None)")
		self.games.InsertColumn(0, "Game")
		self.games.SetColumnWidth(0, 1800)
#		self.games.InsertStringItem(0, "Game One")
#		self.games.InsertStringItem(1, "Testing 123")
#		self.games.InsertStringItem(2, "Entry Test")
#		self.games.InsertStringItem(3, "Listing Items")
#		self.games.InsertStringItem(4, "Game 789")

		backend.load_emulators()
		backend.load_playlists()
		pl = backend.playlist_list
		c = 0
		for p in pl:
			self.playlists.InsertStringItem(c, p.name)
			if p.id != None:
				self.playlists.SetItemData(c, int(p.id))
			else:
				self.playlists.SetItemData(c, -1)
			c += 1
		
		p = pl[0]
			
		self.games.playlist = p
		self.games.gamelist = p.gamelist()
		self.games.SetItemCount(len(self.games.gamelist))
		self.games.RefreshItems(0, len(self.games.gamelist))
		self.playlists.SetColumnWidth(0, 200)
		self.playlists.SetColumnWidth(0, wx.LIST_AUTOSIZE)

		self.playlists.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnChangePlaylist)
		self.playlists.Bind(wx.EVT_LIST_KEY_DOWN, self.OnKeyUp)
		#wx.EVT_LIST_KEY_DOWN(self.playlists, self.OnKeyUp)
		self.playlists.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
		self.games.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
		
		TIMER_ID = 150
		self.timer = wx.Timer(self, TIMER_ID)
		self.Bind(wx.EVT_TIMER, self.OnTimer)

	def OnChangePlaylist(self, event):
		name, id, item = self.GetSelItem(self.playlists)
		p = backend.playlist_table[id]
		self.games.playlist = p
		self.games.gamelist = p.gamelist()
		self.games.SetItemCount(len(self.games.gamelist))
		self.games.RefreshItems(0, len(self.games.gamelist))
		#self.games.SetColumnWidth(0, wx.LIST_AUTOSIZE)


	def OnTimer(self, event):
		ep = self.emulator_thread
		if ep and ep != True:
			if not ep.is_alive():
				self.timer.Stop()
				ep.buffer.write("\nEmulator exited with return code %d\n" % (ep.proc.returncode,))
				self.emulator_thread = None
				item = self.games.FindItemData(-1, ep.game.id)
				self.games.SetItemBackgroundColour(item, self.games.GetBackgroundColour())

	def OnKeyUp(self, event):
		key = event.GetKeyCode()
		
		if key == wx.WXK_RETURN:
			self.OnStartGame(None)
		elif key == wx.WXK_LEFT:
			self.playlists.SetFocus()
		elif key == wx.WXK_RIGHT:
			self.games.SetFocus()
		else:
			event.Skip()
		
	def GetSelItem(self, box):
		item = box.GetNextItem(-1, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
		if item == -1:
			return None
		else:
			return (box.GetItemText(item), box.GetItemData(item), item)
			
	def OnStartGame(self, event):
		if self.emulator_thread:
			return
		self.emulator_thread = True
		name, id, item = self.GetSelItem(self.games)
		print name, id, item
		game = backend.get_game(id)
		emuid = game.emu_id
		if emuid == None:
			emuid = backend.gamesystem_table[game.system_id].emu_id
		emu = backend.emulator_table[emuid]
		proc = emu.start_game(game)
		self.emulator_thread = backend.EmulatorHandlerThread(game, proc)
		self.emulator_thread.start()
		self.timer.Start(1000)
		self.games.SetItemBackgroundColour(item, wx.Colour(196,0,0))

class ToybocksApp(wx.App):
	def OnInit(self):
		wx.InitAllImageHandlers()
		mainwnd = ToybocksMainWindow(None, -1, "")
		self.SetTopWindow(mainwnd)
		mainwnd.Show()
		state = wx.LIST_STATE_FOCUSED|wx.LIST_STATE_SELECTED
		mainwnd.playlists.SetItemState(0, state, state)
		mainwnd.games.SetItemState(0, state, state)
		mainwnd.playlists.SetFocus()
		return 1

app = ToybocksApp(0)
app.MainLoop()
