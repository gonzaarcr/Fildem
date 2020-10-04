#! /usr/bin/python3

import os
import sys
import threading

from handlers.default import HudMenu
from handlers.global_menu import GlobalMenu
from handlers.rofi import RofiMenu
from utils.appindicator import MainApp


def run_command(module, function):
	args = 'python3 -c "from %s import %s as run; run()"'
	args = args % (module, function)

	proc = threading.Thread(target=os.system, args=[args])
	proc.start()


def run_hud_menu(menu):
	run_command('appmenu', 'main')
	run_command('keybinder', menu)


def global_hud_menu(accel, dbus_menu):
	menu = GlobalMenu(dbus_menu)
	menu.run()


def default_hud_menu(accel, dbus_menu):
	menu = HudMenu(dbus_menu)
	menu.run()


def appindicator_menu(accel, dbus_menu):
	MainApp(dbus_menu)

def rofi_hud_menu(*args):
	menu = RofiMenu()
	menu.run()


def main():
	if sys.stdin.isatty():
		run_hud_menu('main')
	else:
		default_hud_menu()


def global_menu():
	if sys.stdin.isatty():
		run_hud_menu('global_menu')
	else:
		global_hud_menu()


def appind_menu():
	if sys.stdin.isatty():
		run_hud_menu('appindicator')
	else:
		appindicator_menu()


def rofi():
	if sys.stdin.isatty():
		run_hud_menu('rofi')
	else:
		rofi_hud_menu()


if __name__ == "__main__":
	main()
	# global_menu()
	# appind_menu()
