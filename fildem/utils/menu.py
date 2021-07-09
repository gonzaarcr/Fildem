import dbus

from gi.repository import GLib

from fildem.utils.global_keybinder import GlobalKeybinder
from fildem.utils.window import WindowManager
from fildem.utils.service import MyService

from fildem.handlers.default import HudMenu
from fildem.handlers.global_menu import GlobalMenu

from fildem.menu_model.menu_model import MenuModel


class DbusMenu:

	def __init__(self):
		self.keyb = GlobalKeybinder.create(self.on_keybind_activated)
		self.app = None
		self.session = dbus.SessionBus()
		self.window = WindowManager.new_window()
		self.tries = 0
		self.retry_timer_id = 0
		self.collect_timer = 0
		self._menu_model = None

		self._init_window()
		self._listen_menu_activated()
		self._listen_hud_activated()
		WindowManager.add_listener(self.on_window_switched)

	def _init_window(self):
		self._menu_model = MenuModel(self.session, self.window)
		self._update()

	def on_window_switched(self, window):
		self.reset_timeout()
		self.window = window
		self._init_window()

	def reset_timeout(self):
		if self.retry_timer_id:
			GLib.source_remove(self.retry_timer_id)
		self.tries = 0
		self.retry_timer_id = 0

		if self.collect_timer:
			GLib.source_remove(self.collect_timer)

	def _listen_menu_activated(self):
		proxy = self.session.get_object(MyService.BUS_NAME, MyService.BUS_PATH)
		signal = proxy.connect_to_signal("MenuActivated", self.on_menu_activated)

	def _listen_hud_activated(self):
		proxy = self.session.get_object(MyService.BUS_NAME, MyService.BUS_PATH)
		signal = proxy.connect_to_signal("HudActivated", self.on_hud_activated)

	def on_menu_activated(self, menu: str, x: int):
		if menu == '__fildem_move':
			self._move_menu(x)
			return

		if x != -1:
			self._start_app(menu, x)
		else:
			self._start_app(menu)

	def on_hud_activated(self):
		menu = HudMenu(self)
		menu.run()

	def on_keybind_activated(self, character: str):
		self.on_app_started()
		self._start_app(character)

	def _move_menu(self, x: int):
		if self.app is None:
			return

		self.app.move_window(x)

	def _start_app(self, menu_activated: str, offset=300):
		if self.app is None:
			self.app = GlobalMenu(self, menu_activated, offset)
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

	def _retry_init(self):
		self.retry_timer_id = 0
		self._init_window()
		return False

	def _update_menus(self):
		self._menu_model._update_menus()

		max_tries = 2
		if self.tries < max_tries and self.tree.root is None:
			self.tries += 1
			self.retry_timer_id = GLib.timeout_add_seconds(2, self._retry_init)

	def _update(self):
		self._update_menus()
		self._handle_shortcuts(self._menu_model.top_level_menus)
		self._send_msg(self._menu_model.top_level_menus)

	def _send_msg(self, top_level_menus):
		if len(top_level_menus) == 0:
			top_level_menus = dbus.Array(signature="s")
		proxy = self.session.get_object(MyService.BUS_NAME, MyService.BUS_PATH)
		proxy.EchoSendTopLevelMenus(top_level_menus)

	@property
	def prompt(self):
		return self.window.get_app_name()

	@property
	def actions(self):
		return self._menu_model.actions

	def accel(self):
		return self._menu_model.accel

	@property
	def tree(self):
		return self._menu_model.tree

	def activate(self, selection):
		self._menu_model.activate(selection)
