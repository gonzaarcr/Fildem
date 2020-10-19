#! /usr/bin/python3

import os
import subprocess
import gi

from gi.repository import GLib


gl_panel_bg_colour = None

def _get_panel_background_colour():
	home = os.path.expanduser('~')
	bashCommand = "gsettings " \
		"--schemadir "+ home + "/.local/share/gnome-shell/extensions/user-theme@gnome-shell-extensions.gcampax.github.com/schemas/ " \
		"get org.gnome.shell.extensions.user-theme name"

	process = subprocess.run(bashCommand.split(), capture_output=True, text=True)
	output = process.stdout
	theme_name = output.rstrip('\n').strip("'")

	if not theme_name:
		return

	stylesheetPaths = [
		[GLib.get_home_dir(), '.themes'],
		[GLib.get_user_data_dir(), 'themes'],
		*map(lambda dir: [dir, 'themes'], GLib.get_system_data_dirs())
	]
	stylesheetPaths = map(lambda themeDir: GLib.build_filenamev([
		*themeDir, theme_name, 'gnome-shell', 'gnome-shell.css',
	]), stylesheetPaths);
	stylesheetFile = list(filter(os.path.isfile, stylesheetPaths))
	if len(stylesheetFile) == 0:
		return

	stylesheetFile = stylesheetFile[0]
	with open(stylesheetFile) as f:
		line = f.readline()
		while line.find('#panel') == -1:
			line = f.readline()

		while line.find('background-color') == -1:
			line = f.readline()

		idx = line.find('background-color') + len('background-color')

		while idx < len(line):
			if line[idx] == '#':
				colour_hex = line[idx+1:idx+7]
				break
			idx += 1

	if not colour_hex[3].isalpha():
		colour_hex = colour_hex[:3]

	return colour_hex

def get_panel_background_colour():
	global gl_panel_bg_colour

	if gl_panel_bg_colour is not None:
		return gl_panel_bg_colour

	try:
		gl_panel_bg_colour = _get_panel_background_colour()
	except Exception:
		gl_panel_bg_colour = None

	return gl_panel_bg_colour
