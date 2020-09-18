import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject

import re
import sys

GDK_KEYS = { x.upper(): x for x in dir(Gdk) if x.startswith('KEY_') }

MODIFIERS_SWITCH = {
	'Primary': Gdk.ModifierType.CONTROL_MASK,
	'Control': Gdk.ModifierType.CONTROL_MASK,
	'Shift': Gdk.ModifierType.SHIFT_MASK,
	'Super': Gdk.ModifierType.SUPER_MASK,
	'Alt': Gdk.ModifierType.MOD1_MASK
}

# https://valadoc.org/gtk+-3.0/Gtk.accelerator_parse.html#!
# Gtk.accelerator_parse()
def parse_accel(accel):
	'''
		GTk accels are the form <Primary><Shift>t <Primary><Shift>bracketright
		Qt accels are the form <Control><Shift>O
	'''
	if accel == '':
		return None

	if accel.lower() == 'del':
		# So hardcoded that it hurts (blame qbittorrent)
		return (Gdk.ModifierType(0), 65535)

	flags = Gdk.ModifierType(0)
	idx = 0
	while accel[idx] == '<':
		idx += 1
		idx_end = accel.find('>', idx)
		mod = accel[idx:idx_end]
		flags |= MODIFIERS_SWITCH[mod]
		idx = idx_end + 1

	closing = accel.rfind('>')
	key = accel if closing == -1 else accel[closing+1:]
	key = GDK_KEYS['KEY_' + key.upper()]
	code = Gdk.__getattr__(key)

	if code == None:
		print(f'Key not found: {key=}', file=sys.stderr)
		return None

	return (flags, code)
