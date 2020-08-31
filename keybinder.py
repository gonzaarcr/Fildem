#! /usr/bin/python3

import gi

gi.require_version('Keybinder', '3.0')

from gi.repository import Keybinder, GLib

from gnomehud.command import default_hud_menu
from gnomehud.command import rofi_hud_menu


def run_keybinder(callback):
  Keybinder.init()
  Keybinder.bind('<Ctrl><Alt>space', callback)

  try:
    GLib.MainLoop().run()
  except KeyboardInterrupt:
    GLib.MainLoop().quit()


def main():
  run_keybinder(default_hud_menu)


def rofi():
  run_keybinder(rofi_hud_menu)


if __name__ == "__main__":
  main()
