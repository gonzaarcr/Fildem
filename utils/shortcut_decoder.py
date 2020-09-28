import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk


def parse_accel(accel: str):
	"""
		GTk accels are the form <Primary><Shift>t <Primary><Shift>bracketright
		Qt accels are the form <Control><Shift>O
	"""
	if accel == '':
		return None

	if accel.lower() == 'del':
		# So hardcoded that it hurts (blame qbittorrent)
		return 65535, Gdk.ModifierType(0)
	else:
		return Gtk.accelerator_parse(accel)
