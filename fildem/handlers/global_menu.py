import gi
import time

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio

from fildem.utils.wayland import is_wayland


def get_separator():
	return u'\u0020\u0020\u00BB\u0020\u0020'


def inject_custom_style(widget, style_string):
	provider = Gtk.CssProvider()
	provider.load_from_data(style_string.encode())

	screen   = Gdk.Screen.get_default()
	priority = Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
	Gtk.StyleContext.add_provider_for_screen(screen, provider, priority)


def parse_accel(accel: str):
	if accel == '':
		return None
	elif accel.lower() == 'del':
		# So hardcoded that it hurts (blame qbittorrent)
		return 65535, Gdk.ModifierType(0)
	else:
		return Gtk.accelerator_parse(accel)


class Menu(Gtk.Menu):

	def __init__(self, tree, node, accel_group, activate_callback=None, *args, **kwargs):
		"""
		tree: Tree
		node: Node
		accel_group: Gtk.AccelGroup
		activate_callback: Callable[[str], None]
			If None the action `'app.' + item.action` is used on the MenuItem
		"""
		super(Gtk.Menu, self).__init__(*args, **kwargs)
		self.accel_group = accel_group
		self.callback = activate_callback
		self.tree = tree
		self.node = node
		self.add_items(tree, node)
		self.show_all()

	def add_items(self, tree, node):
		current_section = None
		for c in tree.children(node.identifier):
			# Separator for Gtk apps
			if current_section is not None and c.data.section != current_section:
				self.append(Gtk.SeparatorMenuItem())
			current_section = c.data.section

			if c.is_leaf():
				menu_item = self._create_item(c.data)
			else:
				menu_item = self._create_sub_menu(c)
				menu_item.set_label(c.tag)

			self.append(menu_item)

	def _create_sub_menu(self, node):
		menu = Menu(self.tree, node, self.accel_group, self.callback)
		menu_item = Gtk.MenuItem()
		menu_item.set_submenu(menu)
		menu_item.set_use_underline(True)
		return menu_item

	def _create_item(self, item):
		"""
		Parameters
		----------
		item: Union[DbusGtkMenuItem, DbusAppMenuItem]

		Returns
		-------
		Gtk.MenuItem
		"""
		if item.separator:
			return Gtk.SeparatorMenuItem()
		elif item.toggle_type == 'radio':
			menu_item = Gtk.RadioMenuItem()
		elif item.toggle_type == 'checkmark':
			menu_item = Gtk.CheckMenuItem()
		elif item.toggle_type == '':
			menu_item = Gtk.MenuItem()

		if item.toggle_state:
			menu_item.set_active(True)

		menu_item.set_accel_path('<MyApp>/Options')
		if self.callback is None:
			menu_item.set_property('action_name', 'app.' + str(item.action))
		else:
			menu_item.connect('activate', self.callback)

		shortcut = parse_accel(item.accel)
		if shortcut is not None:
			menu_item.add_accelerator('activate', self.accel_group, shortcut[0], shortcut[1], Gtk.AccelFlags.VISIBLE)
		
		menu_item.set_label(item.label)
		menu_item.set_use_underline(True)
		return menu_item


