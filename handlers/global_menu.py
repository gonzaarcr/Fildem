import gi
import dbus
import time

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Keybinder', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Keybinder

from utils.menu import DbusMenu
from utils.service import BUS_NAME, BUS_PATH
from utils.fuzzy import FuzzyMatch
from utils.fuzzy import normalize_string
from utils.fuzzy import match_replace
from utils.shortcut_decoder import parse_accel

def get_separator():
  return u'\u0020\u0020\u00BB\u0020\u0020'


def normalize_markup(text):
  return text.replace('&', '&amp;')


def inject_custom_style(widget, style_string):
  provider = Gtk.CssProvider()
  provider.load_from_data(style_string.encode())

  screen   = Gdk.Screen.get_default()
  priority = Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
  Gtk.StyleContext.add_provider_for_screen(screen, provider, priority)


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

        shortcut = parse_accel(item.accel)
        if shortcut != None:
          menu_item.add_accelerator('activate', self.accel_group, shortcut[1], shortcut[0], Gtk.AccelFlags.VISIBLE)
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


class CommandWindow(Gtk.ApplicationWindow):

  def __init__(self, *args, **kwargs):
    kwargs['type'] = Gtk.WindowType.POPUP
    super(Gtk.ApplicationWindow, self).__init__(*args, **kwargs)
    self.seat = Gdk.Display.get_default().get_default_seat()

    self.keybinding_strings = []

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
    self.search_entry.set_has_frame(False)

    self.header_bar = Gtk.HeaderBar(spacing=0)
    self.header_bar.set_custom_title(self.search_entry)

    self.my_menu_bar = Gtk.MenuBar()
    self.item = Gtk.MenuItem()
    self.item.set_label('Options')
    self.item.set_accel_path('<MyApp>/Options')
    self.accel_group = Gtk.AccelGroup()
    #self.add_accel_group(self.accel_group)
    # self.item.set_property('action_name', 'app.quit')
    self.item2 = Gtk.MenuItem()
    self.item2.set_label('Kida long item _Next')
    self.item3 = Gtk.MenuItem()
    self.item3.set_use_underline(True)
    self.item3.set_label('_Salir')
    # self.item3.add_accelerator('activate', self.accel_group, Gdk.KEY_Q, Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
    #self.item3.set_accel_path('<MyApp>/Options/Salir')
    self.item3.set_property('action_name', 'app.quit')
    self.sub_menu = Gtk.Menu()
    self.sub_menu.append(self.item2)
    self.sub_menu.append(self.item3)
    self.item.set_submenu(self.sub_menu)

    self.my_menu_bar.append(self.item)
    # self.my_menu_bar.append(self.item2)
    # self.my_menu_bar.append('Salir', 'app.quit')

    # self.set_titlebar(self.header_bar)

    self.main_box = Gtk.VBox()
    self.main_box.add(self.my_menu_bar)

    self.add(self.main_box)
    # self.set_dark_variation()
    self.set_custom_styles()

    Gdk.event_handler_set(self.on_gdk_event)
    self.menu_test = None

    self.connect('show', self.on_window_show)
    self.connect('button-press-event', self.on_button_press_event)
    self.connect('enter_notify_event', self.on_enter_event)
    self.connect('leave_notify_event', self.on_leave_event)

  def remove_all_keybindings(self):
    for k in self.keybinding_strings:
      Keybinder.unbind_all(k)
    self.keybinding_strings = []

  def add_keybinding(self, menu):
    label = menu.get_label()
    i = label.find('_')
    if i != -1:
      acc = '<Alt>' + label[i + 1]
      Keybinder.bind(acc, lambda accelerator: self.open_menu_shortcut(menu))

  def open_menu_shortcut(self, menu):
    self.make_opaque()
    self.grab_keyboard(self.get_window())
    self.my_menu_bar.select_item(menu) # activate_item(menu)

  def set_menu(self, menus):
    self.destroy_menus()
    self.remove_all_keybindings()
    if len(menus) == 0:
      return
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
    if self.menu_test == None:
      self.menu_test = menu
    button = Gtk.MenuItem()
    button.set_label(name)
    self.add_keybinding(button)
    button.set_use_underline(True)
    button.set_submenu(menu) # set_popup(menu)
    button.show_all()
    button.set_can_focus(True)
    self.my_menu_bar.append(button)

  def destroy_menus(self):
    self.main_box.remove(self.my_menu_bar)
    self.my_menu_bar = Gtk.MenuBar()
    self.main_box.add(self.my_menu_bar)

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

  def grab_keyboard(self, window, status=Gdk.GrabStatus.SUCCESS):
    while self.seat.grab(window, Gdk.SeatCapabilities.KEYBOARD, False, None, None, None) != status:
      time.sleep(0.1)

  def ungrab_keyboard(self):
    self.seat.ungrab()

  def grab_pointer(self, window, status=Gdk.GrabStatus.SUCCESS, tstamp=-1):
    return
    mask = Gdk.EventMask.BUTTON_PRESS_MASK

    while Gdk.pointer_grab(window, True, mask, window, None, tstamp) != status:
      time.sleep(0.1)

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
    # self.grab_pointer(window, status, tstamp)

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

  def on_enter_event(self, widget, event):
    pass
    #self.make_opaque()

  def on_leave_event(self, widget, event):
    pass
    #self.make_transparent()

class GlobalMenu(Gtk.Application):

  def __init__(self, *args, **kwargs):
    kwargs['application_id'] = 'org.gonzaarcr.fildemapp'
    super(Gtk.Application, self).__init__(*args, **kwargs)

    self.dbus_menu = DbusMenu()
    self.dbus_menu.add_window_switch_listener(self.on_window_switched)
    self.actions = []
    Keybinder.init()

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
    ac = self.dbus_menu.actions
    for item in self.dbus_menu.items:
      self.add_menu_action(item.action, item.path, item.label)
    self.window.set_menu(self.dbus_menu.items)
    self.window.show_all()
    # self.window.connect('focus-out-event', self.on_hide_window)

  def add_menu_action(self, name, path, label):
    '''
      Adds an action of the foreign app. Do not add actions
      of the app here
    '''
    name = str(name)
    self.actions.append(name)
    action = Gio.SimpleAction.new(name, None)
    path = get_separator().join(path) + get_separator() + label
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

  def on_window_switched(self):
    print("switched")
    self.window.remove_all_keybindings()
    self.do_activate()

  def menu_activated(self, menu):
    print("menu activated: ", menu)
