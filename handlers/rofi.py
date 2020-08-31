import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

from subprocess import Popen
from subprocess import PIPE

from gnomehud.utils.menu import DbusMenu


def rgba_to_hex(color):
  red   = int(color.red * 255)
  green = int(color.green * 255)
  blue  = int(color.blue * 255)

  return "#{0:02x}{1:02x}{2:02x}".format(red, green, blue)


class RofiMenu:

  def __init__(self):
    self.settings  = Gtk.Settings.get_default()
    self.context   = Gtk.StyleContext()
    self.dbus_menu = DbusMenu()

    self.settings.set_property('gtk-application-prefer-dark-theme', True)

  @property

  def selection(self):
    selection = self.menu_proc.communicate()[0].decode('utf8').rstrip()
    self.menu_proc.stdin.close()

    return selection

  @property

  def items(self):
    items = self.dbus_menu.actions
    return '\n'.join(items).encode('utf-8')

  @property

  def font_name(self):
    return self.settings.get_property('gtk-font-name')

  @property

  def gtk_theme_colors(self):
    colors = {
      'header':      self.lookup_color('insensitive_bg_color'),
      'base':        self.lookup_color('theme_base_color'),
      'text':        self.lookup_color('theme_text_color'),
      'bg':          self.lookup_color('theme_bg_color'),
      'borders':     self.lookup_color('borders'),
      'disabled':    self.lookup_color('insensitive_fg_color'),
      'selected_bg': self.lookup_color('theme_selected_bg_color'),
      'selected_fg': self.lookup_color('theme_selected_fg_color'),
      'error_bg':    self.lookup_color('error_bg_color'),
      'error_fg':    self.lookup_color('error_fg_color')
    }

    for name, color in colors.items():
      colors[name] = rgba_to_hex(color)

    return colors

  @property

  def theme_colors(self):
    colors = {
      'window': [
        self.gtk_theme_colors['header'],
        self.gtk_theme_colors['borders'],
        self.gtk_theme_colors['borders']
      ],
      'normal': [
        self.gtk_theme_colors['base'],
        self.gtk_theme_colors['text'],
        self.gtk_theme_colors['base'],
        self.gtk_theme_colors['selected_bg'],
        self.gtk_theme_colors['selected_fg']
      ],
      'urgent': [
        self.gtk_theme_colors['base'],
        self.gtk_theme_colors['text'],
        self.gtk_theme_colors['base'],
        self.gtk_theme_colors['error_bg'],
        self.gtk_theme_colors['error_fg']
      ]
    }

    for name, color in colors.items():
      colors[name] = ', '.join(color)

    return colors

  @property

  def theme_string(self):
    style = """
      #window { location: north; anchor: north; border: 1px;
        width: 750px; padding: 0; margin: 32px 0 0; }

      #mainbox { spacing: 0; children: [inputbar, %s]; }

      #message { border: 1px 0 0; spacing: 0; padding: 12px;
        background-color: %s; }

      #listview { border: 1px 0 0; spacing: 0; scrollbar: false;
        padding: 0; lines: 6; background-color: @normal-background; }

      #textbox { text-color: %s; }
      #textbox { text-color: %s; }
      #inputbar { padding: 14px 12px; }
      #element { border: 0; padding: 8px 12px; }
      #textbox-prompt-colon { str: ""; }
    """

    layout = 'listview'  if self.dbus_menu.actions else 'message'
    bcolor = self.gtk_theme_colors['bg']
    tcolor = self.gtk_theme_colors['disabled']

    return style % (layout, bcolor, tcolor, tcolor)

  def lookup_color(self, key):
    return self.context.lookup_color(key)[1]

  def open_menu(self):
    options = [
      'rofi',
      '-i',
      '-dmenu',
      '-theme-str', self.theme_string,
      '-p', '⚙',
      '-mesg', 'No menu actions available!',
      '-font', self.font_name,
      '-color-window', self.theme_colors['window'],
      '-color-normal', self.theme_colors['normal'],
      '-color-urgent', self.theme_colors['urgent']
    ]

    self.menu_proc = Popen(options, stdout=PIPE, stdin=PIPE)
    self.menu_proc.stdin.write(self.items)

  def run(self):
    self.open_menu()
    self.dbus_menu.activate(self.selection)
