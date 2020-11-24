import gi
import dbus
import time

gi.require_version('Keybinder', '3.0')

from gi.repository import Keybinder

from utils.fuzzy import match_replace
from utils.window import WindowManager
from utils.service import MyService
from handlers.global_menu import GlobalMenu


def format_label(parts):
	separator = u'\u0020\u0020\u00BB\u0020\u0020'
	return separator.join(parts)


class DbusGtkMenuItem(object):

	def __init__(self, item, path=[], enabled=True):
		self.path   = path
		self.separator = False
		self.action = str(item.get('action', ''))
		self.accel  = str(item.get('accel', '')) # <Primary><Shift><Alt>p
		self.shortcut = str(item.get('shortcut', ''))
		self.label  = item.get('label', '')
		self.text   = format_label(self.path + [self.label])
		self.enabled = enabled
		self.toggle_type = ''
		self.toggle_state = False
		# :submenu
		# two index that indicate the group
		# dbus.String(':submenu'): dbus.Struct((dbus.UInt32(11), dbus.UInt32(0))
		# used for separators and radio button groups
		self.section = None

	def set_toggle(self, toggle):
		if not len(toggle):
			return
		toggle = toggle[0]
		if isinstance(toggle, dbus.Boolean):
			self.toggle_type = 'checkmark'
			self.toggle_state = toggle
		elif isinstance(toggle, str):
			self.toggle_type = 'radio'
			self.toggle_state = len(toggle) > 0

class DbusGtkMenu(object):

	def __init__(self, session, window):
		self.results      = {}
		self.actions      = {}
		self.accels       = {}
		self.items        = []
		self.session      = session
		self.bus_name     = window.get_utf8_prop('_GTK_UNIQUE_BUS_NAME')
		# with app. prefix
		self.app_path     = window.get_utf8_prop('_GTK_APPLICATION_OBJECT_PATH')
		# with win. prefix
		self.win_path     = window.get_utf8_prop('_GTK_WINDOW_OBJECT_PATH')
		# with unity. prefix
		self.menubar_path = window.get_utf8_prop('_GTK_MENUBAR_OBJECT_PATH')
		self.appmenu_path = window.get_utf8_prop('_GTK_APP_MENU_OBJECT_PATH')

	def activate(self, selection):
		action = self.actions.get(selection, '')

		if 'app.' in action:
			self.send_action(action, 'app.', self.app_path)
		elif 'win.' in action:
			self.send_action(action, 'win.', self.win_path)
		elif 'unity.' in action:
			self.send_action(action, 'unity.', self.menubar_path)

	def send_action(self, name, prefix, path):
		object    = self.session.get_object(self.bus_name, path)
		interface = dbus.Interface(object, dbus_interface='org.gtk.Actions')

		interface.Activate(name.replace(prefix, ''), [], dict())

	def get_results(self):
		paths = [self.appmenu_path, self.menubar_path]

		for path in filter(None, paths):
			object    = self.session.get_object(self.bus_name, path)
			interface = dbus.Interface(object, dbus_interface='org.gtk.Menus')
			try:
				results   = interface.Start([x for x in range(1024)])
			except Exception:
				continue
			# interface.End([x for x in range(1024)])

			for menu in results:
				self.results[(menu[0], menu[1])] = menu[2]

		self.collect_entries([0, 0])

	def collect_entries(self, menu, labels=[]):
		section = (menu[0], menu[1])
		for menu in self.results.get(section, []):
			if 'label' in menu:
				menu_item = DbusGtkMenuItem(menu, labels)
				menu_item.section = section
				description = self.describe(menu_item.action)
				if description is not None:
					menu_item.enabled = description[0]
					menu_item.set_toggle(description[1])

				menu_path = labels + [menu_item.label]

				if ':submenu' in menu:
					self.collect_entries(menu[':submenu'], menu_path)
				elif 'action' in menu:
					self.actions[menu_item.text] = menu_item.action
					self.items.append(menu_item)

			elif ':section' in menu:
				self.collect_entries(menu[':section'], labels)

	def describe(self, action):
		"""
		Describe return this:
		dbus.Struct((
		 dbus.Boolean(True), # enabled
		 dbus.Signature(''),
		 dbus.Array([ # This is empty in a not checked item
		  dbus.Boolean(True, variant_level=1)], # Checked or not
		  signature=dbus.Signature('v'))),
		 signature=None)
		"""
		if action.startswith('unity'):
			path = self.menubar_path
		elif action.startswith('win'):
			path = self.win_path
		elif action.startswith('app'):
			path = self.app_path
		else:
			return None

		dot = action.find('.')
		action = action[dot+1:]
		object    = self.session.get_object(self.bus_name, path)
		interface = dbus.Interface(object, dbus_interface='org.gtk.Actions')

		try:
			description = interface.Describe(action)
		except Exception as e:
			# import traceback; traceback.print_exc()
			return None
		enabled = description[0]
		checked = description[2]
		return enabled, checked


