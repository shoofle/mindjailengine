#!/usr/bin/env python

import pyglet
from pyglet import window, text, gl, graphics
from pyglet.window import key

import random
import math

import shapes
from vectors import v

import quadtree

SPAWNCHANCE = 0.01
MAXSIZE = 200

def intersecttest(a, b):
	if a.tangible == 0 or b.tangible == 0:
		return False
	return shapes.intersect(a, b)
quadtree.intersects = intersecttest
quadtree.sortsearchsolution.intersects = intersecttest

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

		pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
		pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA,pyglet.gl.GL_ONE)
		pyglet.gl.glLineWidth(2.0)
		pyglet.gl.glEnable(pyglet.gl.GL_LINE_SMOOTH)
		pyglet.gl.glEnable(pyglet.gl.GL_POINT_SMOOTH)
		#pyglet.gl.glHint(pyglet.gl.GL_POINT_SMOOTH_HINT,pyglet.gl.GL_NICEST)
		#pyglet.gl.glHint(pyglet.gl.GL_POLYGON_SMOOTH_HINT,pyglet.gl.GL_NICEST)
		#pyglet.gl.glLineWidth(19.0)
		###########
		# Now, since this screen represents gameplay, we're going to initialize all the elements of the game we're playing.
		# For now, this is just a pile of stuff.
		###########

		self.killcount = 0
		
		self.coltree = quadtree.QuadTree(items=[], center=v(0,0), height=8)
		self.components = []

		# and now, the things!

		playerobj = self.batch_addcomponent( PlayerBall(self, location = v(0,0)), 0,0,1)
		self.batch_addcomponent( CameraFollower(self, latch=playerobj, spring=50, damping=10), -1,0,0)

		self.batch_addcomponent( FreeBall(self, location = v(0,-50)), 0,0,0)
		self.batch_addcomponent( FreeBall(self, location = v(-100,0)), 0,0,0)
		self.batch_addcomponent( FreeBall(self, location = v(100,0)), 0,0,0)

		self.batch_addcomponent( Spawner(self, location = v(-500, 1500), rad=250), -1,0,0)
		self.batch_addcomponent( Spawner(self, location = v(500, 1500), rad=250), -1,0,0)

		self.batch_addcomponent( EnemyBall(self, location = v(-200,30), rad=30), 0,0,0)
		self.batch_addcomponent( EnemyBall(self, location = v(-260,0), rad=30), 0,0,0)
		self.batch_addcomponent( EnemyBall(self, location = v(-100,60), rad=30), 0,0,0)

		self.batch_addcomponent( ObstacleBall(self, location = v(-120,-200), rad=50), 0,0,0)
		self.batch_addcomponent( ObstacleBall(self, location = v(60,-300), rad=30), 0,0,0)
		self.batch_addcomponent( ObstacleBall(self, location = v(0,-800), rad=200), 0,0,0)
		self.batch_addcomponent( ObstacleBall(self, location = v(-300,-500), rad=100), 0,0,0)
		self.batch_addcomponent( ObstacleBall(self, location = v(200,300), rad=40), 0,0,0)

		self.batch_addcomponent( ObstacleLine(self, location = v(2000, 0), endpoint=v(500, -1500), thick=20), 1,0,0)
		self.batch_addcomponent( ObstacleLine(self, location = v(-2000, 0), endpoint=v(-500, -1500), thick=20), 1,0,0)

		self.batch_addcomponent( ObstacleLine(self, location = v(0, 1500), endpoint=v(-1000, -150),thick = 20), 1,0,0)
		self.batch_addcomponent( ObstacleLine(self, location = v(0, 1500), endpoint=v(1000, -150),thick = 20), 1,0,0)

		self.batch_addcomponent( InvertBall(self, location = v(0,500), rad=2000), 1,0,0)

		###########
		# And now the list of components is done.
		###########

		self.coltree.extend(self.nonstatics)
		self.coltree.extend(self.statics)

		self.constants = {'drag':10, 'gravity':5000, 'elasticity':0.7, 'friction':0.9, 'displace':0.3}

	############
	# thing = object to be added.
	# stationary = whether it is a stationary object which therefore should only check against nonstationary objects.
	# priority = whether it gets priority drawing privileges.
	def batch_addcomponent(self, thing, stationary, priority, listeners):
		self.components.append(thing)

		if stationary == -1:
			pass
		elif stationary == 0:
			try: self.nonstatics.append(thing)			# Non-static objects which test against each other.
			except AttributeError: self.nonstatics = [thing]
		else:
			try: self.statics.append(thing)				# Static ojects which don't need to test against each other.
			except AttributeError: self.statics = [thing]
		if not priority == 0:
			try: self.priority.append(thing)			# Objects which have priority drawing (these are drawn first).
			except AttributeError: self.priority = [thing]
		else:
			try: self.nonpriority.append(thing)			# Objects which do not have priority drawing.
			except AttributeError: self.nonpriority = [thing]
			self.nonpriority.sort(key = lambda t: t.z if hasattr(t,"z") else 0)
		if not listeners == 0:
			try: self.listeners.append(thing)
			except AttributeError: self.listeners = [thing]
		return thing


	def addcomponent(self, thing, stationary, priority, listeners):
		self.coltree.append(thing)
		return self.batch_addcomponent(thing,stationary,priority,listeners)

	def killcountincrease(self): # increment the kill count!
		self.killcount = self.killcount + 1
	def pause(self):
		self.pwin.thescreen = PauseScreen(self.pwin, self)
	def draw(self):
		""" Instructs each component to draw itself, starting with the components in the priority set. """
		pyglet.gl.glClear(pyglet.gl.GL_COLOR_BUFFER_BIT | pyglet.gl.GL_DEPTH_BUFFER_BIT)
		#pyglet.gl.glEnable(pyglet.gl.GL_DEPTH_TEST)
		pyglet.gl.glClearColor(1.0,1.0,1.0,0.0)
		pyglet.gl.glPushMatrix()
		#for thing in self.priority:
		#	pyglet.gl.glColor3f(0.0,0.0,0.0)
		#	thing.draw()
		for thing in self.nonpriority:
			pyglet.gl.glColor3f(0.0,0.0,0.0)
			thing.draw()
		pyglet.gl.glPopMatrix()

	def update(self, timestep):
		""" Update each component. """
		for thing in self.components:
			if thing.dead:
				self.components.remove(thing)
				if thing in self.statics: self.statics.remove(thing)
				elif thing in self.nonstatics: self.nonstatics.remove(thing)
				#if thing in self.priority: self.priority.remove(thing)
				if thing in self.nonpriority: self.nonpriority.remove(thing)
				self.coltree.remove(thing)
				continue
			thing.update(timestep)


		# And now they're updated, we do collision detection.
		colset = set()

		### Statics-nonstatics detection.
		for obj in self.statics:
			colset = self.coltree.collisions(obj) or []
			for col in colset:
				obj.collide(col)
		for obj in self.nonstatics:
			colset = self.coltree.collisions(obj) or []
			for col in colset:
				obj.collide(col)
		#print self.coltree.statusrep("")
		# Done checking for/reacting to collisions!

	def on_key_press(self, symbol, modifiers):
		if symbol == key.P: # If they pressed p, we want to pause.
			self.pwin.thescreen = PauseScreen(self.pwin, self)
		for thing in self.listeners:
			thing.on_key_press(symbol, modifiers)
	def on_key_release(self, symbol, modifiers):
		for thing in self.listeners:
			thing.on_key_release(symbol, modifiers)
	def on_mouse_press(self, x, y, button, modifiers):
		for thing in self.listeners:
			thing.on_mouse_press(x, y, button, modifiers)
	def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
		for thing in self.listeners:
			thing.on_mouse_drag(x, y, dx, dy, button, modifiers)
	def on_mouse_motion(self, x, y, dx, dy):
		for thing in self.listeners:
			thing.on_mouse_motion(x, y, dx, dy)

