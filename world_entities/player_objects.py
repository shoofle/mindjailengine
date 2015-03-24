import pyglet
from pyglet.window import key

import math
import random
from vectors import v

from .world_objects import Entity
from components import *

################################
### Player-related stuff!    ###
### Player, Bullets, Camera. ###
################################

class PlayerBall(Entity):
	""" The player. Oh my, but this is a big class. Oh well. It's an important object. """
	def __init__(self, pscreen, location=v(0,0)):
		self.lifecycle = Lifecycle(owner=self, screen=pscreen)
		self.lifecycle.update = self.update
		self.position_component = PositionComponent(owner=self, position=location)
		
		self.shape = shapes.Circle(owner=self, rad=15)
		self.physics_component = PhysicsBody(owner=self)
		self.renderable_component = ShapeRenderer(owner=self, color=(0.0, 0.6, 0.0))
		self.input_listeners = None #TODO: input listener component.

		self.collision_component = Collider(owner=self)
		
		self.thrust = 30000
		self.thrustdir = v(0,0)

		self.player = True
		#self.shape2 = shapes.Circle(10, rad=self.rad/4, drawtype="fill", invert=0)

	def fire_bullet(self):
		newthing = BulletBall(self.lifecycle.parent_screen, self, location=self.position_component.position)
		svel = self.physics_component.vel
		if abs(svel) == 0: newthing.physics_component.vel = v(0, 800)
		else: newthing.physics_component.vel = svel + 800*svel.unit()
		self.lifecycle.parent_screen.add_entity(newthing)

	def fire_bomb(self):
		newthing = BombBall(self.lifecycle.parent_screen, self, location=self.position_component.position)
		svel = self.physics_component.vel
		if abs(svel) == 0: newthing.physics_component.vel = v(0, 800)
		else: newthing.physics_component.vel = svel + 800*svel.unit()
		self.lifecycle.parent_screen.add_entity(newthing)

	def fire_laser(self):
		svel = self.physics_component.vel
		if abs(svel) == 0: direct = v(0,1)
		else: direct = svel.unit()
		newlaser = LaserLine(self.lifecycle.parent_screen, self, location=self.position_component.position, direction=direct)
		self.lifecycle.parent_screen.add_entity(newlaser)

	def gotkill(self, other): self.lifecycle.parent_screen.killcountincrease()
	def update(self,timestep): self.physics_component.acc += self.thrust*timestep*self.thrustdir
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

class BulletBall(Entity):
	""" A projectile object. It's a circle! Woo."""
	def __init__(self, pscreen, parent, location=v(0,0)):
		self.parent = parent
		self.bullet = True
		self.time_to_live = 4
		self.time=0

		self.lifecycle = Lifecycle(owner=self, screen=pscreen)
		self.lifecycle.update = self.update
		self.position_component = PositionComponent(owner=self, position=location)

		self.shape = shapes.Circle(owner=self, rad=5)
		self.physics_component = PhysicsBody(owner=self)
		self.renderable_component = ShapeRenderer(owner=self, color=(1.0, 0.2, 0.5))
		
		self.collision_component = Collider(owner=self)
		self.collision_component.collides_with = lambda other: other is not self.parent
		self.collision_component.collide = self.collide
	def collide(self,other):
		if hasattr(other.owner,"enemy") and other.owner.enemy:
			self.lifecycle.dead = True
			self.parent.gotkill(other.owner)
	def update(self,timestep):
		self.time += timestep
		if self.time>self.time_to_live:
			self.lifecycle.dead = True

class LaserLine(Entity):
	""" A laser beam! """
	def __init__(self, pscreen, parent,location=v(0,0), direction=v(0,1), length=1000):
		self.parent = parent
		self.bullet = True
		self.time_to_live = 0.5
		self.time=0

		self.lifecycle = Lifecycle(owner=self, screen=pscreen)
		self.lifecycle.update = self.update
		self.position_component = PositionComponent(owner=self, position=location)
		
		self.shape=shapes.Line(owner=self, vector=direction*length)
		self.physics_component = PhysicsBody(owner=self, tangible=False, immobile=True)
		self.renderable_component = ShapeRenderer(owner=self, color=(0.0, 0.0, 1.0, 1.0))
		
		self.collision_component = Collider(owner=self)
		self.collision_component.collides_with = lambda other: other is not self.parent
		self.collision_component.collide = self.collide
	def collide(self,other):
		if hasattr(other, "enemy") and other.enemy:
			self.lifecycle.dead = True
			self.parent.gotkill(other)
	def update(self,timestep):
		self.time += timestep
		self.renderable_component.color = (0.0, 0.0, 1.0-(self.time/self.time_to_live), 1.0-(self.time/self.time_to_live))
		if self.time>self.time_to_live: self.lifecycle.dead = True

class BombBall(Entity):
	""" A bomb, which explodes after a certain amount of time to throw things flying. """
	def __init__(self, pscreen, parent, location=v(0,0)):
		self.parent = parent
		self.time_to_live=2
		self.time=0

		self.lifecycle = Lifecycle(owner=self, screen=pscreen)
		self.lifecycle.update = self.update
		self.position_component = PositionComponent(owner=self, position=location)
		
		self.shape = shapes.Circle(owner=self, rad=8)
		self.physics_component = PhysicsBody(owner=self, pos=location)
		self.renderable_component = ShapeRenderer(owner=self, color=(0.0, 0.0, 0.0, 1.0))
		
		self.collision_component = Collider(owner=self)
		self.collision_component.collides_with = lambda other: other is not self.parent
	def update(self,timestep):
		self.time += timestep
		if self.time > self.time_to_live: 
			new_explosion = BombExplosion(self.lifecycle.parent_screen, self, location=self.position_component.position)
			self.lifecycle.parent_screen.add_entity( new_explosion  )
			self.lifecycle.dead = True
		self.renderable_component.color = ((self.time/self.time_to_live), 0.0, 0.0, 1.0)

class BombExplosion(Entity):
	""" The explosion for the bomb. This is a non-tangible object which needs to collide with things. """
	def __init__(self, pscreen, parent, location=v(0,0)):
		self.parent = parent
		self.time_to_live=0.5
		self.time=0

		self.lifecycle = Lifecycle(owner=self, screen=pscreen)
		self.lifecycle.update = self.update
		self.position_component = PositionComponent(owner=self, position=location)
		
		self.shape = shapes.Circle(owner=self, rad=100, drawtype="fill")
		self.physics_component = PhysicsBody(owner=self, tangible=False, immobile=True)
		self.renderable_component = ShapeRenderer(owner=self, color=(1, 0, 0, 1))
		
		self.collision_component = Collider(owner=self)
		self.collision_component.collide = self.collide
	def collide(self, other): 
		vector = other.owner.position_component.position - self.position_component.position
		other.owner.physics_component.acc += 100*(1-self.time/self.time_to_live)*vector
	def update(self, timestep):
		self.time += timestep
		if self.time > self.time_to_live:
			self.lifecycle.dead = True
		self.renderable_component.color = (1.0-self.time/self.time_to_live, 0, 0, 1.0-self.time/self.time_to_live)

