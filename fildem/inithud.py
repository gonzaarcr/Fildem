#!/usr/bin/python3

import dbus

def main():
	session = dbus.SessionBus()
	proxy = session.get_object('com.gonzaarcr.appmenu', '/com/gonzaarcr/appmenu')
	proxy.EmitHudActivated()

if __name__ == "__main__":
	main()