#############################
### DONE WITH THE SCREENS ###
#############################
class Manager(object):
	"""Manages one aspect of the game world, and the behaviors of all the entities affected by that aspect/component.

	A manager will keep a list of the components which it owns - for example, the RigidBody manager has a list of 
	  RigidBodyComponents.
	# Manager.entities is a list of all the entities with the component in question.
	"""
	def __init__(self):
		self.component_list = []
	
	def update(self, time_step):
		"""Update the state of every component, having advanced time by time_step."""
		for component in self.component_list: 
			self.individual_update(component, time_step)
	
	def individual_update(self, component, time_step):
		"""Update logic for an individual component.

		If this were the Drawable Manager/Components, then this would update the animation and tell opengl to draw.
		"""
		pass

class Entity(object):
	"""An entity is a single object in the game world, and has various components attached to it which define its behavior.

	Might be empty. Might contain a list of components, for redundancy.
	"""
	def __init__(self):
		pass

class Component(object):
	"""A component describes some aspect of an entity. Each type of Component has an associated Manager.

	The Manager describes the behavior associated with the Component. For example, the RigidBodyComponent includes
	  information about the position of the object, shape, mass, and so on. The RigidBodyManager defines how momentum
	  changes these values every clock tick, and watches for collisions between objects.
	Components are attached to the Entity they describe, and should be able to access other Components, if they have them.
	Components may require the presence of other components in order to attach.
	"""
	def __init__(self, entity):
		self.entity = entity


