#! /usr/bin/python3

import dbus

from gi.repository import GLib
from dbus.mainloop.glib import DBusGMainLoop

from gnomehud.utils.service import BUS_NAME
from gnomehud.utils.service import AppMenuService


def run_service():
  AppMenuService()

  try:
    GLib.MainLoop().run()
  except KeyboardInterrupt:
    GLib.MainLoop().quit()


def main():
  DBusGMainLoop(set_as_default=True)
  session_bus = dbus.SessionBus()

  if not session_bus.name_has_owner(BUS_NAME):
    run_service()


if __name__ == "__main__":
  main()
