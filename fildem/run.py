#!/usr/bin/python3

import os
import sys

from fildem.command import main as command_main

def main():
	if sys.path[0] != '':
		os.chdir(sys.path[0])

	if os.environ['XDG_SESSION_TYPE'] != 'x11':
		os.environ['GDK_BACKEND'] = 'x11'

	os.environ['UBUNTU_MENUPROXY'] = '0'
	command_main()
	
if __name__ == '__main__':
	main()
