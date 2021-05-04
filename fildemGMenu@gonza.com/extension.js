'use strict';

const { loadInterfaceXML } = imports.misc.fileUtils;

const { Clutter, Gio, GLib, GObject, Meta, St } = imports.gi;

const AppSystem  = imports.gi.Shell.AppSystem.get_default();
const WinTracker = imports.gi.Shell.WindowTracker.get_default();

const ExtensionUtils = imports.misc.extensionUtils;
const Me = ExtensionUtils.getCurrentExtension();

const Settings = Me.imports.settings.FildemGlobalMenuSettings;
const Main = imports.ui.main;
const PanelMenu = imports.ui.panelMenu;
const WindowMenu = imports.ui.windowMenu;


function log(msg) {
	const debug = true;
	if (debug)
		global.log('[FILDEM_MENU] ' + msg);
}


const WindowActions = class WindowActions {
	constructor() {
		this._win = global.display.get_focus_window();
		this.actions = [];
	}

	// gitlab.gnome.org/GNOME/gnome-shell/-/blob/gnome-3-36/js/ui/windowMenu.js
	getActions() {
		let type = this._win.get_window_type();
		let win = this._win;

		if (win.can_minimize())
			this.actions.push('Minimize');

		if (win.can_maximize())
			this.actions.push(win.get_maximized() ? 'Unmaximize' : 'Maximize');

		if (win.allows_move())
			this.actions.push('Move');

		if (win.allows_resize())
			this.actions.push('Resize');

		if (win.titlebar_is_onscreen() && type != Meta.WindowType.DOCK && type != Meta.WindowType.DESKTOP)
			this.actions.push('Move Titlebar Onscreen')

		if (win.get_maximized() == Meta.MaximizeFlags.BOTH
			|| type == Meta.WindowType.DOCK
			|| type == Meta.WindowType.DESKTOP
			|| type == Meta.WindowType.SPLASHSCREEN) {

			this.actions.push('Always on Top' + (win.is_above() ? ' ✓' : ''));
		}

		if (Main.sessionMode.hasWorkspaces
			&& (!Meta.prefs_get_workspaces_only_on_primary() || win.is_on_primary_monitor())) {

			let isSticky = win.is_on_all_workspaces();

			if (win.is_always_on_all_workspaces()) {
				this.actions.push('Always on Visible Workspace' + (isSticky ? ' ✓' : ''));
			}

			if (!isSticky) {
				let workspace = win.get_workspace();
				if (workspace != workspace.get_neighbor(Meta.MotionDirection.LEFT))
					this.actions.push('Move to Workspace Left');

				if (workspace != workspace.get_neighbor(Meta.MotionDirection.RIGHT))
					this.actions.push('Move to Workspace Right');

				if (workspace != workspace.get_neighbor(Meta.MotionDirection.UP))
					this.actions.push('Move to Workspace Up');

				if (workspace != workspace.get_neighbor(Meta.MotionDirection.DOWN))
					this.actions.push('Move to Workspace Down');
			}
		}

		let display = global.display;
		let nMonitors = display.get_n_monitors();
		let monitorIndex = win.get_monitor();
		if (nMonitors > 1 && monitorIndex >= 0) {
			let dir = Meta.DisplayDirection.UP;
			let upMonitorIndex = display.get_monitor_neighbor_index(monitorIndex, dir);
			if (upMonitorIndex != -1)
				this.actions.push('Move to Monitor Up');

			dir = Meta.DisplayDirection.DOWN;
			let downMonitorIndex = display.get_monitor_neighbor_index(monitorIndex, dir);
			if (downMonitorIndex != -1)
				this.actions.push('Move to Monitor Down');

			dir = Meta.DisplayDirection.LEFT;
			let leftMonitorIndex = display.get_monitor_neighbor_index(monitorIndex, dir);
			if (leftMonitorIndex != -1)
				this.actions.push('Move to Monitor Left');

			dir = Meta.DisplayDirection.RIGHT;
			let rightMonitorIndex = display.get_monitor_neighbor_index(monitorIndex, dir);
			if (rightMonitorIndex != -1)
				this.actions.push('Move to Monitor Right');
		}
		
		if (win.can_close())
			this.actions.push('Close');

		return this.actions;
	}

	_doAction(action) {
		if (action.endsWith(' ✓')) {
			action = action.substr(0, action.length - 2);
		}
		let win = this._win;
		switch (action) {
			case 'Minimize':
				win.minimize();
				break;
			case 'Unmaximize':
				win.unmaximize(Meta.MaximizeFlags.BOTH);
				break;
			case 'Maximize':
				win.maximize(Meta.MaximizeFlags.BOTH);
				break;
			case 'Move':
				GLib.timeout_add(GLib.PRIORITY_DEFAULT, 100, () => {
					WindowMenu.WindowMenu.prototype._grabAction(win, Meta.GrabOp.KEYBOARD_MOVING, global.display.get_current_time_roundtrip());
				});
				break;
			case 'Resize':
				GLib.timeout_add(GLib.PRIORITY_DEFAULT, 100, () => {
					WindowMenu.WindowMenu.prototype._grabAction(win, Meta.GrabOp.KEYBOARD_RESIZING_UNKNOWN, global.display.get_current_time_roundtrip());
				});
				break;
			case 'Move Titlebar Onscreen':
				win.shove_titlebar_onscreen();
				break;
			case 'Always on Top':
				if (win.is_above())
					win.unmake_above();
				else
					win.make_above();
				break;
			case 'Always on Visible Workspace':
				if (win.is_on_all_workspaces())
					win.unstick();
				else
					win.stick();
				break;
			case 'Move to Workspace Left':
				this._moveToWorkspace(Meta.MotionDirection.LEFT);
				break;
			case 'Move to Workspace Right':
				this._moveToWorkspace(Meta.MotionDirection.RIGHT);
				break;
			case 'Move to Workspace Up':
				this._moveToWorkspace(Meta.MotionDirection.UP);
				break;
			case 'Move to Workspace Down':
				this._moveToWorkspace(Meta.MotionDirection.DOWN);
				break;
			case 'Move to Monitor Up':
				this._moveToMonitor(Meta.DisplayDirection.UP);
				break;
			case 'Move to Monitor Down':
				this._moveToMonitor(Meta.DisplayDirection.DOWN);
				break;
			case 'Move to Monitor Left':
				this._moveToMonitor(Meta.DisplayDirection.LEFT);
				break;
			case 'Move to Monitor Right':
				this._moveToMonitor(Meta.DisplayDirection.RIGHT);
				break;
			case 'Close':
				win.delete(global.get_current_time());
				break;
		}
	}

	_moveToWorkspace(dir) {
		let workspace = this._win.get_workspace();
		this._win.change_workspace(workspace.get_neighbor(dir));
	}

	_moveToMonitor(dir) {
		let monitorIndex = window.get_monitor();
		let newMonitorIndex = global.display.get_monitor_neighbor_index(monitorIndex, dir);
		if (newMonitorIndex != -1) {
			this._win.move_to_monitor(newMonitorIndex);
		}
	}
}

