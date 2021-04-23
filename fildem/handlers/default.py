import gi
import time

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject

from fildem.utils.fuzzy import FuzzyMatch
from fildem.utils.fuzzy import normalize_string
from fildem.utils.fuzzy import match_replace
from fildem.utils.window import WindowActions
from fildem.utils.wayland import is_wayland


def normalize_markup(text):
	return text.replace('_', '').replace('&', '&amp;')


def run_generator(function):
	priority  = GLib.PRIORITY_LOW
	generator = function()

	GLib.idle_add(lambda: next(generator, False), priority=priority)


def inject_custom_style(widget, style_string):
	provider = Gtk.CssProvider()
	provider.load_from_data(style_string.encode())

	screen   = Gdk.Screen.get_default()
	priority = Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
	Gtk.StyleContext.add_provider_for_screen(screen, provider, priority)


def add_style_class(widget, class_names):
	context = widget.get_style_context()
	context.add_class(class_names)


class CommandListItem(Gtk.ListBoxRow):

	value = GObject.Property(type=str)
	index = GObject.Property(type=int)
	query = GObject.Property(type=str)

	def __init__(self, *args, **kwargs):
		super(Gtk.ListBoxRow, self).__init__(*args, **kwargs)

		self.set_can_focus(False)

		self.query = self.get_property('query')
		self.value = self.get_property('value')
		self.index = self.get_property('index')
		self.fuzzy = FuzzyMatch(text=self.value)

		self.label = Gtk.Label(margin=6, margin_left=10, margin_right=10)
		self.label.set_justify(Gtk.Justification.LEFT)
		self.label.set_halign(Gtk.Align.START)

		self.connect('notify::query', self.on_query_notify)

		self.add(self.label)
		self.set_label(self.value)

		self.show_all()

	def get_label(self):
		return self.label.get_label()

	def set_label(self, text):
		self.label.set_label(normalize_markup(text))

	def set_markup(self, markup):
		self.label.set_markup(normalize_markup(markup))

	def position(self):
		return self.fuzzy.score if bool(self.query) else -1

	def visibility(self):
		return self.fuzzy.score > -1 if bool(self.query) else True

	def highlight_match(self, match):
		return '<u><b>%s</b></u>' % match.group(0)

	def highlight_matches(self):
		words = self.query.replace(' ', '|')
		value = match_replace(words, self.highlight_match, self.value)

		self.set_markup(value)

	def do_label_markup(self):
		if bool(self.query):
			self.highlight_matches()

		elif '<u>' in self.get_label():
			self.set_label(self.value)

	def on_query_notify(self, *args):
		self.fuzzy.set_query(self.query)

		if self.visibility():
			GLib.idle_add(self.do_label_markup, priority=GLib.PRIORITY_HIGH_IDLE)


