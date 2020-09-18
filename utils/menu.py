import gi
import dbus

gi.require_version('Bamf', '3')

from gi.repository import Gio
from gi.repository import Bamf

from utils.fuzzy import match_replace


def format_label(parts):
  separator = u'\u0020\u0020\u00BB\u0020\u0020'
  return separator.join(parts)


class DbusGtkMenuItem(object):

  def __init__(self, item, path=[]):
    self.path   = path
    self.action = str(item.get('action', ''))
    self.accel  = str(item.get('accel', '')) # <Primary><Shift><Alt>p
    self.shortcut = str(item.get('shortcut', ''))
    self.label  = item.get('label', '')
    self.text   = format_label(self.path + [self.label])


class DbusGtkMenu(object):

  def __init__(self, session, window):
    self.results      = {}
    self.actions      = {}
    self.accels       = {}
    self.items        = []
    self.session      = session
    self.bus_name     = window.get_utf8_prop('_GTK_UNIQUE_BUS_NAME')
    self.app_path     = window.get_utf8_prop('_GTK_APPLICATION_OBJECT_PATH')
    self.win_path     = window.get_utf8_prop('_GTK_WINDOW_OBJECT_PATH')
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
      results   = interface.Start([x for x in range(1024)])

      for menu in results:
        self.results[(menu[0], menu[1])] = menu[2]

    self.collect_entries([0, 0])

  def collect_entries(self, menu, labels=[]):
    for menu in self.results.get((menu[0], menu[1]), []):
      if 'label' in menu:
        menu_item = DbusGtkMenuItem(menu, labels)

        menu_path = labels + [menu_item.label]

        if ':submenu' in menu:
          self.collect_entries(menu[':submenu'], menu_path)
        elif 'action' in menu:
          self.actions[menu_item.text] = menu_item.action
          self.items.append(menu_item)

      elif ':section' in menu:
        self.collect_entries(menu[':section'], labels)


class DbusAppMenuItem(object):

  def __init__(self, item, path=[]):
    self.path   = path
    self.action = int(item[0])
    self.accel  = self.get_shorcut(item[1])
    self.label  = item[1].get('label', '')
    self.text   = format_label(self.path + [self.label])
    self.enabled = item[1].get('enabled', True)
    self.visible = item[1].get('visible', True)
    self.icon_data = item[1].get('icon_data', bytearray())

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
    except dbus.exceptions.DBusException as e:
      # print(e)
      return None

  def get_results(self):
    if self.interface:
      results = self.interface.GetLayout(0, -1, ['label'])
      self.collect_entries(results[1], [])

  def collect_entries(self, item=None, labels=[]):
    menu_item = DbusAppMenuItem(item, labels)
    menu_path = labels

    if bool(menu_item.label) and menu_item.label != 'Root':
      menu_path = labels + [menu_item.label]

    if len(item[2]):
      for child in item[2]:
        self.collect_entries(child, menu_path)

    elif bool(menu_item.label):
      self.actions[menu_item.text] = menu_item.action
      self.items.append(menu_item)

class DummyWindow(object):
  def __init__(self):
    super(DummyWindow, self).__init__()
    self.xid = 0
    self.props = {}

  def get_xid(self):
    return self.xid

  def set_xid(self, xid):
    self.xid = xid

  def get_utf8_prop(self, id):
    return self.props[id] if id in self.props else None
  
  def set_utf8_prop(self, key, value):
    self.props[key] = value

class DbusMenu:

  def __init__(self):
    self.session = dbus.SessionBus()
    self.window = DummyWindow()
    self._init_window()
    self.listen_chwindow_signal()
    self._win_switch_listeners = []

  def _init_window(self):
    self.matcher = Bamf.Matcher.get_default()
    self.window  = self.matcher.get_active_window()
    self.appmenu = DbusAppMenu(self.session, self.window)
    self.gtkmenu = DbusGtkMenu(self.session, self.window)

  def listen_chwindow_signal(self):
    name = 'com.gonzaarcr.appmenu'
    path = '/com/gonzaarcr/appmenu'
    proxy  = self.session.get_object(name, path)
    signal = proxy.connect_to_signal("WindowSwitchedSignal", self.window_switched)
    #self.matcher.connect('active-window-changed', self.window_switched_bamf)

  def window_switched(self, window_data):
    '''
    Listener on dbus WindowSwitched
    '''
    xid = window_data['xid'] if window_data['xid'] != '' else 0
    self.window.set_xid(int(xid))
    for p in window_data:
      if p == 'xid':
        continue
      self.window.set_utf8_prop('_' + p.upper(), window_data[p])
    self._init_window()
    for cb in self._win_switch_listeners:
      cb()

  def window_switched_bamf(self, matcher, object, p0):
    win = object if object != None else p0
    '''
    self._init_window()
    for cb in self._win_switch_listeners:
      cb()
    '''

  def add_window_switch_listener(self, callback):
    self._win_switch_listeners.append(callback)

  @property
  def prompt(self):
    return ''
    app  = self.matcher.get_active_application()
    file = app.get_desktop_file()
    info = Gio.DesktopAppInfo.new_from_filename(file)

    return info.get_string('Name')

  @property
  def actions(self):
    self.appmenu.get_results()
    self.gtkmenu.get_results()

    actions = { **self.gtkmenu.actions, **self.appmenu.actions }
    self.handle_empty(actions)

    return actions.keys()

  def accel(self):
    accel = { **self.gtkmenu.accels, **self.appmenu.accels }
    return accel

  @property
  def items(self):
    items = self.gtkmenu.items + self.appmenu.items
    return items

  def activate(self, selection):
    if selection in self.gtkmenu.actions:
      self.gtkmenu.activate(selection)

    elif selection in self.appmenu.actions:
      self.appmenu.activate(selection)

  def handle_empty(self, actions):
    if not len(actions):
      alert = 'No menu items available!'
      print('Gnome HUD: WARNING: (%s) %s' % (self.prompt, alert))