/**
 * A single Button like File, Edit, etc.
 */
var MenuButton = GObject.registerClass(
class MenuButton extends PanelMenu.Button {

	_init(label, menuBar) {
		label = label.replace('_', '');
		super._init(0.0, label);
		this._label = label;
		this._menuBar = menuBar;

		this.box = new St.BoxLayout({style_class: 'panel-status-menu-box menubar-button'});
		this.labelWidget = new St.Label({
			text: this._label,
			y_align: Clutter.ActorAlign.CENTER,
			reactive: true
		});
		this.box.add_child(this.labelWidget);
		this.add_child(this.box);
		this.connect('button-release-event', this.onButtonEvent.bind(this));
	}

	_onStyleChanged(actor) {
		super._onStyleChanged(actor);
		let padding = this._menuBar.extension.settings.get_int('min-padding');
		this._minHPadding = padding;
		this._natHPadding = padding;
	}

	onButtonEvent(actor, event) {
		if (event.get_button() !== 1)
			return Clutter.EVENT_PROPAGATE;

		this._menuBar.onButtonClicked(this._label);
		return Clutter.EVENT_STOP;
	}
});

const Cache = class Cache {
	constructor() {
		this.N = 10;
		this.lru = [];
		this.entries = {};
		this.lastQueriedKey = '';
	}

	get(key) {
		this.lastQueriedKey = key;
		return this.entries[key];
	}

	_set(key, value) {
		if (this.entries[key]) {
			const oldItem = this.lru.splice(this.lru.indexOf(key), 1);
		}
		this.lru.push(key);
		this.entries[key] = value;

		if (this.lru.length > this.N) {
			const toRemove = this.lru.pop();
			this.entries[toRemove] = undefined;
		}
	}

	withCache(f) {
		const self = this;
		const g = (param) => {
			self._set(self.lastQueriedKey, param);
			f(param);
		}
		return g;
	}
}