class DbusAppMenuItem(object):

	def __init__(self, item, path=[]):
		self.path   = path
		self.action = int(item[0])
		self.accel  = self.get_shorcut(item[1])
		self.separator = item[1].get('type', '') == 'separator'
		self.label  = item[1].get('label', '')
		self.text   = format_label(self.path + [self.label])
		self.enabled = item[1].get('enabled', True)
		self.visible = item[1].get('visible', True)
		self.toggle_state = item[1].get('toggle-state', 0) == 1
		self.toggle_type = item[1].get('toggle-type', '') # 'radio' or 'checkmark'
		self.icon_data = item[1].get('icon_data', bytearray())
		# Only used on Gtkapps
		self.section = None

	def get_shorcut(self, item):
		shortcut = item.get('shortcut', '')
		if len(shortcut) == 0:
			return shortcut

		shortcut = shortcut[0]
		ret = ''
		for i, v in enumerate(shortcut):
			# The last one should be on caps?
			ret += '<' + v + '>' if (i != len(shortcut) - 1) else v
		return ret

class DbusAppMenu(object):

	def __init__(self, session, window):
		self.actions   = {}
		self.accels    = {}
		self.items     = []
		self.session   = session
		self.window    = window
		self.interface = self.get_interface()

	def activate(self, selection):
		action = self.actions[selection]
		try:
			self.interface.Event(action, 'clicked', 0, 0)
		except Exception as e:
			self.retry_activate(selection)

	def retry_activate(self, selection):
		# Electron apps change a lot their menus, we have to update to retry
		self.actions = {}
		self.accels = {}
		self.items = []
		results = self.interface.GetLayout(0, -1, dbus.Array(signature="s"))
		self.collect_entries(results[1], [])
		action = self.actions[selection]
		self.interface.Event(action, 'clicked', 0, 0)

	def get_interface(self):
		bus_name = 'com.canonical.AppMenu.Registrar'
		bus_path = '/com/canonical/AppMenu/Registrar'

		try:
			object     = self.session.get_object(bus_name, bus_path)
			interface  = dbus.Interface(object, bus_name)
			name, path = interface.GetMenuForWindow(self.window.get_xid())
			object     = self.session.get_object(name, path)
			interface  = dbus.Interface(object, 'com.canonical.dbusmenu')

			return interface
		except dbus.exceptions.DBusException:
			# import traceback; traceback.print_exc()
			return None

	def get_results(self):
		if self.interface:
			results = self.interface.GetLayout(0, -1, dbus.Array(signature="s"))
			try:
				self.collect_entries(results[1], [])
			except Exception:
				pass

	def collect_entries(self, item=None, labels=[]):
		menu_item = DbusAppMenuItem(item, labels)
		menu_path = labels

		if 'children-display' in item[1]:
			item_id = item[0]
			self.interface.AboutToShow(item_id)
			self.interface.Event(item_id, 'opened', 'not used', dbus.UInt32(time.time()))
			item = self.interface.GetLayout(item_id, -1, dbus.Array(signature="s"))[1]

		if bool(menu_item.label) and menu_item.label != 'Root':
			menu_path = labels + [menu_item.label]

		if len(item[2]):
			for child in item[2]:
				self.collect_entries(child, menu_path)

		elif bool(menu_item.label) or menu_item.separator:
			self.actions[menu_item.text] = menu_item.action
			self.items.append(menu_item)

