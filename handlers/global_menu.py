import gi
import time

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject

from utils.menu import DbusMenu
from utils.fuzzy import FuzzyMatch
from utils.fuzzy import normalize_string
from utils.fuzzy import match_replace

def get_separator():
  return u'\u0020\u0020\u00BB\u0020\u0020'


def normalize_markup(text):
  return text.replace('&', '&amp;')


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

  def __init__(self, depth, *args, **kwargs):
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
    label = self.value.split(get_separator())[depth]
    self.set_label(label)

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


class Menu(Gtk.Menu):

  def __init__(self, menus, depth, accel_group, *args, **kwargs):
    super(Gtk.Menu, self).__init__(*args, **kwargs)
    self.accel_group = accel_group
    self.depth = depth
    self.add_items(menus)
    self.show_all()

  def add_items(self, menus):
    i = 0
    while i < len(menus):
      item = menus[i]
      if len(item.path) == self.depth:
        #item
        menu_item = Gtk.MenuItem()
        menu_item.set_accel_path('<MyApp>/Options')
        menu_item.set_property('action_name', 'app.' + str(item.action))
        label = item.label

        if item.accel != '':
          pass
          # menu_item.add_accelerator('activate', self.accel_group, Gdk.KEY_Q, Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
      else:
        # sub_menu
        current_prefix = item.path[self.depth]
        current_menu = []
        while i < len(menus) and len(menus[i].path) > self.depth and menus[i].path[self.depth] == current_prefix:
          current_menu.append(menus[i])
          i += 1

        menu_item = self.create_sub_menu(current_menu)
        label = item.path[self.depth]

      menu_item.set_use_underline(True)
      menu_item.set_label(label)
      self.append(menu_item)
      i += 1

  def create_sub_menu(self, menu):
    menu = Menu(menu, self.depth + 1, self.accel_group)
    menu_item = Gtk.MenuItem()
    menu_item.set_submenu(menu)
    return menu_item

class CommandList(Gtk.ListBox):

  menu_actions = GObject.Property(type=object)

  def __init__(self, depth=0, *args, **kwargs):
    super(Gtk.ListBox, self).__init__(*args, **kwargs)

    self.menu_actions = self.get_property('menu-actions')
    self.select_value = ''
    self.filter_value = ''
    self.visible_rows = []
    self.selected_row = 0
    self.selected_obj = None
    self.depth = depth

    self.set_sort_func(self.sort_function)
    self.set_filter_func(self.filter_function)

    self.connect('row-selected', self.on_row_selected)
    self.connect('notify::menu-actions', self.on_menu_actions_notify)

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
    command = CommandListItem(value=value, index=index, depth=self.depth)

    self.append_visible_row(command)
    self.add(command)

  def do_list_items(self):
    for index, value in enumerate(self.menu_actions):
      self.do_list_item(value, index)
      self.reset_selection_state(index)
      yield True

  def on_row_selected(self, listbox, item):
    self.select_value = item.value if item else ''

  def on_menu_actions_notify(self, *args):
    self.visible_rows = []
    self.foreach(lambda item: item.destroy())

    run_generator(self.do_list_items)