/**
 * This is a manager not a container
 */
const MenuBar = class MenuBar {
	constructor(proxy, extension) {
		this._menuButtons = [];
		this._proxy = proxy;
		this.extension = extension;
		// pixels from x_0 to the start of the menu
		this._width_offset = 300;
		this.MARGIN_FIRST_ELEMENT = 4;
		this._isShowingMenu = false;

		this._cache = new Cache();

		this._notifyFocusWinId = global.display.connect('notify::focus-window', this._onWindowSwitched.bind(this));
		this._proxy.listeners['SendTopLevelMenus'].push(this._cache.withCache(this.setMenus.bind(this)));
		this._proxy.listeners['MenuOnOff'].push(this._onMenuOnOff.bind(this));
		Main.panel.reactive = true;
		Main.panel.track_hover = true;

		this._panelEvHandlers = [];
		this._forceShowMenu = false;
		this._showAppMenuButton = false;
		this.setForceShowMenu();
		this.setHideAppMenuButton();

		Main.overview.connect('showing', this._onOverviewOpened.bind(this));
		Main.overview.connect('hiding', this._onOverviewClosed.bind(this));
	}

	setForceShowMenu() {
		this._forceShowMenu = !this.extension.settings.get_boolean('show-only-when-hover');

		if (!this._forceShowMenu) {
			this._panelEvHandlers.push(Main.panel.connect('enter-event', this._onPanelEnter.bind(this)));
			this._panelEvHandlers.push(Main.panel.connect('leave-event', this._onPanelLeave.bind(this)));
		} else {
			for (let h of this._panelEvHandlers) {
				Main.panel.disconnect(h);
			}
			this._panelEvHandlers = [];
		}
	}

	setHideAppMenuButton() {
		this._showAppMenuButton = !this.extension.settings.get_boolean('hide-app-menu');

		let appBtn = Main.panel._leftBox.get_children().filter(item => {
			item.get_first_child().constructor.name == 'AppMenuButton'
		});
		if (appBtn.length > 0) {
			this._appMenuButton = appBtn[0];
		}
		this._restoreLabel();
	}

	addMenuButton(label, setmargin) {
		let menuButton = new MenuButton(label, this);
		this._menuButtons.push(menuButton);
		const nItems = Main.panel._leftBox.get_children().length;
		menuButton.hide();
		if (setmargin)
			menuButton.set_style('margin-left: '+ this.MARGIN_FIRST_ELEMENT + 'px')
		Main.panel.addToStatusArea(label, menuButton, nItems, 'left');
	}

	setMenus(menus) {
		// The expansion/shrink can be annoying, so we only do it
		// when there’s no menus
		if (menus.length === 0) {
			this._hideMenu();
		}
		this.removeAll();
		let first = true;
		for (let menu of menus) {
			this.addMenuButton(menu, first);
			first = false;
		}
		if (this._forceShowMenu && !Main.overview.visibleTarget) {
			this._onPanelEnter();
		}
	}

	_onPanelEnter() {
		if (this._menuButtons.length === 0 || Main.overview.visibleTarget)
			return;

		this._hideAppMenuButton();
		this._showMenu();
	}

	// Hides the label and calculates the width
	_hideAppMenuButton() {
		let width = 0;
		for (let el of Main.panel._leftBox.get_children()) {
			let firstChild = el.get_first_child();
			if (firstChild === this._menuButtons[0]) {
				this._width_offset = width;
				break;
			}
			if (firstChild.constructor.name == 'AppMenuButton') {
				// [Deprecated]
				this._appMenuButton = firstChild;
				let label = firstChild._label;

				if (!this._showAppMenuButton) {
					label.hide();
				}
				this._width_offset = width + el.width;
				// break;
			}
			if (el.is_visible()) {
				width += el.get_width();
			}
		}
	}

	_showMenu() {
		this._menuButtons.forEach(btn => btn.show());
		this._menuButtons.forEach(btn => btn.ease({
			opacity: 255,
			mode: Clutter.AnimationMode.EASE_OUT_QUART,
			duration: 250
		}));
	}

	_onPanelLeave() {
		if (this._isShowingMenu || this._forceShowMenu)
			return;

		this._hideMenu();
	}

	_hideMenu() {
		this._menuButtons.forEach(btn => btn.ease({
			opacity: 0,
			mode: Clutter.AnimationMode.EASE_OUT_QUART,
			duration: 100,
			onComplete: () => { this._menuButtons.forEach(btn => btn.hide()); this._restoreLabel() }
		}));
	}

	_restoreLabel() {
		if (this._appMenuButton) {
			this._appMenuButton._label.show();
		}
	}

	_onMenuOnOff(on) {
		if (on) {
			this._onPanelEnter();
			this.onButtonClicked('__fildem_move', this._width_offset);
		} else {
			this._isShowingMenu = false;
			this._onPanelLeave();
		}
	}

	onButtonClicked(label) {
		this._isShowingMenu = true;
		this._proxy.EchoSignal(label, this._width_offset);
	}

	removeAll() {
		for (let e of this._menuButtons) {
			e.destroy();
		}
		this._menuButtons = [];
	}

	_onWindowSwitched() {
		this.removeAll();
		this._restoreLabel();
		this._hideMenu();
		const overview = Main.overview.visibleTarget;
		const focusApp = WinTracker.focus_app || Main.panel.statusArea.appMenu._targetApp;
		if (focusApp) {
			let windowData = {};
			// TODO does the window matter?
			let win = focusApp.get_windows()[0];
			let appId = focusApp.get_id(); // *.desktop			

			// Check cache
			let cachedValue = this._cache.get(appId);
			if (cachedValue) {
				this.setMenus(cachedValue);
			}

			// global.log(`app id: ${focusApp.get_id()} win id: ${win.get_id()}`);
			// TODO check pixel-saver extension for others way of obtaining xid
			let xid = '';
			try {
				xid = parseInt(win.get_description().match(/0x[0-9a-f]+/)[0]);
			} catch (e) {}
			windowData['xid'] = String(xid);
			for (let p in win) {
				if (p.startsWith('gtk_') && win[p] != null) {
					windowData[p] = win[p];
				}
			}
			this._proxy.WindowSwitched(windowData);
		}
	}

	_onOverviewOpened() {
		this._hideMenu();
	}

	_onOverviewClosed() {
		if (this._forceShowMenu && this._menuButtons.length) {
			this._hideAppMenuButton();
			this._showMenu();
		}
	}

	_disconnectAll() {
		// AppSystem.disconnect(this._appStateChangedId);
		// WinTracker.disconnect(this._notifyFocusAppId);
		for (let h of this._panelEvHandlers) {
			Main.panel.disconnect(h);
		}
		global.display.disconnect(this._notifyFocusWinId);
	}

	destroy() {
		this._disconnectAll();
		this.removeAll();
		this._restoreLabel();
	}
};

