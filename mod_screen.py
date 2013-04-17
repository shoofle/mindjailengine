#!/usr/bin/env python

import pyglet
from pyglet import window, text, graphics
import pyglet.gl as opengl
from pyglet.window import key

import random
import math

import shapes
from vectors import v
import collision_structures

from components import *
from world_objects import *

""" A class containing a module for the game. """
class TheScreen(object):
	""" Encapsulates the main action of gameplay - whizzing around in a terrain, shooting things, etc.

	In the future, a lot of the behavior handled here will be offloaded to level-specific scripting and such,
	  but TheScreen (TODO: retitle to something descriptive) should handle tracking the set of objects, firing
	  keyboard events to the objects that want them, collision detection, physics in general, collision events,
	  and for now it tracks health and score and such.
	TheScreen.addcomponent(thing, static, priority, listener), which adds 'thing' to the components list.

	TODO: this is going to be changed over to a component-entity system to separate out physics from other behaviors.
	  Instead, there's going to be a... recipe? system, wherein objects will be built by requesting a new entity 
	  identifier (just a unique reference to a new object) and then adding a number of components, each of which
	  describes one aspect of the entity's behavior, to it. So it should look like this:
	    player_object = self.new_entity()
	    player_object.add_components(RigidBody, CameraFollower, Drawable, ControlsListener, BallFlightBehaviors)
	    player_object.RigidBody.position = 0,0
	    player_object.RigidBody.mass, player_object.RigidBody.radius = 5, 10
	    player_object.CameraFollower.spring_constant = 10
	    player_object.Drawable = # no idea how this is going to be defined in practice
	  and that would add those behaviors into the entity, and also to the systems that define how they behave.
	  Some components require other components, so for example when it adds BallFlightBehaviors, it checks to see
	    if there's a ControlsListener attached to this entity. Some components are simply collections of 
	    components - the RigidBody component is a Position component plus a Shape component, with a mass and so on.
	  So RigidBody would define the solid dynamics of it, CameraFollower would make sure that our camera follows,
	    ControlsListener would get events and pass them in, and BallFlightBehaviors would make it so that
	    those events are handled and turned into flying around.
	  A free-falling ball might look like this:
	    free_ball = self.new_entity()
	    free_ball.add_components(RigidBody, Drawable)
	  An enemy spawner would look like this:
	    spawner = self.new_entity()
	    spawner.add_components(RigidBody, Drawable, EnemyCreatingBehavior)
	  These would all be defined in functions so that instead you can simply say make_spawner(location) twice 
	    instead of having to actually define the spawner twice. That function is what I call a recipe - it says
	    "make a new entity, and put on the following pieces in this order".
	That's a lot of words.
	"""
	def __init__(self, pwin):
		""" Initialize the gamescreen. pwin is the parent window. """
		self.pwin = pwin
		self.width = pwin.width
		self.height= pwin.height
		self.draw_debug = False

		self.killcount = 0
		self.total_time = 0
		self.camera_rect = CollisionComponent(owner=None, pos=v(0,0), shape=shapes.Rectangle(-1,1,-1,1)) # (xmin, xmax), (ymin, ymax)
		self.constants = {'drag':5, 'gravity':v(0,-15000), 'elasticity':0.7, 'friction':0.9, 'displace':0.7}

		opengl.glEnable(opengl.GL_BLEND)
		opengl.glBlendFunc(opengl.GL_SRC_ALPHA,opengl.GL_ONE)
		opengl.glLineWidth(2.0)

