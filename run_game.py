#!/usr/bin/env python
from the_window import GameWindow
from screens import level_from_file
import pyglet

def go():
	window = GameWindow()
	window.thescreen = level_from_file.GameplayScreen(window, "one")
	window.unpause()
	pyglet.app.run()

if __name__ == "__main__":
	go()
