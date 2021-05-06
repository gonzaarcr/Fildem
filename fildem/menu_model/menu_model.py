#!/usr/bin/python3

import dbus
import time

from fildem.menu_model.menu_item import DbusGtkMenuItem, DbusAppMenuItem

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

		self.top_level_menus = []

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
				interface.End([x for x in range(1024)])
			except Exception:
				continue

			for menu in results:
				self.results[(menu[0], menu[1])] = menu[2]

		self.collect_entries()

	def collect_entries(self, menu=(0, 0), labels=[]):
		section = (menu[0], menu[1])
		for menu in self.results.get(section, []):
			if 'label' in menu:
				if len(labels) == 0:
					self.top_level_menus.append(menu.get('label', None))

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


class DbusAppMenu(object):

	def __init__(self, session, window):
		self.actions   = {}
		self.accels    = {}
		self.items     = []
		self.session   = session
		self.window    = window
		self.interface = self.get_interface()
		self.top_level_menus = []
		self.results = None

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
			self.results = self.interface.GetLayout(0, -1, dbus.Array(signature="s"))
			try:
				self.collect_entries(self.results[1])
			except Exception:
				pass

	def collect_entries(self, item=None, labels=None):
		if self.results is None:
			return
		if item is None:
			item = self.results[1]
		if labels is None:
			labels = []
		menu_item = DbusAppMenuItem(item, labels)
		menu_path = labels

		if 'children-display' in item[1]:
			item_id = item[0]
			try:
				self.interface.AboutToShow(item_id)
			except Exception:
				pass
			self.interface.Event(item_id, 'opened', 'not used', dbus.UInt32(time.time()))
			item = self.interface.GetLayout(item_id, -1, dbus.Array(signature="s"))[1]

		if bool(menu_item.label) and menu_item.label != 'Root' and menu_item.label != 'DBusMenuRoot':
			menu_path = labels + [menu_item.label]

		if len(item[2]):
			if not self.top_level_menus:
				self.top_level_menus = list(map(lambda c: c[1].get('label', ''), item[2]))

			for child in item[2]:
				self.collect_entries(child, menu_path)

		elif bool(menu_item.label) or menu_item.separator:
			self.actions[menu_item.text] = menu_item.action
			self.items.append(menu_item)
