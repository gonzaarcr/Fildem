const GObject = imports.gi.GObject;
const Gio = imports.gi.Gio;
const Gtk = imports.gi.Gtk;
const Config = imports.misc.config;

const Me = imports.misc.extensionUtils.getCurrentExtension();
const Settings = Me.imports.settings.FildemGlobalMenuSettings;

const SHELL_VERSION = Config.PACKAGE_VERSION;


const PrefsWidget = GObject.registerClass(
class PrefsWidget extends Gtk.Box {	

	_init(settings, params) {
		super._init(params);

		this._buildable = new Gtk.Builder();
		this._buildable.add_from_file(Me.path + '/settings.ui');

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

function buildPrefsWidget() {
	let settings = new Settings(Me.metadata['settings-schema']);
	let widget = new PrefsWidget(settings);
	widget.show_all();

	return widget;
}
