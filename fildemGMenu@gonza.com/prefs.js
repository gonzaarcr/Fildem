import GObject from 'gi://GObject?version=2.0';
import Gio from 'gi://Gio?version=2.0';
import Gtk from 'gi://Gtk?version=4.0';
import * as Config from 'resource:///org/gnome/Shell/Extensions/js/misc/config.js';

// import {Extension as Me} from 'resource:///org/gnome/shell/extensions/extension.js';
import {ExtensionPreferences} from 'resource:///org/gnome/Shell/Extensions/js/extensions/prefs.js';
import {FildemGlobalMenuSettings as Settings} from './settings.js';

const SHELL_VERSION = Config.PACKAGE_VERSION;


const PrefsWidget = GObject.registerClass(
class PrefsWidget extends Gtk.Box {	

	_init(conf, settings, params) {
		super._init(params);

		this._buildable = new Gtk.Builder();
		this._buildable.add_from_file(conf.path + '/settings.ui');

		let prefsWidget = this._getWidget('prefs_widget');
		if (SHELL_VERSION < '40') {
			this.add(prefsWidget);
		} else {
			this.append(prefsWidget);
		}

		this._settings = settings;
		this._bindBooleans();
    	this._bindIntSpins();
	}

	show_all() {
		if (SHELL_VERSION < '40')
			super.show_all();
	}

	_getWidget(name) {
		let wname = name.replace(/-/g, '_');
		return this._buildable.get_object(wname);
	}

	/********************
	 * Int Spins
	 ********************/

	_getIntSpins() {
		return [
			'min-padding'
		];
	}

	_bindIntSpin(setting) {
		let widget = this._getWidget(setting);
		widget.set_value(this._settings.get_int(setting));
		widget.connect('value-changed', (spin) => {
			this._settings.set_int(setting, spin.get_value());
		});
	}

	_bindIntSpins() {
		this._getIntSpins().forEach(this._bindIntSpin, this);
	}

	/********************
	 * Booleans
	 ********************/

	_getBooleans() {
		return [
			'show-only-when-hover',
			'hide-app-menu'
		];
	}

	_bindBoolean(setting) {
		let widget = this._getWidget(setting);
		this._settings.bind(setting, widget, 'active', Gio.SettingsBindFlags.DEFAULT);
	}

	_bindBooleans() {
		this._getBooleans().forEach(this._bindBoolean, this);
	}
});

function init() {

}

export default class FildemMenuExtensionPrefs extends ExtensionPreferences {
	getPreferencesWidget() {
		return buildPrefsWidget(this);
	}
}

function buildPrefsWidget(conf) {
	let settings = new Settings(conf, conf.metadata['settings-schema']);
	let widget = new PrefsWidget(conf, settings);
	widget.show_all();

	return widget;
}
