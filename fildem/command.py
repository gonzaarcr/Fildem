#! /usr/bin/python3

import os
import threading

from fildem.handlers.default import HudMenu
from fildem.handlers.global_menu import GlobalMenu
from fildem.handlers.rofi import RofiMenu

def run_command(module, function):
	args = 'python3 -c "from fildem.%s import %s as run; run()"'
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

def rofi_hud_menu(*args):
	menu = RofiMenu()
	menu.run()

def main():
	run_hud_menu('main')

def global_menu():
	run_hud_menu('global_menu')

def rofi():
	run_hud_menu('rofi')


if __name__ == "__main__":
	main()
