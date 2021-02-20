#!/usr/bin/python3

import dbus


def format_label(parts):
	separator = u'\u0020\u0020\u00BB\u0020\u0020'
	return separator.join(parts)


class DbusGtkMenuItem(object):

	def __init__(self, item, path=[], enabled=True):
		self.path   = path
		self.separator = False
		self.action = str(item.get('action', ''))
		self.accel  = str(item.get('accel', '')) # <Primary><Shift><Alt>p
		self.shortcut = str(item.get('shortcut', ''))
		self.label  = item.get('label', '')
		self.text   = format_label(self.path + [self.label])
		self.enabled = enabled
		self.toggle_type = ''
		self.toggle_state = False
		# :submenu
		# two index that indicate the group
		# dbus.String(':submenu'): dbus.Struct((dbus.UInt32(11), dbus.UInt32(0))
		# used for separators and radio button groups
		self.section = None

	def set_toggle(self, toggle):
		if not len(toggle):
			return
		toggle = toggle[0]
		if isinstance(toggle, dbus.Boolean):
			self.toggle_type = 'checkmark'
			self.toggle_state = toggle
		elif isinstance(toggle, str):
			self.toggle_type = 'radio'
			self.toggle_state = len(toggle) > 0


class DbusAppMenuItem(object):

	def __init__(self, item, path=[]):
		self.path   = path
		self.action = int(item[0])
		self.accel  = self.get_shorcut(item[1])
		self.separator = item[1].get('type', '') == 'separator'
		self.label  = item[1].get('label', '')
		self.text   = format_label(self.path + [self.label])
		self.enabled = item[1].get('enabled', True)
		self.visible = item[1].get('visible', True)
		self.toggle_state = item[1].get('toggle-state', 0) == 1
		self.toggle_type = item[1].get('toggle-type', '') # 'radio' or 'checkmark'
		self.icon_data = item[1].get('icon_data', bytearray())
		# Only used on Gtkapps
		self.section = None
		self.children = []

	def get_shorcut(self, item):
		shortcut = item.get('shortcut', '')
		if len(shortcut) == 0:
			return shortcut

		shortcut = shortcut[0]
		ret = ''
		for i, v in enumerate(shortcut):
			# The last one should be on caps?
			ret += '<' + v + '>' if (i != len(shortcut) - 1) else v
		return ret
