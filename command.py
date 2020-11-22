#! /usr/bin/python3

import os
import threading


def run_command(module, function):
	args = 'python3 -c "from %s import %s as run; run()"'
	args = args % (module, function)

	proc = threading.Thread(target=os.system, args=[args])
	proc.start()

def run_hud_menu(menu):
	run_command('appmenu', 'main')
	run_command('keybinder', menu)

def main():
	run_hud_menu('main')

def global_menu():
	run_hud_menu('global_menu')

def rofi():
	run_hud_menu('rofi')


if __name__ == "__main__":
	main()