class CommandList(Gtk.ListBox):

	menu_actions = GObject.Property(type=object)
	window_actions = GObject.Property(type=object)

	def __init__(self, *args, **kwargs):
		super(Gtk.ListBox, self).__init__(*args, **kwargs)

		self.menu_actions = self.get_property('menu-actions')
		self.select_value = ''
		self.filter_value = ''
		self.visible_rows = []
		self.selected_row = 0
		self.selected_obj = None

		self.list_window_actions = False

		self.set_sort_func(self.sort_function)
		self.set_filter_func(self.filter_function)

		self.connect('row-selected', self.on_row_selected)
		self.connect('notify::menu-actions', self.on_menu_actions_notify)
		self.connect('notify::window-actions', self.on_menu_actions_notify)

	def set_filter_value(self, value=None):
		self.visible_rows = []
		self.filter_value = normalize_string(value)

		GLib.idle_add(self.invalidate_filter_value, priority=GLib.PRIORITY_LOW)

	def invalidate_filter_value(self):
		self.invalidate_filter()

		GLib.idle_add(self.invalidate_sort, priority=GLib.PRIORITY_HIGH)
		GLib.idle_add(self.invalidate_selection, priority=GLib.PRIORITY_LOW)

	def invalidate_selection(self):
		if bool(self.filter_value):
			self.visible_rows = []
			self.foreach(self.append_visible_row)
		else:
			self.visible_rows = self.get_children()

		self.select_row_by_index(0)

	def reset_selection_state(self, index):
		if index == 0:
			self.invalidate_selection()
			return True

	def append_visible_row(self, row):
		if row.visibility():
			self.visible_rows.append(row)
			return True

	def select_row_by_index(self, index):
		if index in range(0, len(self.visible_rows)):
			self.selected_row = index
			self.selected_obj = self.visible_rows[index]

			self.selected_obj.activate()

	def get_last_row_index(self):
		return len(self.visible_rows) - 1

	def select_prev_row(self):
		lastrow = self.get_last_row_index()
		prevrow = self.selected_row - 1
		prevrow = lastrow if prevrow < 0 else prevrow

		self.select_row_by_index(prevrow)

	def select_next_row(self):
		lastrow = self.get_last_row_index()
		nextrow = self.selected_row + 1
		nextrow = 0 if nextrow > lastrow else nextrow

		self.select_row_by_index(nextrow)

	def sort_function(self, row1, row2):
		score_diff = row1.position() - row2.position()
		index_diff = row1.index - row2.index

		return score_diff or index_diff

	def filter_function(self, item):
		item.set_property('query', self.filter_value)
		return item.visibility()

	def do_list_item(self, value, index):
		command = CommandListItem(value=value, index=index)

		self.append_visible_row(command)
		self.add(command)

	def do_list_items(self):
		if self.list_window_actions:
			for index, value in enumerate(self.window_actions):
				self.do_list_item(value, index)
				self.reset_selection_state(index)
				yield True

		offset = len(self.window_actions) if self.window_actions is not None else 0
		
		for index, value in enumerate(self.menu_actions):
			self.do_list_item(value, offset + index)
			self.reset_selection_state(offset + index)
			yield True

	def on_row_selected(self, listbox, item):
		self.select_value = item.value if item else ''

	# args=(<default.CommandList object (handlers+default+CommandList)>, <GParamBoxed 'menu-actions'>)
	def on_menu_actions_notify(self, *args):
		self.visible_rows = []
		self.foreach(lambda item: item.destroy())

		if args[1].name == 'window-actions':
			self.list_window_actions = True
			# run_generator(self.do_list_items)
		elif args[1].name == 'menu-actions':
			run_generator(self.do_list_items)


