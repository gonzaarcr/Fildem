import gi
import os

gi.require_version('Keybinder', '3.0')

from gi.repository import Keybinder

from fildem.utils.wayland import is_wayland


class GlobalKeybinder:
	"""
	Global keybinder for mnemonic, like Alt+F for files, etc.
	"""
	def __init__(self, callback=None):
		Keybinder.init()
		self.keybinding_strings = []
		self.keybinder_callback = callback

	@classmethod
	def create(cls, callback=None):
		if not is_wayland():
			return cls(callback)
		else:
			return DummyKeybinder()

	def add_keybinding(self, character):
		acc = '<Alt>' + character
		Keybinder.bind(acc, lambda accelerator: self.on_keybind_activated(character))
		self.keybinding_strings.append(acc)

	def on_keybind_activated(self, char):
		self.keybinder_callback(char)

	def remove_all_keybindings(self):
		for k in self.keybinding_strings:
			Keybinder.unbind(k)
		self.keybinding_strings = []


class DummyKeybinder:

	def add_keybinding(self, character):
		pass

	def remove_all_keybindings(self):
		pass