const ifaceXml = `
<node>
  <interface name="com.gonzaarcr.appmenu">
	<method name="EchoSignal">
	  <arg type="s" direction="in" name="menu"/>
	  <arg type="u" direction="in" name="x"/>
	</method>
	<method name="WindowSwitched">
	  <arg name="win_data" type="a{ss}" direction="in"/>
	</method>

	<signal name="WindowSwitchedSignal">
	  <arg name="win_data" type="a{ss}"/>
	</signal>
	<signal name="MenuActivated">
	  <arg name="menu" type="s"/>
	  <arg name="x" type="u"/>
	</signal>

	<method name="EchoMenuOnOff">
	  <arg name="on" type="b" direction="in"/>
	</method>
	<signal name="MenuOnOff">
	  <arg name="on" type="b"/>
	</signal>

	<method name="SendTopLevelMenus">
	  <arg name="top_level_menus" type="as" direction="in"/>
	</method>
	<signal name="SendTopLevelMenusSignal">
	  <arg name="top_level_menus" type="as"/>
	</signal>


	<method name="RequestWindowActions"/>
	<signal name="RequestWindowActionsSignal"/>

	<method name="ListWindowActions">
	  <arg name="actions" type="as" direction="in"/>
	</method>
	<signal name="ListWindowActionsSignal">
	  <arg name="actions" type="as"/>
	</signal>

	<method name="ActivateWindowAction">
	  <arg name="action" type="s" direction="in"/>
	</method>
	<signal name="ActivateWindowActionSignal">
	  <arg name="action" type="s"/>
	</signal>
  </interface>
</node>`;

