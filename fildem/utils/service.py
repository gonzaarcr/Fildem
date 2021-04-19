import dbus
import dbus.service

from gi.repository import GLib

BUS_NAME = 'com.canonical.AppMenu.Registrar'
BUS_PATH = '/com/canonical/AppMenu/Registrar'


class AppMenuService(dbus.service.Object):
	"""
		Types:
			- u: int
			- a: array
			- y: byte
			- s: string
			- o: DBus object path
			- g: DBus type signature

		https://people.gnome.org/~ryanl/glib-docs/gvariant-format-strings.html
	"""
	def __init__(self):
		self.window_dict = dict()

		bus_name = dbus.service.BusName(BUS_NAME, bus=dbus.SessionBus())
		dbus.service.Object.__init__(self, bus_name, BUS_PATH)

	@dbus.service.method(BUS_NAME, in_signature='uo', sender_keyword='sender')
	def RegisterWindow(self, windowId, menuObjectPath, sender):
		self.window_dict[windowId] = [dbus.String(sender), dbus.ObjectPath(menuObjectPath)]

	@dbus.service.method(BUS_NAME, in_signature='u')
	def UnregisterWindow(self, windowId):
		if windowId in self.window_dict:
			del self.window_dict[windowId]

	@dbus.service.method(BUS_NAME, in_signature='u', out_signature='so')
	def GetMenuForWindow(self, windowId):
		if windowId in self.window_dict:
			return self.window_dict[windowId]

	@dbus.service.method(BUS_NAME, out_signature='a{u(so)}')
	def GetMenus(self):
		return self.window_dict

	@dbus.service.method(BUS_NAME)
	def Q(self):
		GLib.MainLoop().quit()


class MyService(dbus.service.Object):

	BUS_PATH = '/com/gonzaarcr/appmenu'
	BUS_NAME = 'com.gonzaarcr.appmenu'

	def __init__(self):
		self.bus_name = dbus.service.BusName(self.BUS_NAME, bus=dbus.SessionBus())
		dbus.service.Object.__init__(self, self.bus_name, self.BUS_PATH)

	@dbus.service.signal(BUS_NAME, signature='su')
	def MenuActivated(self, menu, x):
		pass

	@dbus.service.method(BUS_NAME, in_signature='su')
	def EchoSignal(self, menu, x):
		self.MenuActivated(menu, x)

	@dbus.service.method(BUS_NAME, in_signature='a{ss}')
	def WindowSwitched(self, window_data):
		self.WindowSwitchedSignal(window_data)

	@dbus.service.signal(BUS_NAME, signature='a{ss}')
	def WindowSwitchedSignal(self, window_data):
		pass

	@dbus.service.method(BUS_NAME, in_signature='as')
	def EchoSendTopLevelMenus(self, top_level_menus):
		self.SendTopLevelMenus(top_level_menus)

	@dbus.service.signal(BUS_NAME, signature='as')
	def SendTopLevelMenus(self, top_level_menus):
		pass

	@dbus.service.method(BUS_NAME, in_signature='b')
	def EchoMenuOnOff(self, on):
		self.MenuOnOff(on)

	@dbus.service.signal(BUS_NAME, signature='b')
	def MenuOnOff(self, on):
		pass

	# Window action stuff (the menu on alt-space)
	@dbus.service.method(BUS_NAME)
	def RequestWindowActions(self):
		self.RequestWindowActionsSignal()

	@dbus.service.signal(BUS_NAME)
	def RequestWindowActionsSignal(self):
		pass

	@dbus.service.method(BUS_NAME, in_signature='as')
	def ListWindowActions(self, action_list):
		self.ListWindowActionsSignal(action_list)

	@dbus.service.signal(BUS_NAME, signature='as')
	def ListWindowActionsSignal(self, top_level_menus):
		pass

	@dbus.service.method(BUS_NAME, in_signature='s')
	def ActivateWindowAction(self, action):
		self.ActivateWindowActionSignal(action)

	@dbus.service.signal(BUS_NAME, signature='s')
	def ActivateWindowActionSignal(self, action):
		pass

	# Needed to activate the hud on wayland
	@dbus.service.method(BUS_NAME)
	def EmitHudActivated(self):
		self.HudActivated()

	@dbus.service.signal(BUS_NAME)
	def HudActivated(self):
		pass
