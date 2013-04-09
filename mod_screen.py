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

import procedural

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
		self.camera_rect = ((0,1),(0,1)) # (xmin, xmax), (ymin, ymax)

		opengl.glMatrixMode(opengl.GL_PROJECTION)
		opengl.glEnable(opengl.GL_BLEND)
		opengl.glBlendFunc(opengl.GL_SRC_ALPHA,opengl.GL_ONE)
		opengl.glLineWidth(2.0)

		opengl.glEnable(opengl.GL_LINE_SMOOTH)
		opengl.glHint(opengl.GL_LINE_SMOOTH_HINT,opengl.GL_NICEST)
		opengl.glEnable(opengl.GL_POINT_SMOOTH)
		opengl.glHint(opengl.GL_POINT_SMOOTH_HINT,opengl.GL_NICEST)
#		opengl.glEnable(opengl.GL_POLYGON_SMOOTH)
#		opengl.glHint(opengl.GL_POLYGON_SMOOTH_HINT,opengl.GL_NICEST)
		
		#Activate the depth buffer.
		opengl.glEnable(opengl.GL_DEPTH_TEST)
		#opengl.glDepthFunc(opengl.GL_LEQUAL)
		#opengl.glDepthRange(0.0, 1.0) #For some reason the z-buffer wasn't working until I threw this in.

		#Lighting!
		#opengl.glEnable(opengl.GL_LIGHTING)
		#opengl.glEnable(opengl.GL_LIGHT0)
		#opengl.glLightf(opengl.GL_LIGHT0, opengl.GL_LINEAR_ATTENUATION, 0.05)

		###########
		# Now, since this screen represents gameplay, we're going to initialize all the elements of the game we're playing.
		# For now, this is just a pile of stuff.
		###########
		
		# Set up all the different lists of objects in the world. These roughly correspond to managers! Sort of.
		self.coltree = collision_structures.SpatialGrid()
		#self.coltree = collision_structures.MultistoreSpatialGrid()
		
		self.physics_objects = []
		self.collision_objects = []
		self.static_objects = []
		self.nonstatic_objects = []
		self.priority = []
		self.nonpriority = []
		self.listeners = []

		self.components = []

		# and now, the things!

		playerobj = self.batch_addcomponent( PlayerBall(self, location = v(0,0)), listeners=True)
		self.batch_addcomponent( CameraFollower(self, latch=playerobj, spring=50, damping=10), collisions=False, priority=True) # Doesn't need collisions.

		self.batch_addcomponent( FreeBall(self, location = v(0,-50)) )
		self.batch_addcomponent( FreeBall(self, location = v(-100,0)) )
		self.batch_addcomponent( FreeBall(self, location = v(100,0)) )
		self.batch_addcomponent( FreeBall(self, location = v(0, 1700), rad=80) )

		self.batch_addcomponent( Spawner(self, location = v(-500, 1500), rad=250), static=True )
		self.batch_addcomponent( Spawner(self, location = v(500, 1500), rad=250), static=True )

		self.batch_addcomponent( EnemyBall(self, location = v(-200,30), rad=30) )
		self.batch_addcomponent( EnemyBall(self, location = v(-260,0), rad=30) )
		self.batch_addcomponent( EnemyBall(self, location = v(-100,60), rad=30) )

		#self.batch_addcomponent( ObstacleBall(self, location = v(-120,-200), rad=50) )
		#self.batch_addcomponent( ObstacleBall(self, location = v(60,-300), rad=30) )
		#self.batch_addcomponent( ObstacleBall(self, location = v(0,-800), rad=200) )
		#self.batch_addcomponent( ObstacleBall(self, location = v(-300,-500), rad=100) )
		#self.batch_addcomponent( ObstacleBall(self, location = v(200,300), rad=40) )
		for i in range(100):
			position = v(random.uniform(-1,1)*4000, random.uniform(-1,1)*1000)
			self.batch_addcomponent( ObstacleBall(self, location = position, rad=40), static=True, invisible=False)

		wavelength = 600
		depth = 150
		h = -1000
		for i in range(-10, 10):
			self.batch_addcomponent( ObstacleLine(self, location=v(i*wavelength, h), endpoint=v((i+0.5)*wavelength, h+depth), thick=20), static=True )
			self.batch_addcomponent( ObstacleLine(self, location=v((i+0.5)*wavelength, h+depth), endpoint=v((i+1)*wavelength, h), thick=20), static=True )

		# The scoop.
		#self.batch_addcomponent( ObstacleLine(self, location=v(2000, 0), endpoint=v(500, -1500), thick=20), static=True )
		#self.batch_addcomponent( ObstacleLine(self, location=v(-2000, 0), endpoint=v(-500, -1500), thick=20), static=True )
		#self.batch_addcomponent( ObstacleLine(self, location=v(-1000, -1500), endpoint=v(1000, -1500), thick=20), static=True )

		# The A-frame roof.
		#self.batch_addcomponent( ObstacleLine(self, location=v(0, 1500), endpoint=v(-1000, -150),thick = 20), static=True )
		#self.batch_addcomponent( ObstacleLine(self, location=v(0, 1500), endpoint=v(1000, -150),thick = 20), static=True )


		#self.batch_addcomponent( InvertBall(self, location = v(0,1000), rad=2600), static=True )

		self.batch_addcomponent( procedural.Background(self), static=True, collisions=False, priority=True )

		###########
		# And now the list of components is done.
		###########

		self.coltree.extend(self.collision_objects)

		self.constants = {'drag':10, 'gravity':v(0,-5000), 'elasticity':0.7, 'friction':0.9, 'displace':0.3}

	def batch_addcomponent(self, thing, physics=True, collisions=None, static=None, priority=False, listeners=False, invisible=False):
		"""Add a number of components to the lists of objects with various qualities, but do not yet add them to the collision structure.

		This method is supposed to be used to add a large number of objects at once - and then followed up by a call that adds
		  the appropriate objects into the coltree. The various keyword arguments have meanings:
		physics: if True, then the object is presumed to have physics behavior.
		collisions: if True, then the object should be tested for collisions. If physics is True, then this defaults to True.
		static: if True, the object never moves, and so doesn't need to be tested for collisions with other static objects.
		priority: if True, the object will be drawn before others. if False, they will be ordered by z-value (if they have one)
		listeners: if True, the object will receive keyboard and mouse events.
		"""
		if collisions is None: collisions = physics
		if static is None: static = not physics
		try:
			self.components.append(thing)
			if physics: self.physics_objects.append(thing)
			if collisions: 
				self.collision_objects.append(thing)
				if static: self.static_objects.append(thing)
				else: self.nonstatic_objects.append(thing)
			if not invisible:
				if priority: self.priority.append(thing) # Objects which have priority drawing (these are drawn first).
				else:
					self.nonpriority.append(thing)	# Objects which do not have priority drawing.
					self.nonpriority.sort(key = lambda t: t.z if hasattr(t,"z") else 0)
			if listeners: self.listeners.append(thing)
		except AttributeError as e: print("There was some kind of problem building the list of objects in the world. \n{}".format(e))
		finally: return thing

	def addcomponent(self, thing, *args, **kwargs):
		self.batch_addcomponent(thing, *args, **kwargs)
		if thing in self.collision_objects: self.coltree.append(thing)
		return thing

	def killcountincrease(self): # increment the kill count!
		self.killcount = self.killcount + 1

	def draw(self):
		""" Instructs each component to draw itself, starting with the components in the priority set. """
		# Clear the screen. The background is white. Also clear the buffers.
		opengl.glClearColor(1.0,1.0,1.0,0.0)
