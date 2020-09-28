
import gi

gi.require_version('AppIndicator3', '0.1')
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import AppIndicator3

from handlers.global_menu import Menu


class AppIndicator(object):
	# We can’t remove indicators, as far as I know,
	# so we recycle them. The application with most menu
	# that I‘ve seen is GIMP and LibreOofice with 11
	indicatorIds = []
	indicatorPool = []

	ICON_NAME = 'system-search'

	def __init__(self, menus):
		super(AppIndicator, self).__init__()
		self.indicators = []

		for idx in range(len(menus)):
			menu = menus[idx]['menu']
			label = menus[idx]['label']
			if idx >= len(self.indicatorPool):
				self._create_indicator(label + '-fildem')

			indicator = self.indicatorPool[idx]
			indicator.set_title(label + '-fildem')
			indicator.set_menu(menu)
			indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

	def _create_indicator(self, indicator_id):
		indicator = AppIndicator3.Indicator.new(indicator_id, self.ICON_NAME, AppIndicator3.IndicatorCategory.SYSTEM_SERVICES)
		self.indicatorPool.append(indicator)
		self.indicatorIds.append(indicator_id)

	def hide_all(self):
		for indicator in self.indicatorPool:
			indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)
			indicator.set_menu(Gtk.Menu())


class MainApp(object):
	"""docstring for MainApp"""
	def __init__(self, dbus_menu):
		super(MainApp, self).__init__()
		self.dbus_menu = dbus_menu
		self.dbus_menu.add_window_switch_listener(self.on_window_switched)
		self.indicator_manager = AppIndicator([])
		self.on_window_switched()

	def do_activate(self):
		ac = self.dbus_menu.actions
		self.set_menu(self.dbus_menu.items)

	def set_menu(self, menus):
		self.indicator_manager.hide_all()
		indicator_builder = []
		if len(menus) == 0:
			return
		current_prefix = menus[0].path[0]
		current_menu = []
		for item in menus:
			if item.path[0] == current_prefix:
				current_menu.append(item)
			else:
				indicator_builder.append(self.create_menu(current_prefix, current_menu))
				current_menu = [ item ]
				current_prefix = item.path[0]
		else:
			indicator_builder.append(self.create_menu(current_prefix, current_menu))

		self.indicator_manager = AppIndicator(indicator_builder)

	def create_menu(self, name, current_menu):
		if len(current_menu) == 0:
			return
		menu = Menu(current_menu, 1, Gtk.AccelGroup(), self.item_activated)
		menu.show_all()
		return {'menu': menu, 'label': name}

	def item_activated(self, menu_item):
		print(dir(menu_item))
		print(menu_item.path)
		print(menu_item.get_path)

	def on_window_switched(self):
		self.do_activate()