class ShapeComponent(object):
	"""Shape data for an object."""
	def __init__(self, entity, *args, **kwargs):
				 



################################################
### Things which are reused by many objects. ###
def initialize_habitats(self, pscreen):
	""" Initialize the habitat of this object.
	"""
	self.pscreen = pscreen

def initialize_states(self, dead=False, tangible=1, immobile=0):
	""" Initialize the state variables: whether the object is 
	dead - if the 'dead' flag is set, then it will be removed next chance we get.
	tangible - if the 'tangible' value is nonzero and matches another object, then they can collide.
	immobile - if the 'immobile' flag is set, then the object cannot be moved.
	"""
	self.dead = dead
	self.tangible = tangible
	self.immobile = immobile
def initialize_attributes(self, pos=v(0,0), vel=v(0,0), acc=v(0,0), r=20, shape=None, numpoints=60, **kwargs):
	""" Initialize various attributes of the physics-ness of the object.
	x - starting location, obviously.
	v - starting velocity.
	f - starting acceleration. Don't have mass yet. When we have mass, this'll be starting force.
	r - radius scale of the object.
	shape - a shape, if you want a non-circle one.
	"""
	self.pos = pos
	self.vel = vel
	self.acc = acc

	self.rad = r
	
	if shape is None: self.shape = shapes.Circle(numpoints=numpoints, rad=self.rad, drawtype="lines", invert=0, **kwargs)
	else: self.shape = shape
def phys_collide(self,other):
	""" Standard collision response. Reflect our velocity along the collision line thing.
	If they're immobile, move us out.
	"""
	#comme = self.vel - com
	vector = other.pos - self.pos
	self.vel = self.vel + v(0,200)
	if vector == None: return None
	else:
		velperp = self.vel.proj(vector)
		velpar = self.vel - velperp
		if self.vel*vector > 0:
			self.vel = self.pscreen.constants['elasticity'] * velperp + self.pscreen.constants['friction'] * velpar
		else :
			self.vel = -self.pscreen.constants['elasticity'] * velperp + self.pscreen.constants['friction'] * velpar
		self.pos = self.pos + self.pscreen.constants['displace'] * vector
	if other.immobile == 1:
		self.pos = self.pos + vector
def update_world(self,timestep):
	""" The part of the update cycle where the various effects of the world act. """
	self.acc = self.acc + timestep*self.pscreen.constants['gravity']*(v(0,-1))
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
	""" A basic ball object. It's a circle! Woo."""
	def __init__(self, pscreen, location=v(0,0), *args, **kwargs):
		initialize_habitats(self,pscreen)
		initialize_states(self, dead=False, tangible=1, immobile=0)
		initialize_attributes(self, pos=location, vel=v(0,0), acc=v(0,0), r=20)
	def collide(self,other):
		phys_collide(self,other)
	def update(self,timestep):
		update_world(self,timestep)
		update_inertia(self,timestep)
	def draw(self):
		self.shape.draw(self.pos)
class ObstacleBall(object):
	def __init__(self, pscreen, location=v(0,0), rad=20, *args, **kwargs):
		initialize_habitats(self,pscreen)
		initialize_states(self, dead=False, tangible=1, immobile=1)
		initialize_attributes(self, pos=location, vel=v(0,0), acc=(0,0), r=rad)
	def update(self, timestep): pass
	def draw(self): self.shape.draw(self.pos)
	def collide(self,other): pass
class ObstacleLine(object):
	def __init__(self, pscreen, location=v(0,0), endpoint=v(0,1), thick = 0,*args, **kwargs):
		initialize_habitats(self,pscreen)
		initialize_states(self, dead=False, tangible=1, immobile=1)
		initialize_attributes(self, pos=location, vel=v(0,0), acc=(0,0))
		self.start = self.pos
		self.end = endpoint
		self.shape = shapes.Line(endpoint - self.pos, thickness = thick)
	def update(self, timestep): pass
	def draw(self): self.shape.draw(self.pos)
	def collide(self,other): pass
