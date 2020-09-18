#! /usr/bin/python3

import os
import sys
import threading

from handlers.default import HudMenu
from handlers.global_menu import GlobalMenu
from handlers.rofi import RofiMenu


def run_command(module, function):
  PATH = '~/wip/gnomehud'
  args = 'cd '+ PATH + '; ' + 'python3 -c "from %s import %s as run; run()"'
  args = args % (module, function)

  proc = threading.Thread(target=os.system, args=[args])
  proc.start()


def run_hud_menu(menu):
  run_command('appmenu', 'main')
  run_command('keybinder', menu)


def default_hud_menu(*args):
  menu = GlobalMenu()
  menu.run()


def rofi_hud_menu(*args):
  menu = RofiMenu()
  menu.run()
  # menu.start()
  # start


def main():
  if True and sys.stdin.isatty():
    run_hud_menu('main')
  else:
    default_hud_menu()


def rofi():
  if sys.stdin.isatty():
    run_hud_menu('rofi')
  else:
    rofi_hud_menu()


if __name__ == "__main__":
  main()