class DbusMenu:

	def __init__(self):
		self.keyb = GlobalKeybinder(self.on_keybind_activated)
		self.app = None
		self.session = dbus.SessionBus()
		self.window = WindowManager.new_window()
		self._init_window()
		self._listen_menu_activated()
		self._width_offset = 300
		WindowManager.add_listener(self.on_window_switched)

	def _init_window(self):
		self.appmenu = DbusAppMenu(self.session, self.window)
		self.gtkmenu = DbusGtkMenu(self.session, self.window)
		self._update()

	def on_window_switched(self, window):
		self.window = window
		self._init_window()

	def _listen_menu_activated(self):
		proxy  = self.session.get_object(MyService.BUS_NAME, MyService.BUS_PATH)
		signal = proxy.connect_to_signal("MenuActivated", self.on_menu_activated)

	def on_menu_activated(self, menu: str, x: int):
		if menu == '__fildem_move':
			self._move_menu(x)
			return

		if x != -1:
			self._width_offset = x
		self._start_app(menu)

	def on_keybind_activated(self, character: str):
		self.on_app_started()
		self._start_app(character)

	def _move_menu(self, x: int):
		if self.app is None:
			return

		self.app.move_window(x) 

	def _start_app(self, menu_activated: str):
		if self.app is None:
			self.app = GlobalMenu(self, menu_activated, self._width_offset)
			self.app.connect('shutdown', self.on_app_shutdown)
			self.app.run()

	def on_app_started(self):
		self._echo_onoff(True)

	def on_app_shutdown(self, app):
		self._echo_onoff(False)
		self.app = None

	def _echo_onoff(self, on: bool):
		self.proxy = dbus.SessionBus().get_object(MyService.BUS_NAME, MyService.BUS_PATH)
		self.proxy.EchoMenuOnOff(on)

	def _handle_shortcuts(self, top_level_menus):
		self.keyb.remove_all_keybindings()
		for label in top_level_menus:
			idx = label.find('_')
			if idx == -1:
				continue
			c = label[idx + 1]
			self.keyb.add_keybinding(c)

	def _update_menus(self):
		self.gtkmenu.get_results()
		if not len(self.appmenu.items):
			self.appmenu.get_results()

	def _update(self):
		self._update_menus()
		top_level_menus = list(dict.fromkeys(map(lambda it: it.path[0] if len(it.path) > 0 else None, self.items)))
		top_level_menus = list(filter(lambda x: x is not None, top_level_menus))
		self._handle_shortcuts(top_level_menus)
		self._send_msg(top_level_menus)

	def _send_msg(self, top_level_menus):
		if len(top_level_menus) == 0:
			top_level_menus = dbus.Array(signature="s")
		proxy  = self.session.get_object(MyService.BUS_NAME, MyService.BUS_PATH)
		proxy.EchoSendTopLevelMenus(top_level_menus)

	@property
	def prompt(self):
		return self.window.get_app_name()

	@property
	def actions(self):
		actions = self.gtkmenu.actions
		if not len(actions):
			actions = self.appmenu.actions

		self.handle_empty(actions)

		return actions.keys()

	def accel(self):
		accel = self.gtkmenu.accels
		if not len(accel):
			accel = self.appmenu.accels
		return accel

	@property
	def items(self):
		items = self.appmenu.items
		if not len(items):
			items = self.gtkmenu.items
		return items

	def activate(self, selection):
		if selection in self.gtkmenu.actions:
			self.gtkmenu.activate(selection)

		elif selection in self.appmenu.actions:
			self.appmenu.activate(selection)

	def handle_empty(self, actions):
		if not len(actions):
			alert = 'No menu items available!'
			promt = ''
			try:
				promt = self.prompt
			except Exception as e:
				pass
			print('Gnome HUD: WARNING: (%s) %s' % (promt, alert))


class GlobalKeybinder(object):
	"""
	Global keybinder for mnemonic, like Alt+F for files, etc.
	"""
	def __init__(self, callback=None):
		super(GlobalKeybinder, self).__init__()
		Keybinder.init()
		self.keybinding_strings = []
		self.keybinder_callback = callback

	def add_keybinding(self, character):
		acc = '<Alt>' + character
		Keybinder.bind(acc, lambda accelerator: self.on_keybind_activated(character))
		self.keybinding_strings.append(acc)

	def on_keybind_activated(self, char):
		self.keybinder_callback(char)

	def remove_all_keybindings(self):
		for k in self.keybinding_strings:
			Keybinder.unbind(k)
		self.keybinding_strings = []


class WindowActions(object):
	"""Window actions from the shell from the alt-space menu"""
	def __init__(self, callback=None):
		super(WindowActions, self).__init__()

		self.listeners = []
		if callback is not None:
			self.listeners.append(callback)

		session = dbus.SessionBus()
		self.proxy = session.get_object(MyService.BUS_NAME, MyService.BUS_PATH)
		self.actions = []
		signal = self.proxy.connect_to_signal("ListWindowActionsSignal", self.on_actions_receive)

	def request_window_actions(self):
		self.proxy.RequestWindowActions()

	def on_actions_receive(self, actions):
		self.actions = actions
		for callback in self.listeners:
			callback(actions)

	def activate_action(self, action):
		self.proxy.ActivateWindowAction(action)
