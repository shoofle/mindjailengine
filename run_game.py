from the_window import GameWindow
import load_level_screen
import pyglet

if __name__ == "__main__":
	window = GameWindow()
	window.thescreen = load_level_screen.GameplayScreen(window, "one")
	pyglet.app.run()
