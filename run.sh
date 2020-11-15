#!/bin/bash

SCRIPT_PATH=${0%/*}
cd $SCRIPT_PATH

if [ $XDG_SESSION_TYPE = 'x11' ]; then
	export UBUNTU_MENUPROXY=0; python3 ./command.py
else
	export UBUNTU_MENUPROXY=0; export GDK_BACKEND=x11; python3 ./command.py
fi

