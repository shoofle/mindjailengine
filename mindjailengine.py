#!/bin/usr/python
############################## Sup, dawg.
# This is a game engine or something, by Shoofle Munroe, this is being written at jul 24, 3:51 PM, 2013 (probably), contact me if you wanna use stuff or whatever at xsigma@gmail.com . Thanks!
############################## Wheeeeee! a game engine! and games!

import pyglet
from pyglet import window, clock, text

from vectors import v

class GameWindow(window.Window):
	"""This class represents the main window for the game. 

	Screens take a reference to the window that displays them in their constructor, and, to change 
		what screen is up, simply change what window.thescreen points to.

	This GameWindow class also takes care of input handling, and in theory the screens should be able to 
		just use a standard interface instead of having to interface with whatever windowing library we use.
		At the moment we use pyglet, but... that might not stay.

	I'm not actually sure whether the main engine entry point - for starting applications and stuff - should be a the window or the app. The app makes a little more sense to me, but pyglet has a really lightweight object for it - it's basically just the event loop. I think it'd make it harder to refactor to a different windowing system.
	"""

	def __init__(self, screen_module = None, *args, **kwargs):
		window.Window.__init__(self, *args, **kwargs)
		self.set_mouse_visible(False)

		self.keys_have_been_pressed = False

		self.total_time = 0
		self.framerate = 0
		self.framerate_decay = 0.6

		# The 'clock' object pyglet provides is global. It might be nice to give us engine-specific clock functionality, or have this here for switching to a different windowing library in the future. Maybe this is just overthinking it! Anyway, this exposes it to the guts of the game in case they need it.
		self.clock = clock
		self.clock.set_fps_limit(60)

	def main_loop(self):
		"""The main execution loop for the program."""
		dt = self.clock.tick()

		while not self.has_exit: # This should be changed to simply use pyglet's on_draw event. I think.
			dt = clock.tick()

			self.update(dt)

	def update(self, time_step):
		self.dispatch_events() # Apparently this is just a legacy call, that we don't need. Uh oh! Most applications are supposed to use the pyglet.app.run function. Huh. I guess this whole thing could do with more severe refactoring.
		self.clear()

		# Draw the screen! This should, probably, be moved into an on_draw behavior. TODO!
		self.thescreen.draw()

		# Do world logic screen updates!
		self.thescreen.update(time_step)

		# Keep a running time. You gotta have a running time!
		self.total_time = self.total_time + time_step

		# Calculate the framerate as a running average. This is a little thing, but hey. I like it. Sometimes you gotta know your framerate! And sometimes you gotta know your framerate in such a way that it's not extremely sensitive to tiny variations!
		self.framerate = (1-self.framerate_decay)*(1/time_step) + self.framerate_decay*self.framerate

		self.flip() # if we're using on_draw, then we don't need this at all.

	"""Pyglet has a number of input event functions. These handlers simply pass them through to the active screen."""
	def on_key_press(self, symbol, modifiers):
		# on_key_press and on_key_release both have a little bit of weirdness. This is just to deal with the fact that we don't want to accept a "key has been released!" event if the key was pressed before the window opened. This is a little bit hacky - in theory, it should do this on a per-key basis. It might not even be necessary, though!
		# I'm not sure if this slows the game down at all. I assume it doesn't.
		self.keys_have_been_pressed = True
		self.thescreen.on_key_press(symbol, modifiers)
		window.Window.on_key_press(self, symbol,modifiers)
	def on_key_release(self,symbol,modifiers):
		# See also the comment in on_key_press about the check for whether keys have been pressed.
		if not self.keys_have_been_pressed: return 
		self.thescreen.on_key_release(symbol, modifiers)
	def on_mouse_press(self, x, y, button, modifiers): 
		self.thescreen.on_mouse_press(x, y, button, modifiers)
	def on_mouse_drag(self, x, y, dx, dy, button, modifiers): 
		self.thescreen.on_mouse_drag(x, y, dx, dy, button, modifiers)
	def on_mouse_motion(self, x, y, dx, dy): 
		self.thescreen.on_mouse_motion(x, y, dx, dy)


# This branch - executed if this file is run directly as a script - is no longer necessary. 
# The behavior to start the application has been moved to the file `run_game.py`.
# This is only being kept for legacy purposes, or maybe for debug. Maybe it's just to make me feel better!
debug = False
if __name__ == "__main__":
	"""What to do if we're being launched directly!"""
	wind = GameWindow()

	import mod_screen as screen_module
	wind.thescreen = screen_module.TheScreen(wind)

	if debug:
		import cProfile
		cProfile.run('wind.main_loop()')
	else:
		wind.main_loop()
