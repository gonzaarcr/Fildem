#! /usr/bin/python3

import gi

gi.require_version('Keybinder', '3.0')

from gi.repository import Keybinder, GLib

from dbus.mainloop.glib import DBusGMainLoop

from fildem.command import default_hud_menu, rofi_hud_menu, global_hud_menu
from fildem.utils.menu import DbusMenu
from fildem.utils.wayland import is_wayland


def run_keybinder(callback):
	# for wayland
	DBusGMainLoop(set_as_default=True)
	dbus_menu = DbusMenu()

	if not is_wayland():
		Keybinder.bind('<Alt>space', callback, dbus_menu)
	# GLib.timeout_add_seconds(1, callback)
	try:
		GLib.MainLoop().run()
	except KeyboardInterrupt:
		GLib.MainLoop().quit()

def main():
	run_keybinder(default_hud_menu)


def rofi():
	run_keybinder(rofi_hud_menu)


def global_menu():
	run_keybinder(global_hud_menu)


if __name__ == "__main__":
	main()