#		opengl.glClear(opengl.GL_COLOR_BUFFER_BIT | opengl.GL_DEPTH_BUFFER_BIT)

		# TODO: Speed this up by not drawing things outside the window.
		for thing in self.priority:
			opengl.glColor3f(0.0,0.0,0.0)
			if self.draw_debug and hasattr(thing, 'draw_debug'): thing.draw_debug()
			thing.draw()
		for thing in sorted(self.coltree.collisions_with_rect(self.camera_rect), key=lambda j: j.pos.x):
		#for thing in self.nonpriority:
			opengl.glColor3f(0.0,0.0,0.0)
			if self.draw_debug and hasattr(thing, 'draw_debug'): thing.draw_debug()
			thing.draw()
		g = (t for t in self.nonpriority if t not in self.coltree)
		for b in g: 
			opengl.glColor3f(0.0,0.0,0.0)
			if self.draw_debug and hasattr(b, 'draw_debug'): b.draw_debug()
			b.draw()
		if self.draw_debug and hasattr(self.coltree,'draw'): self.coltree.draw()

	def update(self, timestep):
		"""Update the state of each component in the game world."""
		self.total_time += timestep

		dead_things = (t for t in self.components if t.dead)

		for thing in dead_things:
			self.components.remove(thing)
			if thing in self.physics_objects: 	self.physics_objects.remove(thing)
			if thing in self.collision_objects: self.collision_objects.remove(thing)
			if thing in self.static_objects: 	self.static_objects.remove(thing)
			if thing in self.nonstatic_objects: self.nonstatic_objects.remove(thing)
			if thing in self.priority: 			self.priority.remove(thing)
			if thing in self.nonpriority: 		self.nonpriority.remove(thing)
			self.coltree.remove(thing)
			del thing

		for thing in self.components: thing.update(timestep)

		# And now they're updated, we do collision detection.
		for obj in self.nonstatic_objects:
			set_of_collisions = self.coltree.collisions(obj) 
			for col in set_of_collisions:
				if hasattr(obj, 'test_for_collision') and not obj.test_for_collision:
					continue
				if hasattr(col, 'test_for_collision') and not col.test_for_collision:
					continue
				if shapes.intersect(obj, col):
					if hasattr(obj, 'collides_with') and not obj.collides_with(col):
						continue
					if hasattr(col, 'collides_with') and not col.collides_with(obj):
						continue
					obj.collide(col)
					col.collide(obj)
		# Done checking for/reacting to collisions!

	def on_key_press(self, symbol, modifiers):
		if symbol == key.P: self.pwin.thescreen = PauseScreen(self.pwin, self)
		if symbol == key.R: print(self.coltree.status_rep(''))
		if symbol == key.D: self.draw_debug = not self.draw_debug
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
				'Arial', 24, \
				color = (0, 0, 0, 200),\
				x = self.pwin.width/2, y = self.pwin.height/2 ,\
				anchor_x="center", anchor_y="center", \
				width=3*self.pwin.width/4, height=3*self.pwin.height/4, \
				multiline=1 \
			)
		self.bottom_text_label = text.Label( \
				self.bottom_text, \
				'Arial', 24, \
				color = (0, 0, 0, 200), \
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

#############################
### DONE WITH THE SCREENS ###
#############################

################################################
### Things which are reused by many objects. ###
def initialize_habitats(self, pscreen):
	""" Initialize the habitat of this object."""
	self.pscreen = pscreen
def initialize_states(self, dead=False, tangible=True, immobile=False, test_for_collision=True):
	""" Initialize state variables.
	dead - if the 'dead' flag is set, then it will be removed next chance we get.
	tangible - if the 'tangible' value is truthy, it will physics-collide with other objects.
		not yet implemented: if tangible matches another object, we can collide with that object.
	immobile - if the 'immobile' flag is set, then the object cannot be moved.
	test_for_collision - if true, then this object should be tested for whether it collides.
	"""
	# TODO: These duplicate the functionality of the tests in addcomponent. Compact this down for the component system.
	self.dead = dead
	self.tangible = tangible
	self.immobile = immobile
	self.test_for_collision = test_for_collision
def initialize_attributes(self, pos=v(0,0), vel=v(0,0), acc=v(0,0), r=20, shape=None, **kwargs):
	""" Initialize various attributes of the physics-ness of the object.

	This is like initializing a RigidBody component.
	pos - starting location, obviously.
	vel - starting velocity.
	acc - starting acceleration. Don't have mass yet. When we have mass, this'll be starting force.
	r - radius scale of the object.
	shape - a shape, if you want a non-circle one.
	"""
	self.pos = pos
	self.vel = vel
	self.acc = acc

	self.rad = r
	
	if shape is None: self.shape = shapes.Circle(rad=self.rad, invert=0, **kwargs)
	else: self.shape = shape
def phys_collide(self,other):
	""" Basic response to collisions. If they're immobile, move us out.	"""
	if not other.tangible: return
	vector = shapes.intersect(self, other) # Returns the shortest vector by which to move 'self' to no longer be intersecting 'other'.
	if vector is None: return None
	else:
		velocity_perpendicular = self.vel.proj(vector) # The component of self.vel which is parallel or anti-parallel to 'vector'.
		velocity_parallel = self.vel - velocity_perpendicular
		if vector*self.vel > 0: 
			# We are already moving in the direction to escape.
			self.vel = self.pscreen.constants['friction']*velocity_parallel + self.pscreen.constants['elasticity']*velocity_perpendicular
		else:
			# We are moving to be deeper into the object. We should reverse the perpendicular component of our velocity.
			self.vel = self.pscreen.constants['friction']*velocity_parallel - self.pscreen.constants['elasticity']*velocity_perpendicular
		self.pos += self.pscreen.constants['displace'] * vector
	if other.immobile:
		self.pos += vector
	if self.pscreen.draw_debug:
		opengl.glBegin(opengl.GL_LINES)
		opengl.glVertex3f(self.pos.x, self.pos.y, 30.0)
		opengl.glVertex3f(self.pos.x + vector.x, self.pos.y + vector.y, 30.0)
		opengl.glEnd()
def update_world(self,timestep):
	""" The part of the update cycle where the various effects of the world act. """
	self.acc = self.acc + timestep*self.pscreen.constants['gravity']
	self.acc = self.acc - timestep*self.pscreen.constants['drag']*self.vel
def update_inertia(self,timestep):
	""" Update position and velocity in the standard way. """
	self.pscreen.coltree.remove(self) 
	self.vel = self.vel + timestep*self.acc
	self.pos = self.pos + timestep*self.vel
	self.acc = v(0,0)
	self.pscreen.coltree.append(self)

#############################################
### The objects which populate the level! ###
#############################################

class FreeBall(object):
	""" A circular object that can move and bounce freely. It's a circle! Woo."""
	def __init__(self, pscreen, location=v(0,0), rad=20, *args, **kwargs):
		initialize_habitats(self,pscreen)
		initialize_states(self)
		initialize_attributes(self, pos=location, vel=v(0,0), acc=v(0,0), r=rad)
		self.shape.drawtype = "3d"
	def collide(self,other): phys_collide(self,other)
	def update(self,timestep):
		update_world(self,timestep)
		update_inertia(self,timestep)
	def draw(self): self.shape.draw(self.pos)
class ObstacleBall(object):
	""" A ball fixed in space. """
	def __init__(self, pscreen, location=v(0,0), rad=20, *args, **kwargs):
		initialize_habitats(self,pscreen)
		initialize_states(self, immobile=True)
		initialize_attributes(self, pos=location, vel=v(0,0), acc=(0,0), r=rad)
		self.shape.drawtype="3d"
	def collide(self,other): pass
	def update(self, timestep): pass
	def draw(self): self.shape.draw(self.pos)
class ObstacleLine(object):
	""" A line, potentially with rounded ends, fixed in space. """
	def __init__(self, pscreen, location=v(0,0), endpoint=v(0,1), thick = 0,*args, **kwargs):
		initialize_habitats(self,pscreen)
		initialize_states(self, immobile=True)
		initialize_attributes(self, pos=location, vel=v(0,0), acc=(0,0))
		self.start = self.pos
		self.end = endpoint
		self.shape = shapes.Line(endpoint - self.pos, thickness = thick)
	def collide(self,other): pass
	def update(self, timestep): pass
	def draw(self): self.shape.draw(self.pos)
class InvertBall(object):
	""" An inverted circle, suitable for use as the boundary of a level. """
	def __init__(self, pscreen, location=v(0,0), rad=20, *args, **kwargs):
		initialize_habitats(self,pscreen)
		initialize_states(self, immobile=True)
		initialize_attributes(self, pos=location, vel=v(0,0), acc=(0,0), r=rad)
		self.shape.invert = True
	def collide(self,other): pass
	def update(self, timestep): pass
	def draw(self): self.shape.draw(self.pos)

###################
### Opponents!? ###
###################

class Spawner(object):
	""" A circular area that spawns EnemyBalls until it reaches the max, with chance spawn_chance every frame. """
	def __init__(self, pscreen, location=v(0,0), rad=100, z=0.25, *args, **kwargs):
		initialize_habitats(self,pscreen)
		initialize_states(self, tangible=False, immobile=True)#, test_for_collision=False)
		initialize_attributes(self, pos=location, vel=v(0,0), acc=v(0,0), r=rad)
		self.z = z
		self.shape.drawtype = "fill"

		self.spawn_count = 0
		self.spawn_count_max = 20 # Maximum number that will spawn before the spawner dies.
		self.spawn_chance = 0.01 # chance of spawning, per frame.
		self.maxvelocity = 1000
	def collide(self,other): pass
	def update(self, timestep):
		if self.spawn_count > self.spawn_count_max: return
		if random.random() < self.spawn_chance:
			r = random.random()*self.rad
			angle = random.random()*2*math.pi
			position = self.pos + v(r*math.cos(angle), r*math.sin(angle))
			newball = EnemyBall(self.pscreen, location=position, rad=30)
			vel = random.random()*self.maxvelocity
			angle = random.random()*2*math.pi
			newball.vel = v( vel*math.cos(angle), vel*math.sin(angle) )

			self.pscreen.addcomponent(newball)

			self.spawn_count = self.spawn_count + 1
	def draw(self): 
		opengl.glColor4f(0.6,0.0,0.6,0.4)
		self.shape.draw(self.pos, self.z)
class EnemyBall(object):
	""" An enemy ball, which can be destroyed by bullets. """
	def __init__(self, pscreen, location=v(0,0), rad=30, *args, **kwargs):
		initialize_habitats(self,pscreen)
		initialize_states(self)
		initialize_attributes(self, pos=location, vel=v(0,0), acc=v(0,0), r=rad)
		self.shape.drawtype = "fill"
		self.enemy = True
	def collide(self,other):
		if hasattr(other,"bullet") and other.bullet: self.dead = True
		phys_collide(self,other)
	def update(self,timestep):
		update_world(self,timestep)
		update_inertia(self,timestep)
	def draw(self):
		opengl.glColor3f(0.5,0.5,0.5)
		self.shape.draw(self.pos)

################################
### Player-related stuff!    ###
### Player, Bullets, Camera. ###
################################

class PlayerBall(object):
	""" The player. Oh my, but this is a big class. Oh well. It's an important object. """
	def __init__(self,pscreen, location=v(0,0), *args, **kwargs):
		initialize_habitats(self,pscreen)
		initialize_states(self)
		initialize_attributes(self, pos=location, vel=v(0,0), acc=v(0,0), r=15)
		self.z=0

		self.thrust = 7500
		self.thrustdir = v(0,0)
		self.player = True

		self.shape2 = shapes.Circle(10, rad=self.rad/4, drawtype="fill", invert=0)

	def fire_bullet(self):
		newbullet = BulletBall(self.pscreen, self, location=self.pos)
		if abs(self.vel) == 0: newbullet.vel = v(0, 800)
		else: newbullet.vel = self.vel + 800*self.vel.unit()
		self.pscreen.addcomponent(newbullet)

	def fire_bomb(self):
		newbomb = BombBall(self.pscreen, self, location=self.pos)
		if abs(self.vel) == 0: newbomb.vel = v(0, 200)
		else: newbomb.vel = self.vel + 200*self.vel.unit()
		self.pscreen.addcomponent(newbomb)

	def fire_laser(self):
		if abs(self.vel) == 0: direct = v(0,1000)
		else: direct = 1000*self.vel.unit()
		newlaser = LaserLine(self.pscreen, self, location=self.pos, direction=direct)
		self.pscreen.addcomponent(newlaser, static=True)

	def gotkill(self, other): self.pscreen.killcountincrease()
	def collide(self,other): phys_collide(self,other)
	def update(self,timestep):
		self.acc = self.acc + self.thrust*timestep*self.thrustdir
		update_world(self,timestep)
		update_inertia(self,timestep)
	def draw(self):
		#opengl.glLightfv(opengl.GL_LIGHT0, opengl.GL_POSITION, (opengl.GLfloat * 4)(*(self.pos.x, self.pos.y, 0.0, 1.0)))
		opengl.glColor3f(0.0,0.6,0.0)
		self.shape.draw(self.pos)
		opengl.glColor3f(0.0,0.0,1.0)
		self.shape2.draw(self.pos + self.vel.unit()*(self.shape.rad - self.shape2.rad/2))
	def on_key_press(self, symbol, modifiers):
		if symbol == key.UP: self.thrustdir = self.thrustdir + v(0,2)
		if symbol == key.DOWN: self.thrustdir = self.thrustdir + v(0,-1)
		if symbol == key.LEFT: self.thrustdir = self.thrustdir + v(-1,0)
		if symbol == key.RIGHT: self.thrustdir = self.thrustdir + v(1,0)
		if symbol == key.Z: self.fire_bullet()
		if symbol == key.X: self.fire_laser()
		if symbol == key.C: self.fire_bomb()
	def on_key_release(self, symbol, modifiers):
		if symbol == key.UP: self.thrustdir = self.thrustdir - v(0,2)
		if symbol == key.DOWN: self.thrustdir = self.thrustdir - v(0,-1)
		if symbol == key.LEFT: self.thrustdir = self.thrustdir - v(-1,0)
		if symbol == key.RIGHT: self.thrustdir = self.thrustdir - v(1,0)
	def on_mouse_press(self, x, y, button, modifiers): pass
	def on_mouse_drag(self, x, y, dx, dy, button, modifiers): pass
	def on_mouse_motion(self, x, y, dx, dy): pass
class BulletBall(object):
	""" A projectile object. It's a circle! Woo."""
	def __init__(self, pscreen, parent,location=v(0,0), *args, **kwargs):
		initialize_habitats(self,pscreen)
		initialize_states(self)
		initialize_attributes(self, pos=location, vel=v(0,0), acc=v(0,0), r=5)
		self.parent = parent
		self.bullet = True
		self.time_to_live = 4
		self.time=0
	def collide(self,other):
		if hasattr(other,"enemy") and other.enemy:
			self.dead = True
			self.parent.gotkill(other)
			return
		phys_collide(self,other)
	def collides_with(self, other): return other is not self.parent
	def update(self,timestep):
		self.time += timestep
		if self.time>self.time_to_live:
			self.dead = True
		update_world(self,timestep)
		update_inertia(self,timestep)
	def draw(self):
		opengl.glColor3f(1.0,0.2,0.5)
		self.shape.draw(self.pos)
class LaserLine(object):
	""" A laser beam! """
	def __init__(self, pscreen, parent,location=v(0,0), direction=v(0,1000), *args, **kwargs):
		initialize_habitats(self,pscreen)
		initialize_states(self, tangible=False)
		initialize_attributes(self, pos=location, vel=v(0,0), acc=v(0,0))
		self.parent = parent
		self.bullet = True
		self.time_to_live = 0.5
		self.time=0
		self.shape=shapes.Line(direction)
	def collide(self,other):
		if hasattr(other,"enemy") and other.enemy:
			self.dead = True
			self.parent.gotkill(other)
	def collides_with(self, other): return other is not self.parent
	def update(self,timestep):
		self.time += timestep
		if self.time>self.time_to_live:
			self.dead = True
	def draw(self):
		opengl.glColor3f(0.0,0.0,1.0-(self.time/self.time_to_live))
		self.shape.draw(self.pos)
class BombBall(object):
	""" A bomb, which explodes after a certain amount of time to throw things flying. """
	def __init__(self, pscreen, parent, location=None):
		initialize_habitats(self, pscreen)
		initialize_states(self)
		initialize_attributes(self, pos=location, vel=v(0,0), acc=v(0,0), r=8)
		self.parent = parent
		self.time_to_live=2
		self.time=0
	def collide(self, other): phys_collide(self,other)
	def collides_with(self, other): return other is not self.parent
	def update(self,timestep):
		self.time += timestep
		if self.time > self.time_to_live: 
			self.pscreen.addcomponent( BombExplosion(self.pscreen, self, location=self.pos), static=True )
			self.dead = True
		update_world(self,timestep)
		update_inertia(self,timestep)
	def draw(self):
		# Color goes from black to red as it approaches exploding.
		opengl.glColor3f((self.time/self.time_to_live), 0.0, 0.0)
		self.shape.draw(self.pos)
class BombExplosion(object):
	""" The explosion for the bomb. This is a non-tangible object which needs to collide with things. """
	def __init__(self, pscreen, parent, location=None):
		initialize_habitats(self, pscreen)
		initialize_states(self, tangible=False, immobile=True)
		initialize_attributes(self, pos=location, vel=v(0,0), acc=v(0,0), r=100)
		self.shape.drawtype = "fill"

		self.parent = parent
		self.time_to_live=0.5
		self.time=0
	def collide(self, other): other.acc = 100*(1-self.time/self.time_to_live)*(other.pos - self.pos)
	def update(self, timestep):
		self.time += timestep
		if self.time > self.time_to_live:
			self.dead = True
	def draw(self):
		opengl.glColor4f(1.0-self.time/self.time_to_live, 0*self.time/self.time_to_live, 0*self.time/self.time_to_live, 1.0-self.time/self.time_to_live)
		self.shape.draw(self.pos)

class CameraFollower(object):
	""" This object follows the latch and defines the drawing frustrum and basically sets up cameras. """
	def __init__(self, pscreen, latch=None, spring=30, damping=2):
		initialize_habitats(self,pscreen)
		initialize_states(self, dead=False, tangible=False, immobile=False)
		self.z = -10

		self.template_text = "FPS: {0:.2f}\n# of Objects: {1}\n# of Non-Static: {2}"
		l_x, l_y = 3*self.pscreen.pwin.width/4.0, 1*self.pscreen.pwin.height/4.0
		l_w, l_h = self.pscreen.pwin.width/4.0, self.pscreen.pwin.height/8.0
		self.hud_label = text.Label(
				self.template_text.format(0, 0, 0), 
				font_name='Arial', font_size=12, color=(0,0,0,255), 
				x=l_x, y=l_y, width=l_w, height=l_h, 
				anchor_x="center", anchor_y="center", multiline = 1 )
		self.hud_background = pyglet.graphics.vertex_list(4, 'v3f', 'c3f')
		self.hud_background.vertices = (l_x-l_w/2, l_y-l_h/2, -1, l_x+l_w/2, l_y-l_h/2, -1, l_x+l_w/2, l_y+l_h/2, -1, l_x-l_w/2, l_y+l_h/2, -1)
		self.hud_background.colors = (1, 1, 1)*4

		self.target = latch
		self.spring = spring
		self.damping = damping

		self.scale = 0.5
		self.decay = 0.4

		self.time = 0

		self.pos = self.target.pos
		self.vel = self.target.vel
		self.acc = v(0,0)
	def update(self,timestep):
		# The reason this doesn't call update_inertia is that that also deals with the collision tree.
		self.acc = self.acc + self.spring*(self.target.pos-self.pos)
		self.acc = self.acc - self.damping*self.vel
		self.vel = self.vel + timestep*self.acc
		self.pos = self.pos + timestep*self.vel
		self.acc = v(0,0)

		targvel = abs(self.target.vel)/1000
		scalefactor = 1 + 2/(1+math.exp(-targvel))
		self.scale = self.decay*self.scale + (1-self.decay)/scalefactor
		self.time = self.time + timestep
		
		self.hud_label.text = self.template_text.format(self.pscreen.pwin.avefps, len(self.pscreen.coltree), len(self.pscreen.nonstatic_objects))

	def draw(self):

		opengl.glMatrixMode(opengl.GL_PROJECTION)
		opengl.glLoadIdentity()
		
		#z = 1000.0 + 500/self.scale
		z=600
		clipping_plane_z_coordinates = (-400.0,500.0)

		dist_to_near_plane = min(z-clipping_plane_z_coordinates[0], z-clipping_plane_z_coordinates[1])
		dist_to_near_plane = max(dist_to_near_plane, 0.1) # Ensure that it's not negative.
		dist_to_far_plane = max(z-clipping_plane_z_coordinates[0], z-clipping_plane_z_coordinates[1])

		width = 1000.0
		height = width*self.pscreen.pwin.height/self.pscreen.pwin.width
#		width, height = 1000.0, 1000.0 # Width and height of the viewport at the xy plane.
		left_at_near_plane, right_at_near_plane = -(dist_to_near_plane/z)*width/2, (dist_to_near_plane/z)*width/2
		bottom_at_near_plane, top_at_near_plane = -(dist_to_near_plane/z)*height/2, (dist_to_near_plane/z)*height/2
		
		opengl.glFrustum(left_at_near_plane, right_at_near_plane, bottom_at_near_plane, top_at_near_plane, dist_to_near_plane, dist_to_far_plane)
		opengl.glTranslatef( -self.pos.x, -self.pos.y, -z )

		# This line tells the parent screen what rect should be drawn. Format is ((x minimum, x maximum), (y minimum, y maximum))
		self.pscreen.camera_rect = ((self.pos.x - width/2.0, self.pos.x + width/2.0),(self.pos.y - height/2.0,self.pos.y + height/2.0)) # TODO: make this better.

		opengl.glMatrixMode(opengl.GL_MODELVIEW)

		opengl.glMatrixMode(opengl.GL_PROJECTION) # Edit the projection matrix.
		opengl.glPushMatrix() # Push onto the stack, so that we can recover after.
		opengl.glLoadIdentity() # Load a blank matrix.
		opengl.glOrtho(0,self.pscreen.pwin.width, 0,self.pscreen.pwin.height, -1, 200) # Multiply by an orthogonal projection.
		
		self.hud_background.draw(opengl.GL_QUADS)
		self.hud_label.draw()

		opengl.glPopMatrix() # Recover the old projection matrix.
		opengl.glMatrixMode(opengl.GL_MODELVIEW) # Return to the former matrix mode.