class InvertBall(object):
	def __init__(self, pscreen, location=v(0,0), rad=20, *args, **kwargs):
		initialize_habitats(self,pscreen)
		initialize_states(self, dead=False, tangible=1, immobile=1)
		initialize_attributes(self, pos=location, vel=v(0,0), acc=(0,0), r=rad)
		self.shape.invert = 1
	def update(self, timestep): pass
	def draw(self): self.shape.draw(self.pos)
	def collide(self,other): pass



###################
### Opponents!? ###
###################

class Spawner(object):
	def __init__(self, pscreen, location=v(0,0), rad=100, z=0.25, *args, **kwargs):
		initialize_habitats(self,pscreen)
		initialize_states(self, dead=False, tangible=0, immobile=1)
		initialize_attributes(self, pos=location, vel=v(0,0), acc=v(0,0), r=rad)
		self.z = z
		self.shape.drawtype = "fill"

		self.spawncount = 0
		self.spawnmax = 10
		self.maxvelocity = 1000
	def collide(self,other): pass
	def update(self, timestep):
		if self.spawncount > self.spawnmax: return None
		if random.random() < SPAWNCHANCE:
			r = random.random()*self.rad
			angle = random.random()*2*math.pi
			position = self.pos + v(r*math.cos(angle), r*math.sin(angle))
			newball = EnemyBall(self.pscreen, location=position, rad=30)
			vel = random.random()*self.maxvelocity
			angle = random.random()*2*math.pi
			newball.vel = v( vel*math.cos(angle), vel*math.sin(angle) )

			self.pscreen.addcomponent(newball, 0,0,0)

			self.spawncount = self.spawncount + 1
	def draw(self): 
		pyglet.gl.glColor4f(0.6,0.0,0.6,0.4)
		self.shape.draw(self.pos, self.z)
			
class EnemyBall(object):
	""" An enemy ball, which can be destroyed by bullets. """
	def __init__(self, pscreen, location=v(0,0), rad=30, *args, **kwargs):
		initialize_habitats(self,pscreen)
		initialize_states(self, dead=False, tangible=1, immobile=0)
		initialize_attributes(self, pos=location, vel=v(0,0), acc=v(0,0), r=rad)
		self.shape.drawtype = "fill"
		self.enemy = True
	def collide(self,other):
		if hasattr(other,"bullet"):
			if other.bullet: self.dead = True
		phys_collide(self,other)
	def update(self,timestep):
		update_world(self,timestep)
		update_inertia(self,timestep)
	def draw(self):
		pyglet.gl.glColor3f(0.5,0.5,0.5)
		self.shape.draw(self.pos)



################################
### Player-related stuff!    ###
### Player, Bullets, Camera. ###
################################

class PlayerBall(object):
	def __init__(self,pscreen, location=v(0,0), *args, **kwargs):
		initialize_habitats(self,pscreen)
		initialize_states(self, dead=False, tangible=1, immobile=0)
		initialize_attributes(self, pos=location, vel=v(0,0), acc=v(0,0), r=12)
		self.z=0

		self.templatetext = "Our hero, L&G!:\n%f\t%f\n%s"
		self.ftext = "huh?"
		self.labelthing = text.Label((self.templatetext) % (0, 0, self.ftext) , 'Arial', 12, \
				x = 3*self.pscreen.pwin.width/4, y = self.pscreen.pwin.height/4, anchor_x = "left" , anchor_y = "top" , \
				width = self.pscreen.pwin.width/4 , height = self.pscreen.pwin.height/4 , multiline = 1 )

		self.thrust = 7500
		self.thrustdir = v(0,0)
		self.shooting = False
		self.player = True

		self.shape2 = shapes.Circle(10, rad=self.rad/4, drawtype="fill", invert=0)
	def firebullet(self):
		newbullet = BulletBall(self.pscreen, self, location=self.pos)
		if abs(self.vel) == 0:
			newbullet.vel = v(0, 500)
		else:
			newbullet.vel = self.vel + 500*self.vel.unit()
		self.pscreen.addcomponent(newbullet, 0,0,0)
	def gotkill(self, other):
		self.pscreen.killcountincrease()

	def collide(self,other):
		self.ftext = ("%f\t%f") % ((self.pos-other.pos).x, (self.pos-other.pos).y)
		phys_collide(self,other)
	def update(self,timestep):
		self.acc = self.acc + self.thrust*timestep*self.thrustdir

		update_world(self,timestep)
		update_inertia(self,timestep)

		self.labelthing.text = self.templatetext % (self.pos.x, self.pos.y, self.ftext)
	def draw(self):
		pyglet.gl.glColor3f(0.0,0.6,0.0)
		self.shape.draw(self.pos)
		pyglet.gl.glColor3f(0.0,0.0,1.0)
		self.shape2.draw(self.pos + self.vel.unit()*(self.shape.rad - self.shape2.rad/2))
		self.labelthing.draw()
	def on_key_press(self, symbol, modifiers):
		if symbol == key.UP: self.thrustdir = self.thrustdir + v(0,2)
		if symbol == key.DOWN: self.thrustdir = self.thrustdir + v(0,-1)
		if symbol == key.LEFT: self.thrustdir = self.thrustdir + v(-1,0)
		if symbol == key.RIGHT: self.thrustdir = self.thrustdir + v(1,0)
		if symbol == key.Z: self.firebullet()
	def on_key_release(self, symbol, modifiers):
		if symbol == key.UP: self.thrustdir = self.thrustdir - v(0,2)
		if symbol == key.DOWN: self.thrustdir = self.thrustdir - v(0,-1)
		if symbol == key.LEFT: self.thrustdir = self.thrustdir - v(-1,0)
		if symbol == key.RIGHT: self.thrustdir = self.thrustdir - v(1,0)
	def on_mouse_press(self, x, y, button, modifiers):pass
	def on_mouse_drag(self, x, y, dx, dy, button, modifiers):pass
	def on_mouse_motion(self, x, y, dx, dy):pass