#		opengl.glEnable(opengl.GL_POINT_SMOOTH)
#		opengl.glHint(opengl.GL_POINT_SMOOTH_HINT,opengl.GL_NICEST)
#		opengl.glEnable(opengl.GL_LINE_SMOOTH)
#		opengl.glHint(opengl.GL_LINE_SMOOTH_HINT,opengl.GL_NICEST)
#		opengl.glEnable(opengl.GL_POLYGON_SMOOTH)
#		opengl.glHint(opengl.GL_POLYGON_SMOOTH_HINT,opengl.GL_NICEST)
		
		#Activate the depth buffer.
		opengl.glEnable(opengl.GL_DEPTH_TEST)

		#Lighting!
		#opengl.glEnable(opengl.GL_LIGHTING)
		#opengl.glEnable(opengl.GL_LIGHT0)
		#opengl.glLightf(opengl.GL_LIGHT0, opengl.GL_LINEAR_ATTENUATION, 0.05)

		###########
		# Now, since this screen represents gameplay, we're going to initialize all the elements of the game we're playing.
		# For now, this is just a pile of stuff.
		###########
		
		# Set up all the different lists of objects in the world. These roughly correspond to managers! Sort of.
		
		self.entities = []
		
		self.physics_objects = []

		self.collision_objects = []
		self.nonstatic_objects = []
		self.coltree = collision_structures.SpatialGrid()

		self.draw_objects = []
		self.draw_priority = []
		self.draw_tree = collision_structures.SpatialGrid()
		
		self.listeners = []

		# and now, the things!

		playerobj = self.add_entity( PlayerBall(self, location = v(0,0)) )
		self.add_entity( CameraFollower(self, latch=playerobj, spring=50, damping=10) )

		self.add_entity( FreeBall(self, location = v(0,-50)) )
		self.add_entity( FreeBall(self, location = v(-100,0)) )
		self.add_entity( FreeBall(self, location = v(100,0)) )
		self.add_entity( FreeBall(self, location = v(0, 1700), rad=80) )

		self.add_entity( Spawner(self, location = v(-500, 1500), rad=250) )
		self.add_entity( Spawner(self, location = v(500, 1500), rad=250) )
		
		self.add_entity( EnemyBall(self, location = v(-200,30), rad=30) )
		self.add_entity( EnemyBall(self, location = v(-260,0), rad=30) )
		self.add_entity( EnemyBall(self, location = v(-100,60), rad=30) )

		#self.batch_add_entity( ObstacleBall(self, location = v(-120,-200), rad=50) )
		#self.batch_add_entity( ObstacleBall(self, location = v(60,-300), rad=30) )
		#self.batch_add_entity( ObstacleBall(self, location = v(0,-800), rad=200) )
		#self.batch_add_entity( ObstacleBall(self, location = v(-300,-500), rad=100) )
		#self.batch_add_entity( ObstacleBall(self, location = v(200,300), rad=40) )
		for i in range(100):
			position = v(random.uniform(-1,1)*4000, random.uniform(-1,1)*1000)
			self.add_entity( ObstacleBall(self, location = position, rad=40) )

		wavelength = 600
		depth = 150
		h = -1000
		for i in range(-10, 10):
			self.add_entity( ObstacleLine(self, location=v(i*wavelength, h), endpoint=v((i+0.5)*wavelength, h+depth), thick=20) )
			self.add_entity( ObstacleLine(self, location=v((i+0.5)*wavelength, h+depth), endpoint=v((i+1)*wavelength, h), thick=20) )

		# The scoop.
		#self.batch_add_entity( ObstacleLine(self, location=v(2000, 0), endpoint=v(500, -1500), thick=20), static=True )
		#self.batch_add_entity( ObstacleLine(self, location=v(-2000, 0), endpoint=v(-500, -1500), thick=20), static=True )
		#self.batch_add_entity( ObstacleLine(self, location=v(-1000, -1500), endpoint=v(1000, -1500), thick=20), static=True )

		# The A-frame roof.
		#self.batch_add_entity( ObstacleLine(self, location=v(0, 1500), endpoint=v(-1000, -150),thick = 20), static=True )
		#self.batch_add_entity( ObstacleLine(self, location=v(0, 1500), endpoint=v(1000, -150),thick = 20), static=True )


		#self.batch_add_entity( InvertBall(self, location = v(0,1000), rad=2600), static=True )