class CommandWindow(Gtk.ApplicationWindow):

	wayland = is_wayland()

	def __init__(self, *args, **kwargs):
		if not self.wayland:
			kwargs['type'] = Gtk.WindowType.POPUP
		super(Gtk.ApplicationWindow, self).__init__(*args, **kwargs)

		self.set_size_request(750, -1)
		self.set_keep_above(True)
		self.set_resizable(False)

		self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
		self.set_position(Gtk.WindowPosition.CENTER)
		self.set_custom_position()

		self.set_skip_pager_hint(True)
		self.set_skip_taskbar_hint(True)
		self.set_destroy_with_parent(True)

		self.empty_label = Gtk.Label(margin=12)
		self.empty_label.set_label('No menu actions available!')

		self.empty_box = Gtk.Box(sensitive=False)
		self.empty_box.set_size_request(750, -1)
		self.empty_box.add(self.empty_label)

		self.command_list = CommandList()
		self.command_list.invalidate_selection()

		self.search_entry = Gtk.SearchEntry(hexpand=True, margin=2)
		self.search_entry.connect('search-changed', self.on_search_entry_changed)
		self.search_entry.set_has_frame(False)

		self.scrolled_window = Gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
		self.scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
		self.scrolled_window.set_size_request(750, 210)
		self.scrolled_window.add(self.command_list)

		self.header_bar = Gtk.HeaderBar(spacing=0)
		self.header_bar.set_custom_title(self.search_entry)

		self.main_box = Gtk.Box()
		self.main_box.add(self.empty_box)
		self.main_box.add(self.scrolled_window)

		self.set_titlebar(self.header_bar)
		self.add(self.main_box)

		self.set_dark_variation()
		self.set_custom_styles()

		Gdk.event_handler_set(self.on_gdk_event)

		self.connect('show', self.on_window_show)
		self.connect('button-press-event', self.on_button_press_event)

	def set_menu_actions(self, actions):
		if actions:
			self.empty_box.hide()
			self.scrolled_window.show()

		self.command_list.set_property('menu-actions', actions)

	def set_window_actions(self, actions):
		self.empty_box.hide()
		self.scrolled_window.show()
		self.command_list.set_property('window-actions', actions)

	def set_custom_position(self):
		position = self.get_position()
		self.move(position.root_x, 32)

	def set_dark_variation(self, set_dark=True):
		settings = Gtk.Settings.get_default()
		settings.set_property('gtk-application-prefer-dark-theme', set_dark)

	def set_custom_styles(self):
		styles = """entry.search.flat { border: 0; outline: 0;
			border-image: none; box-shadow: none; }

			headerbar { box-shadow: none; background: @insensitive_bg_color;
				border-radius: 0; border-width: 0 0 1px 0; }

			scrolledwindow overshoot, scrolledwindow undershoot {
				background: none; box-shadow: none; }

			scrollbar { opacity: 0; }

			window decoration { box-shadow: none; border-color: @borders;
				border-style: solid; border-width: 1px; border-radius: 0; }
		"""

		inject_custom_style(self, styles)

	def grab_keyboard(self, window, status, tstamp):
		while Gdk.keyboard_grab(window, True, tstamp) != status:
			time.sleep(0.1)

	def grab_pointer(self, window, status, tstamp):
		mask = Gdk.EventMask.BUTTON_PRESS_MASK

		while Gdk.pointer_grab(window, True, mask, window, None, tstamp) != status:
			time.sleep(0.1)

	def emulate_focus_out_event(self):
		if not self.wayland:
			tstamp = Gdk.CURRENT_TIME
			Gdk.keyboard_ungrab(tstamp)
			Gdk.pointer_ungrab(tstamp)

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
		if not self.wayland:
			window = self.get_window()
			status = Gdk.GrabStatus.SUCCESS
			tstamp = Gdk.CURRENT_TIME

			self.grab_keyboard(window, status, tstamp)
			self.grab_pointer(window, status, tstamp)

		self.search_entry.grab_focus()

	def on_button_press_event(self, widget, event):
		win_type = event.get_window().get_window_type()
		tmp_type = Gdk.WindowType.TEMP

		if win_type == tmp_type and not self.clicked_inside(event):
			self.emulate_focus_out_event()
			return True

	def on_search_entry_changed(self, *args):
		search_value = self.search_entry.get_text()

		self.scrolled_window.unset_placement()
		self.command_list.set_filter_value(search_value)


class HudMenu(Gtk.Application):

	def __init__(self, dbus_menu, *args, **kwargs):
		kwargs['application_id'] = 'org.gonzaarcr.fildemapp'
		super(Gtk.Application, self).__init__(*args, **kwargs)

		self.dbus_menu = dbus_menu

		# self.set_accels_for_action('app.start', ['<Ctrl><Alt>space'])
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
		self.add_simple_action('start', self.on_show_window)
		self.add_simple_action('quit', self.on_hide_window)
		self.add_simple_action('prev', self.on_prev_command)
		self.add_simple_action('next', self.on_next_command)
		self.add_simple_action('execute', self.on_execute_command)

	def do_activate(self):
		self.window = CommandWindow(application=self, title='Gnome HUD')
		self.window.show_all()

		self.window_actions = WindowActions(self.on_window_actions_receive)
		self.window_actions.request_window_actions()

		self.window.set_menu_actions(self.dbus_menu.actions)
		self.window.connect('focus-out-event', self.on_hide_window)

		self.commands = self.window.command_list
		self.commands.connect_after('button-press-event', self.on_commands_click)

	def on_window_actions_receive(self, actions):
		self.window.set_window_actions(actions)

	def on_show_window(self, *args):
		self.window.show()

	def on_hide_window(self, *args):
		self.window.set_dark_variation(False)
		self.window.destroy()
		self.quit()

	def on_prev_command(self, *args):
		self.commands.select_prev_row()

	def on_next_command(self, *args):
		self.commands.select_next_row()

	def on_commands_click(self, widget, event):
		if event.type == Gdk.EventType._2BUTTON_PRESS:
			self.on_execute_command()

	def on_execute_command(self, *args):
		selected_value = self.commands.select_value
		if selected_value in self.window_actions.actions:
			self.window_actions.activate_action(selected_value)
		else:
			self.dbus_menu.activate(selected_value)
		self.on_hide_window()