class BulletBall(object):
	""" A projectile object. It's a circle! Woo."""
	def __init__(self, pscreen, parent,location=v(0,0), *args, **kwargs):
		initialize_habitats(self,pscreen)
		initialize_states(self, dead=False, tangible=1, immobile=0)
		initialize_attributes(self, pos=location, vel=v(0,0), acc=v(0,0), r=5)
		self.parent = parent
		self.bullet = True
		self.timetolive = 4
		self.time=0
	def collide(self,other):
		if hasattr(other,"player"):
			if other.player: pass
		if hasattr(other,"enemy"): 
			if other.enemy:
				self.dead = True
				self.parent.gotkill(other)
				pass
		phys_collide(self,other)
	def update(self,timestep):
		self.time += timestep
		if self.time>self.timetolive:
			self.dead = True
		update_world(self,timestep)
		update_inertia(self,timestep)
	def draw(self):
		pyglet.gl.glColor3f(1.0,0.0,0.0)
		self.shape.draw(self.pos)
class CameraFollower(object):
	def __init__(self, pscreen, latch=None, spring=30, damping=2):
		initialize_habitats(self,pscreen)
		initialize_states(self, dead=False, tangible=0, immobile=0)
		self.z = -10

		self.templatetext = "FPS: %.2f"
		self.labelthing = text.Label((self.templatetext) % (0,) , 'Arial', 12, x=0, y=0, anchor_x="left", anchor_y="top",\
				width = self.pscreen.pwin.width/4 , height = self.pscreen.pwin.height/4 , multiline = 1 )

		self.target = latch
		self.spring = spring
		self.damping = damping

		self.scale = 0.5
		self.sy = 0.5
		self.decay = 0.4

		self.time = 0

		self.pos = self.target.pos
		self.vel = self.target.vel
		self.acc = v(0,0)
	def update(self,timestep):
		self.acc = self.acc + self.spring*(self.target.pos-self.pos)
		self.acc = self.acc - self.damping*self.vel
		self.vel = self.vel + timestep*self.acc
		self.pos = self.pos + timestep*self.vel
		self.acc = v(0,0)

		targvel = abs(self.target.vel)/1000
		scalefactor = 2/(1+math.exp(-targvel))
		scalefactor = scalefactor + 1
		self.scale = self.decay*self.scale + (1-self.decay)/scalefactor
		self.time = self.time + timestep
		#print(self.pscreen.pwin.avefps)
	def draw(self):
		pyglet.gl.glLoadIdentity()
		pyglet.gl.glTranslatef( self.pscreen.pwin.width/2, self.pscreen.pwin.height/2, 0.0 ) # Take the center of the parent window as the origin.
		pyglet.gl.glFrustum(-1.0, 1.0, -1.0, 1.0, 0.5, 20.0) # Set up the frustrum
		#pyglet.gl.glScalef( 1/self.scale, 1/self.sy, 1.0)
		pyglet.gl.glTranslatef( -self.pos.x, -self.pos.y, -0.5/self.scale )
		#self.labelthing.draw()