class CommandWindow(Gtk.ApplicationWindow):

	wayland = is_wayland()

	def __init__(self, *args, **kwargs):
		kwargs['type'] = Gtk.WindowType.POPUP
		super(Gtk.ApplicationWindow, self).__init__(*args, **kwargs)
		self.app = kwargs['application']
		self.seat = Gdk.Display.get_default().get_default_seat()

		self.set_size_request(-1, -1)
		self.set_keep_above(True)
		self.set_resizable(False)

		self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
		self.set_position(Gtk.WindowPosition.CENTER)
		self.set_custom_position()

		self.set_skip_pager_hint(True)
		self.set_skip_taskbar_hint(True)
		self.set_destroy_with_parent(True)

		self.set_decorated(False)

		self.my_menu_bar = Gtk.MenuBar()
		self.accel_group = Gtk.AccelGroup()

		self.main_box = Gtk.VBox()
		self.main_box.add(self.my_menu_bar)

		self.add(self.main_box)
		# self.set_dark_variation()
		self.set_custom_styles()

		Gdk.event_handler_set(self.on_gdk_event)

		self.connect('show', self.on_window_show)
		self.connect('button-press-event', self.on_button_press_event)

	def open_menu_shortcut(self, menu):
		self.make_opaque()
		self.grab_keyboard(self.get_window())
		self.my_menu_bar.select_item(menu) # activate_item(menu)

	def open_menu_by_name(self, name):
		name = name.replace('_', '')
		for menu in self.my_menu_bar.get_children():
			if menu.get_label().replace('_', '') == name:
				self.open_menu_shortcut(menu)
				break

	def open_menu_by_character(self, char):
		for menu in self.my_menu_bar.get_children():
			label = menu.get_label()
			idx = label.find('_')
			if idx != -1 and label[idx + 1] == char:
				self.open_menu_shortcut(menu)
				break

	def set_tree_menu(self, tree):
		self.destroy_menus()
		children = tree.children(tree[tree.root].identifier)
		for c in children:
			menu = Menu(tree, c, self.accel_group)
			button = Gtk.MenuItem()
			button.set_label(c.tag)
			button.set_use_underline(True)
			button.set_submenu(menu) # set_popup(menu)
			button.show_all()
			button.set_can_focus(True)
			self.my_menu_bar.append(button)

	def destroy_menus(self):
		self.main_box.remove(self.my_menu_bar)
		self.my_menu_bar = Gtk.MenuBar()
		self.main_box.add(self.my_menu_bar)

	def set_custom_position(self, x=-1, y=0):
		position = self.get_position()
		x = x if x != -1 else position.root_x
		self.move(x, y)

	def set_dark_variation(self):
		settings = Gtk.Settings.get_default()
		settings.set_property('gtk-application-prefer-dark-theme', True)

	def set_custom_styles(self):
		styles = """entry.search.flat { border: 0; outline: 0;
			border-image: none; box-shadow: none; }

			headerbar { box-shadow: none; background: @insensitive_bg_color;
				border-radius: 0; border-width: 0 0 1px 0; }

			scrolledwindow overshoot, scrolledwindow undershoot {
				background: none; box-shadow: none; }

			scrollbar { opacity: 0; }

			menubar { background-color: #1d1d1d; }
			menubar > menuitem { min-height: 1em; }

			window decoration { box-shadow: none; border-color: @borders;
				border-style: solid; border-width: 1px; border-radius: 0; }
		"""

		inject_custom_style(self, styles)

	def grab_keyboard(self, window, status=Gdk.GrabStatus.SUCCESS):
		if self.wayland:
			return

		while self.seat.grab(window, Gdk.SeatCapabilities.KEYBOARD, False, None, None, None) != status:
			time.sleep(0.1)

	def ungrab_keyboard(self):
		if self.wayland:
			return

		self.seat.ungrab()

	def emulate_focus_out_event(self):
		tstamp = Gdk.CURRENT_TIME
		self.seat.ungrab()

		fevent = Gdk.Event(Gdk.EventType.FOCUS_CHANGE)
		self.emit('focus-out-event', fevent)

	def clicked_inside(self, event):
		size    = self.get_size()
		x_range = range(0, size.width)
		y_range = range(0, size.height)

		return int(event.x) in x_range and int(event.y) in y_range

	def on_gdk_event(self, event):
		Gtk.main_do_event(event)

	def on_window_show(self, window):
		window = self.get_window()
		status = Gdk.GrabStatus.SUCCESS
		tstamp = Gdk.CURRENT_TIME

		self.grab_keyboard(window, status)

	def on_button_press_event(self, widget, event):
		win_type = event.get_window().get_window_type()
		tmp_type = Gdk.WindowType.TEMP

		if win_type == tmp_type and not self.clicked_inside(event):
			self.emulate_focus_out_event()
			return True

	def make_opaque(self):
		self.set_opacity(1)

	def make_transparent(self):
		self.set_opacity(0)


class GlobalMenu(Gtk.Application):

	def __init__(self, dbus_menu, initial_menu=None, x=-1, *args, **kwargs):
		kwargs['application_id'] = 'org.gonzaarcr.fildemapp'
		super(Gtk.Application, self).__init__(*args, **kwargs)

		self.dbus_menu = dbus_menu
		self.actions = []
		self.initial_menu = initial_menu
		self.initial_x = x

		self.set_accels_for_action('app.quit', ['Escape'])
		self.set_accels_for_action('app.prev', ['Up'])
		self.set_accels_for_action('app.next', ['Down'])
		self.set_accels_for_action('app.execute', ['Return'])

	def add_simple_action(self, name, callback):
		action = Gio.SimpleAction.new(name, None)

		action.connect('activate', callback)
		self.add_action(action)

	def do_startup(self):
		Gtk.Application.do_startup(self)
		self.window = CommandWindow(application=self, title='Gnome HUD')
		self.add_simple_action('start', self.on_show_window)
		self.add_simple_action('quit', self.on_hide_window)
		self.add_simple_action('execute', self.on_execute_command)

	def do_activate(self):
		self.remove_all_actions()
		self.add_menus()
		if self.initial_menu is not None:
			self.on_menu_activated(self.initial_menu, self.initial_x)
		self.window.connect('focus-out-event', self.on_hide_window)

	def add_menus(self):
		for item in self.dbus_menu.tree.leaves():
			self.add_menu_action(item.data)

		self.window.set_tree_menu(self.dbus_menu.tree)
		self.window.show_all()

	def add_menu_action(self, item):
		"""
		Adds an action of the foreign app. Do not add actions
		of the app here
		"""
		name = str(item.action)
		path = item.path
		self.actions.append(name)
		action = Gio.SimpleAction.new(name, None)
		action.set_enabled(item.enabled)
		path = get_separator().join(path) + get_separator() + item.label
		callback = lambda a, b: self.dbus_menu.activate(path)
		action.connect('activate', callback)
		self.add_action(action)

	def remove_all_actions(self):
		for name in self.actions:
			self.remove_action(name)
		self.actions = []

	def on_show_window(self, *args):
		print('GlobalMenu.on_show_window')
		self.window.show()

	def on_hide_window(self, *args):
		self.window.destroy()
		self.quit()

	def on_execute_command(self, *args):
		self.dbus_menu.activate(self.commands.select_value)
		self.on_hide_window()

	def move_window(self, x: int):
		primary_mon = Gdk.Display.get_default().get_primary_monitor()
		if primary_mon == None:
			# Sometimes Wayland returns None
			# It seems to be no way of knowing the primary monitor,
			# we just grab the first one
			primary_mon = Gdk.Display.get_default().get_monitor(0)

		x = primary_mon.get_geometry().x + x / primary_mon.get_scale_factor()
		self.window.set_custom_position(x)

	def on_menu_activated(self, menu: str, x: int):
		self.move_window(x)
		if len(menu) > 1:
			self.window.open_menu_by_name(menu)
		else:
			self.window.open_menu_by_character(menu)
		self.window.make_transparent()
