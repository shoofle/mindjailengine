from the_window import GameWindow
from screens import level_from_file
import pyglet

if __name__ == "__main__":
	window = GameWindow()
	window.thescreen = level_from_file.GameplayScreen(window, "one")
	window.unpause()
	pyglet.app.run()