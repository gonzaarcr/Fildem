import GObject from 'gi://GObject?version=2.0';
import Gio from 'gi://Gio?version=2.0';
const GioSSS = Gio.SettingsSchemaSource;

var FildemGlobalMenuSettings = GObject.registerClass(
class FildemGlobalMenuSettings extends Gio.Settings {
	constructor(conf, schema) {
		super(schema, conf);
	}

	_init(schema, conf) {
		let schemaDir    = conf.dir.get_child('schemas');
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

export {FildemGlobalMenuSettings};