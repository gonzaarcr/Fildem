const GObject = imports.gi.GObject;
const Gio = imports.gi.Gio;
const GioSSS = Gio.SettingsSchemaSource;

const Me = imports.misc.extensionUtils.getCurrentExtension();

var FildemGlobalMenuSettings = GObject.registerClass(
class FildemGlobalMenuSettings extends Gio.Settings {
	_init(schema) {
		let schemaDir    = Me.dir.get_child('schemas');
		let schemaSource = null;

		if (schemaDir.query_exists(null)) {
			schemaSource = GioSSS.new_from_directory(schemaDir.get_path(), GioSSS.get_default(), false);
		} else {
			schemaSource = GioSSS.get_default();
		}

		let schemaObj = schemaSource.lookup(schema, true);

		if (!schemaObj) {
			let message = `Schema ${schema} could not be found for extension ${Me.metadata.uuid}`;
			throw new Error(message + '. Please check your installation.');
		}

		super._init({ settings_schema: schemaObj });
	}
});
