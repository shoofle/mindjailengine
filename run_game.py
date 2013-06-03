import mindjailengine
import load_level_screen

if __name__ == "__main__":
	window = mindjailengine.GameWindow()
	window.thescreen = load_level_screen.TheScreen(window, "one")
	window.main_loop()
