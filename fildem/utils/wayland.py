import os


def is_wayland():
	disp = os.environ.get('WAYLAND_DISPLAY')
	type = os.environ.get('XDG_SESSION_TYPE')

	return 'wayland' in (disp or type)