class CommandWindow(Gtk.ApplicationWindow):

  def __init__(self, *args, **kwargs):
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

    self.search_entry = Gtk.SearchEntry(hexpand=True, margin=2)
    self.search_entry.connect('search-changed', self.on_search_entry_changed)
    self.search_entry.connect('populate-popup', self.on_populate_popup)
    self.search_entry.set_has_frame(False)

    self.header_bar = Gtk.HeaderBar(spacing=0)
    self.header_bar.set_custom_title(self.search_entry)

    self.menus = {}
    self.my_menu_bar = Gtk.MenuBar()
    self.item = Gtk.MenuItem()
    self.item.set_label('Options')
    self.item.set_accel_path('<MyApp>/Options')
    self.accel_group = Gtk.AccelGroup()
    self.add_accel_group(self.accel_group)
    # self.item.set_property('action_name', 'app.quit')
    self.item2 = Gtk.MenuItem()
    self.item2.set_label('Kida long item _Next')
    self.item2.set_property('action_name', 'app.next')
    self.item3 = Gtk.MenuItem()
    self.item3.set_use_underline(True)
    self.item3.set_label('_Salir')
    self.item3.add_accelerator('activate', self.accel_group, Gdk.KEY_Q, Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
    self.item3.set_accel_path('<MyApp>/Options/Salir')
    self.item3.set_property('action_name', 'app.quit')
    self.sub_menu = Gtk.Menu()
    self.sub_menu.append(self.item2)
    self.sub_menu.append(self.item3)
    self.item.set_submenu(self.sub_menu)

    self.my_menu_bar.append(self.item)
    # self.my_menu_bar.append(self.item2)
    # self.my_menu_bar.append('Salir', 'app.quit')
    # self.my_menu_bar.append('Arriba', 'app.prev')
    self.my_menu_bar.show_all()

    # self.button = Gtk.MenuButton()
    # self.button.set_popup(self.my_menu_bar)
    # self.button.set_menu_model(self.menu_model)
    
    self.h_box = Gtk.Box()
    # self.main_box = Gtk.Box()
    # self.my_menu_bar.unparent()
    # self.main_box.add(self.my_menu_bar)

    self.set_titlebar(self.header_bar)

    # self.menu_bar = Gtk.MenuBar()
    self.h_box.add(self.my_menu_bar)

    self.add(self.h_box)
    # self.add(self.main_box)
    self.show_all()
    self.set_dark_variation()
    self.set_custom_styles()

    Gdk.event_handler_set(self.on_gdk_event)

    self.connect('show', self.on_window_show)
    self.connect('button-press-event', self.on_button_press_event)

  def set_menu(self, menus):
    # self.destroy_menus()
    current_prefix = menus[0].path[0]
    current_menu = []
    for item in menus:
      if item.path[0] == current_prefix:
        current_menu.append(item)
      else:
        self.create_menu(current_prefix, current_menu)
        current_menu = [ item ]
        current_prefix = item.path[0]
    else:
      self.create_menu(current_prefix, current_menu)

  def create_menu(self, name, current_menu):
    if len(current_menu) == 0:
      return
    menu = Menu(current_menu, 1, self.accel_group)
    menu.show_all()
    button = Gtk.MenuItem() # Menu()
    button.set_label(name) # set_label(name)
    button.set_submenu(menu) # set_popup(menu)
    button.show_all()
    self.my_menu_bar.append(button)
    # self.h_box.add(button)
    # self.h_box.show_all()


  def set_custom_position(self):
    position = self.get_position()
    self.move(position.root_x, 32)

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
    if event.type is Gdk.EventType.FOCUS_CHANGE:
      return

    Gtk.main_do_event(event)

  def on_window_show(self, window):
    window = self.get_window()
    status = Gdk.GrabStatus.SUCCESS
    tstamp = Gdk.CURRENT_TIME
    self.set_show_menubar(True)

    # self.grab_keyboard(window, status, tstamp)
    # self.grab_pointer(window, status, tstamp)

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

  def on_populate_popup(self, entry, widget):
    # contextual_menu = Gtk.Menu()
    self.sub_item = Gtk.MenuItem(u'Item')
    self.sub_item.set_label("Sub Menu")
    # item = Gtk.MenuItem.submenu("Submenu", sub_item)
    widget.append(self.sub_item)
    # widget.get_children()[2].set_submenu(Gtk.Menu().append(self.sub_item))
    widget.show_all()
    widget.show()
    # widget.prepend(Gtk.SeparatorMenuItem())

    # self.search_entry.do_populate_popup(self.contextual_menu)

class GlobalMenu(Gtk.Application):

  def __init__(self, *args, **kwargs):
    kwargs['application_id'] = 'org.ddog.gnomeAppMenu'
    super(Gtk.Application, self).__init__(*args, **kwargs)

    self.dbus_menu = DbusMenu()
    self.navigation = []
    self.navigation_windows = []
    self.actions = []

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
    ac = self.dbus_menu.actions
    for item in self.dbus_menu.items:
      self.add_menu_action(item.action, item.path, item.label)
    self.window.set_menu(self.dbus_menu.items)
    self.window.connect('focus-out-event', self.on_hide_window)

    # self.commands = self.window.command_list
    # self.commands.connect_after('button-press-event', self.on_commands_click)

  def add_menu_action(self, name, path, label):
    '''
      Adds an action of the foreign app. Do not add actions
      of the app here
    '''
    name = str(name)
    self.actions.append(name)
    action = Gio.SimpleAction.new(name, None)
    path = id = get_separator().join(path) + get_separator() + label
    callback = lambda a, b: self.dbus_menu.activate(path)
    action.connect('activate', callback)
    self.add_action(action)

  def remove_all_actions(self):
    for name in self.actions:
      self.remove_action(name)
    self.actions = []

  def on_show_window(self, *args):
    self.window.show()

  def on_hide_window(self, *args):
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
    self.dbus_menu.activate(self.commands.select_value)
    self.on_hide_window()