const TestProxy = Gio.DBusProxy.makeProxyWrapper(ifaceXml);

const BUS_NAME = 'com.gonzaarcr.appmenu';
const BUS_PATH = '/com/gonzaarcr/appmenu';

class MyProxy {
	constructor() {
		this._createProxy();
		this._handlerIds = [];
	}

	async _createProxy() {
		this._proxy = new TestProxy(
			Gio.DBus.session,
			BUS_NAME,
			BUS_PATH,
			this._onProxyReady.bind(this)
		);
		this.listeners = {
			'MenuActivated': [],
			'SendTopLevelMenus': [],
			'MenuOnOff': []
		}
	}

	async _onProxyReady(result, error) {
		let id = undefined;
		id = this._proxy.connectSignal('SendTopLevelMenus', this._onSendTopLevelMenus.bind(this));
		this._handlerIds.push(id);
		id = this._proxy.connectSignal('RequestWindowActionsSignal', this._onRequestWindowActionsSignal.bind(this));
		this._handlerIds.push(id);
		id = this._proxy.connectSignal('ActivateWindowActionSignal', this._onActivateWindowActionSignal.bind(this));
		this._handlerIds.push(id);
		id = this._proxy.connectSignal('MenuOnOff', this._onMenuOnOff.bind(this));
		this._handlerIds.push(id);
	}

	async _onMenuActivated(proxy, nameOwner, args) {
		global.log(`TestSignal: ${args[0]}`);
	}

	async _onSendTopLevelMenus(proxy, nameOwner, args) {
		let topLevelMenus = args[0];
		for (let callback of this.listeners['SendTopLevelMenus']) {
			callback(topLevelMenus);
		}
	}

	async _onRequestWindowActionsSignal(proxy, nameOwner, args) {
		this._currentWindow = new WindowActions();
		let actions = this._currentWindow.getActions();
		this._proxy.ListWindowActionsRemote(actions);
	}

	async _onActivateWindowActionSignal(proxy, nameOwner, args) {
		this._currentWindow._doAction(args[0]);
	}

	async _onMenuOnOff(proxy, nameOwner, args) {
		for (let callback of this.listeners['MenuOnOff']) {
			callback(args[0]);
		}
	}

	_onNameOwnerChanged(proxy, sender, [name, oldOwner, newOwner]) {
		global.log(`${name} ${oldOwner} ${newOwner}`)
	}

	async WindowSwitched(windowData) {
		this._proxy.WindowSwitchedRemote(windowData);
	}

	async EchoSignal(menu, x) {
		this._proxy.EchoSignalRemote(menu, x);
	}

	destroy() {
		for (let id of this._handlerIds) {
			this._proxy.disconnectSignal(id);
		}
		this._handlerIds = [];
	}
};


class Extension {
	constructor(settings) {
		this.settings = settings;
		this._handlerIds = [];
		this.myProxy = new MyProxy();
		this.menubar = new MenuBar(this.myProxy, this);

		this._connectSettings();
	}

	_connectSettings() {
		this._handlerIds.push(this.settings.connect(
			'changed::show-only-when-hover',
			() => { this.menubar.setForceShowMenu(); }
		));
		this._handlerIds.push(this.settings.connect(
			'changed::hide-app-menu',
			() => { this.menubar.setHideAppMenuButton(); }
		));
	}

	destroy() {
		this._disconnectSettings();

		this.menubar.destroy();
		this.myProxy.destroy();
	}

	_disconnectSettings() {
		for (let h of this._handlerIds) {
			this.settings.disconnect(h);
		}
	}
}


let extension;

function init(metadata) {
}

function enable() {
	let settings = new Settings(Me.metadata['settings-schema']);
	extension = new Extension(settings);
}

function disable() {
	extension.destroy();
	extension = null;
}
