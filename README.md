# Fildem

## Global menu for Ubuntu 20

[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg)](https://buymeacoffee.com/gonza)

![Fildem](https://user-images.githubusercontent.com/19943481/95288612-1d272a80-083f-11eb-9400-be88f61e054d.png)

This project is a fork of gnomehud with the adition of a global menu bar. To install it you have to download this repo and install the extension copying/moving the `fildemGMenu@gonza.com` folder into `~/.local/share/gnome-shell/extensions`. Then, you have to run the app with `./run.sh`.

You can also bring a HUD menu with Alt + Space.

This is a prototype, as I don’t know if people will like or how much it will last until devs nuke it, so fell free to let me know your opinion.

## installation

### Ubuntu 20

You can install the modules with

```
sudo apt install libbamf3-dev bamfdaemon libkeybinder-3.0-dev appmenu-gtk2-module appmenu-gtk3-module unity-gtk-module-common
```

And install the python dependency:

```
pip3 install fuzzysearch
```

And then configure the following files:

- Create the file `~/.gtkrc-2.0` and append `gtk-modules="appmenu-gtk-module"`
- The file `~/.config/gtk-3.0/settings.ini` should have the line `gtk-modules="appmenu-gtk-module"` under [Settings]. If it doesn’t exist create it and paste the following

```
[Settings]
gtk-modules="appmenu-gtk-module"
```

### Arch

I got it to run on a vm, since Arch is so customizable I can’t guaranted it will work on all system, but the modules installed were

```
pacman -S bamf appmenu-gtk-module libkeybinder3 libdbusmenu-gtk2 libdbusmenu-gtk3 libdbusmenu-qt5
```

You also have to install `fuzzysearch` with pip (`pip3 install fuzzysearch`) and edit the files explained on the Ubuntu section.

## Customization

### Menu always visible

If you don’t want to have to hover the menu to view it, change `FORCE_SHOW_MENU` in `extension.js` to `true`, and reload the shell (Alt+F2, r).

### AppMenu Button always visible

The AppMenu button is the gnome button that appears on the top panel. You can set `SHOW_APPMENU_BUTTON` to `true` if you want that. If you are using Unite extension, you can set the button to show the app name instead of the title, otherwise it will be to long and the menu will appear at the right side of the panel.

### Remove space in between buttons

In some gnome themes, the buttons have a small spacing beetween them. This can make the buttons easy to miss and unfocusing our window if it’s not maximized. To fix this, add this somewhere on your `gnome-shell.css` theme:

```
#panel #panelLeft {
  spacing: 0px; }
#panel #panelLeft .panel-button {
  spacing: 0px; }
```

## Running the program at startup

If you manage to make the program work and want to have it running automatically at startup you can add an entry to `gnome-session-properties` with the name of the program and the path to execute it.

## State of the Apps

To see a list of apps that work check [the wiki](https://github.com/gonzaarcr/Fildem/wiki/Using#state-of-the-apps)

## Installation troubleshooting

If you have any question on to get it to work, please don’t create an issue, use [this discussion](https://github.com/gonzaarcr/Fildem/discussions/33).
