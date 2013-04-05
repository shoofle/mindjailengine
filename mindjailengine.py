#!/bin/usr/python
############################## Sup, dawg.
# This is a game engine or something, by Shoofle Munroe, this is being written at jul 24, 3:51 PM, contact me if you wanna use stuff or whatever at xsigma@gmail.com . Thanks!
############################## Wheeeeee! a game engine! and games!

import pyglet
from pyglet import window, clock, text

import mod_screen
from vectors import v

import cProfile

class GameWindow(window.Window):
	"""This class represents the main window for the game. 

	This class is instantiated once, for the window the game runs in. 
	Instantiating this is how the game starts everything.
	This object creates a screen, from mod_screen, on the line under "list of screens to prepare".
	It then updates that screen at 60fps.
	Screens take a reference to the window that displays them in their constructor, and, to change 
	  what screen is up, simply change what window.thescreen points to. For example, when you pause 
	  the game, the main game screen (an instance of mod_screen.TheScreen) instantiates a new 
	  PauseScreen, gives it a pointer to itself, and then sets window.thescreen = pause_screen_instance.
	Now the pause screen is the active screen, and it knows the screen that instantiated it, which it
	  can return to at any point.

	This GameWindow class also takes care of input handling, and in theory the screens should be able to 
	  just use a standard interface instead of having to interface with whatever windowing library we use.
	  At the moment we use pyglet, but... that might not stay.

	"""
	def __init__(self, *args, **kwargs):
		"""Set us up the window!"""
		window.Window.__init__(self, *args, **kwargs)
		self.set_mouse_visible(False)

		#self.gridres = 10

		# self.keyst is the dict of all the keys which are currently being pressed, referenced by symbol strings from key.
		self.keyspressed = False

		# keytext is a multi-line label to hold data about what keys are being pressed, and, um, stuff?
		# Should have a height of three lines, 40 characters wide?
		self.runtime = 0
		self.numsteps = 0
		self.avefps = 0
		self.decay = 0.6

		# List of screens to prepare.
		self.thescreen = mod_screen.TheScreen(self)

		#for thing in self.components:
		#	thing.idnum = self.components.index(thing);
		#	#self.register(thing.idnum, thing.x)
		#	self.componentset.add(thing)


	def main_loop(self):
		"""Main runtime loop, which calls the stuff."""

		clock.set_fps_limit(60)
		dt = clock.tick()

		while not self.has_exit:
			dt = clock.tick()

			self.dispatch_events()
			self.clear()

			self.thescreen.draw()
			self.thescreen.update(0.05)

			self.runtime = self.runtime + dt
			self.avefps = (1-self.decay)/dt + self.decay*self.avefps

			self.flip()

	def on_key_press(self, symbol, modifiers):
		self.keyspressed = True
		self.thescreen.on_key_press(symbol, modifiers)
		window.Window.on_key_press(self, symbol,modifiers)
	def on_key_release(self,symbol,modifiers):
		if not self.keyspressed: pass 
		self.thescreen.on_key_release(symbol, modifiers)
	def on_mouse_press(self, x, y, button, modifiers): self.thescreen.on_mouse_press(x, y, button, modifiers)
	def on_mouse_drag(self, x, y, dx, dy, button, modifiers): self.thescreen.on_mouse_drag(x, y, dx, dy, button, modifiers)
	def on_mouse_motion(self, x, y, dx, dy): self.thescreen.on_mouse_motion(x,y,dx,dy)


if __name__ == "__main__":
	"""What to do if we're being launched directly!"""
	wind = GameWindow()
#	cProfile.run('wind.main_loop()')
	wind.main_loop()
