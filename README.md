# Fildem

## Global menu for Gnome

[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg)](https://buymeacoffee.com/gonza)

![Fildem](https://user-images.githubusercontent.com/19943481/95288612-1d272a80-083f-11eb-9400-be88f61e054d.png)

This project is a fork of gnomehud with the adition of a global menu bar. It’s consist of a Gnome Shell extension and a external program, you must install both for the application to work.

You can also bring a HUD menu with Alt + Space (on Xorg).

This is a prototype, as I don’t know if people will like or how much it will last until devs nuke it, so fell free to let me know your opinion.

## Installation

### Extension

To install the extension, download it from the [Gnome extensions website](https://extensions.gnome.org/extension/4114/fildem-global-menu/).

### Ubuntu

Download the .deb file from the releases section and run `sudo apt install ./fildem_*.deb`

### Arch

Download the .zst file from the releases section and run `sudo pacman -U ./python3-fildem*.zst`

## Configuration

In order for the application to work, you must configure the following files (aplies to all operating systems):

- Create the file `~/.gtkrc-2.0` and append `gtk-modules="appmenu-gtk-module"`
- The file `~/.config/gtk-3.0/settings.ini` should have the line `gtk-modules="appmenu-gtk-module"` under [Settings]. If it doesn’t exist create it and paste the following

```
[Settings]
gtk-modules="appmenu-gtk-module"
```

## Running

After installation you’ll have two executables, `fildem` and `fildem-hud`.  To check if it works use the first one. `fildem-hud` is for using he HUD, if you are on Xorg, you already have it bound to Alt + Space. If you are on Wayland, you can bind some keybinding to that command.

## Customization

### Menu always visible

By default, the menu is visible when you hover the mouse on the panel. If you want the menu to be always visible, unselect “Show menu only when the mouse is over the panel” in the preferences of the extension.

### AppMenu Button always visible

The AppMenu button shows the application name or window title (if you have some extension) in the panel. By default, the fildem extension hides that label when the menu is being shown. If you want it to be always visible, you can unselect “Hide App Menu label” in the preferences of the extension.

### Reduce space between buttons

If the menu shown on the panel is shifted with relation to the one that appears, you can tweak the padding in the preferences window of the extension.

### Remove space in between buttons

In some gnome themes, the buttons have a small spacing between them. This can make the buttons easy to miss and unfocusing our window if it’s not maximized. To fix this, add this somewhere on your `gnome-shell.css` theme:

```
#panel #panelLeft {
  spacing: 0px; }
#panel #panelLeft .panel-button {
  spacing: 0px; }
```

## Running the program at startup

If you manage to make the program work and want to have it running automatically at startup you can add an entry to `gnome-session-properties` with the name of the program and the path to execute it.

## Create a shortcut for the HUD on Wayland

Since it’s not possible to creat a shortcut from the app on Wayland, you have to create it yourself. Go to Settings → Keyboard Shorcuts and create a shortcut that executes `inithud.sh`.

## State of the Apps

To see a list of apps that work check [the wiki](https://github.com/gonzaarcr/Fildem/wiki/Using#state-of-the-apps)

## Installation troubleshooting

If you have any question on to get it to work, please don’t create an issue, use [this discussion](https://github.com/gonzaarcr/Fildem/discussions/33).