#		background = procedural.Background()
#		background.basic_component = BasicComponent(screen=self, tangible=False, immobile=True)
#		self.add_entity( background, static=True, collisions=False, priority=True )


		###########
		# And now the list of entities is done.
		###########


	def add_entity(self, thing):
		""" Add an entity to the world. """
		try:
			if hasattr(thing, 'basic_component'):
				self.entities.append(thing)
			if hasattr(thing, 'physics_component'):
				self.physics_objects.append(thing.physics_component)
			if hasattr(thing, 'collision_component'):
				self.collision_objects.append(thing.collision_component)
				self.coltree.append(thing.collision_component)
				if not thing.collision_component.immobile: 
					self.nonstatic_objects.append(thing.collision_component)
			if hasattr(thing, 'renderable_component'):
				self.draw_objects.append(thing.renderable_component)
				if thing.renderable_component.priority:
					self.draw_priority.append(thing.renderable_component)
				else:
					self.draw_tree.append(thing.renderable_component)
			if hasattr(thing, 'input_listeners'):
				self.listeners.append(thing)
		except AttributeError as e: 
			print("There was some kind of problem building the list of objects in the world. \n{}".format(e))
		finally: 
			return thing

	def killcountincrease(self): # increment the kill count!
		self.killcount = self.killcount + 1

	def draw(self):
		""" Instructs each entity to draw itself, starting with the entities in the priority set. """
		# Clear the screen. The background is white. Also clear the buffers.
		opengl.glClearColor(1.0,1.0,1.0,0.0)
		opengl.glClear(opengl.GL_COLOR_BUFFER_BIT | opengl.GL_DEPTH_BUFFER_BIT)
		
		opengl.glPushMatrix()
		for thing in self.draw_priority:
			thing.draw()
		for thing in self.draw_tree.collisions(self.camera_rect):
			thing.draw()
		if self.draw_debug: 
			self.coltree.draw()
			self.draw_tree.draw()
		opengl.glPopMatrix()

	def update(self, timestep):
		"""Update the state of each entity in the game world."""
		self.total_time += timestep

		dead_things = (t for t in self.entities if t.basic_component.dead)

		for thing in dead_things:
			self.entities.remove(thing)
			if thing.physics_component in self.physics_objects: 	self.physics_objects.remove(thing.physics_component)
			
			if thing.collision_component in self.collision_objects: self.collision_objects.remove(thing.collision_component)
			if thing.collision_component in self.nonstatic_objects: self.nonstatic_objects.remove(thing.collision_component)
			if thing.collision_component in self.coltree:			self.coltree.remove(thing.collision_component)

			if thing.renderable_component in self.draw_objects:		self.draw_objects.remove(thing.renderable_component)
			if thing.renderable_component in self.draw_priority:	self.draw_priority.remove(thing.renderable_component)
			if thing.renderable_component in self.draw_tree:		self.draw_tree.remove(thing.renderable_component)
			
			if thing in self.listeners:								self.listeners.remove(thing)
			del thing
		
		for thing in self.entities:
			thing.basic_component.update(timestep)

		for thing in self.physics_objects:
			thing.update(timestep)

		for thing in self.draw_objects:
			self.draw_tree.remove(thing)
			thing.update(timestep)
			self.draw_tree.append(thing)
		
		for thing in self.collision_objects:
			self.coltree.remove(thing)
			thing.update(timestep)
			self.coltree.append(thing)

		# And now they're updated, we do collision detection.
		for obj in self.nonstatic_objects:
			set_of_collisions = self.coltree.collisions(obj)
			for col in set_of_collisions:
				if not obj.collides_with(col.owner): continue
				if not col.collides_with(obj.owner): continue
				vector = shapes.intersect(obj, col)
				if vector is not None:
					obj.collide(col)
					col.collide(obj)
					po = obj.physics_component
					co = col.physics_component
					if po is not None and po.tangible and co is not None and co.tangible:
						if not po.immobile: bounce(po, co, vector)
						if not co.immobile: bounce(co, po, -vector)
		

	def on_key_press(self, symbol, modifiers):
		if symbol == key.P: 
			self.pwin.thescreen = PauseScreen(self.pwin, self)
		if symbol == key.R: 
			print(self.coltree.status_report())
			print(self.draw_tree.status_report())
			print(opengl.gl_info.get_version())
		if symbol == key.D: 
			self.draw_debug = not self.draw_debug
		for thing in self.listeners: thing.on_key_press(symbol, modifiers)
	def on_key_release(self, symbol, modifiers):
		for thing in self.listeners: thing.on_key_release(symbol, modifiers)
	def on_mouse_press(self, x, y, button, modifiers):
		for thing in self.listeners: thing.on_mouse_press(x, y, button, modifiers)
	def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
		for thing in self.listeners: thing.on_mouse_drag(x, y, dx, dy, button, modifiers)
	def on_mouse_motion(self, x, y, dx, dy):
		for thing in self.listeners: thing.on_mouse_motion(x, y, dx, dy)

class PauseScreen(object): 
	""" A game screen thingy for when the game is paused. """
	def __init__(self, pwin, childscreen):
		self.pwin = pwin
		self.childscreen = childscreen # The screen which paused us. pressing P will return us to this screen.

		self.prepared_to_exit = False
		self.pausetime = 0

		self.top_text = "THE GAME! IT'S PAUSED!\nPress 'p' to unpause.\nKills: {0}"
		self.bottom_text = "Don't forget: \nz to fire bullets! \nx to fire lasers! \nc to fire bombs! \narrows to move! \nesc to exit! \n\nd to activate debug drawing!"

		self.top_text_label = text.Label(
				self.top_text.format(self.childscreen.killcount), \
				'Arial', 24, color = (0, 0, 0, 200),\
				x = self.pwin.width/2, y = self.pwin.height/2 ,\
				anchor_x="center", anchor_y="center", \
				width=3*self.pwin.width/4, height=3*self.pwin.height/4, \
				multiline=1 \
			)
		self.bottom_text_label = text.Label( \
				self.bottom_text, \
				'Arial', 24, color = (0, 0, 0, 200), \
				x = self.pwin.width/2, y = self.pwin.height/4, \
				anchor_x="center", anchor_y="center", \
				width=3*self.pwin.width/4, height=3*self.pwin.height/4, \
				multiline=1 \
			)
	def update(self, timestep): self.pausetime += timestep
	def draw(self):
		self.childscreen.draw()
		self.top_text_label.draw()
		self.bottom_text_label.draw()
	# Listeners.
	def on_key_press(self, symbol, modifiers):
		if symbol == key.P: 
			if self.pausetime > 1:
				self.prepared_to_exit = True
	def on_key_release(self, symbol, modifiers):
		if symbol == key.P: 
			if self.prepared_to_exit:
				self.pwin.thescreen = self.childscreen
				del self
	def on_mouse_press(self, x, y, button, modifiers):pass
	def on_mouse_drag(self, x, y, dx, dy, button, modifiers):pass
	def on_mouse_motion(self, x, y, dx, dy):pass

