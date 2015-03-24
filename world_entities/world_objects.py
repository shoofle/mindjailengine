import pyglet
from pyglet.window import key

import math
import random
from vectors import v

from components import * 

#############################################
### The objects which populate the level! ###
#############################################
class Entity(object):
	pass

class FreeBall(Entity):
	""" A circular object that can move and bounce freely. It's a circle! Woo."""
	def __init__(self, pscreen, location=v(0,0), rad=20):
		self.lifecycle = Lifecycle(owner=self, screen=pscreen)
		self.position_component = PositionComponent(owner=self, position=location)

		self.shape = shapes.Circle(owner=self, rad=rad, drawtype="3d")
		self.physics_component = PhysicsBody(owner=self, immobile=False)
		self.renderable_component = ShapeRenderer(owner=self)

		self.collision_component = Collider(owner=self)
		
class ObstacleBall(Entity):
	""" A ball fixed in space. """
	def __init__(self, pscreen, location=v(0,0), rad=20):
		self.lifecycle = Lifecycle(owner=self, screen=pscreen)
		self.position_component = PositionComponent(owner=self, position=location)
		
		self.shape = shapes.Circle(owner=self, rad=rad, drawtype="3d")
		self.physics_component = PhysicsBody(owner=self, immobile=True)
		self.renderable_component = ShapeRenderer(owner=self)
		
		self.collision_component = Collider(owner=self)
class ObstacleLine(Entity):
	""" A line, potentially with rounded ends, fixed in space. """
	def __init__(self, pscreen, location=v(0,0), endpoint=v(0,1), thick = 0,*args, **kwargs):
		self.lifecycle = Lifecycle(owner=self, screen=pscreen)
		self.position_component = PositionComponent(owner=self, position=location)
		
		self.shape = shapes.Line(owner=self, vector=endpoint - location, thickness=thick)
		self.physics_component = PhysicsBody(owner=self, immobile=True)
		self.renderable_component = ShapeRenderer(owner=self)
		
		self.collision_component = Collider(owner=self)

###################
### Opponents!? ###
###################

class Spawner(Entity):
	""" A circular area that spawns EnemyBalls until it reaches the max, with chance spawn_chance every frame. """
	def __init__(self, pscreen, location=v(0,0), rad=100, z=0.25):
		self.lifecycle = Lifecycle(owner=self, screen=pscreen)
		self.lifecycle.update = self.update
		self.position_component = PositionComponent(owner=self, position=location)
		
		self.shape = shapes.Circle(owner=self, rad=rad, invert=0, drawtype="fill")
		self.renderable_component = ShapeRenderer(owner=self, z=z, color=(0.6, 0, 0.6, 0.4))

		self.spawn_count = 0
		self.spawn_count_max = 20 # Maximum number that will spawn before the spawner dies.
		self.spawn_chance = 0.01 # chance of spawning, per frame.
		self.max_velocity = 1000
	def update(self, timestep):
		if self.spawn_count > self.spawn_count_max: return
		if random.random() < self.spawn_chance:
			r = random.random()*self.shape.radius
			angle = random.random()*2*math.pi
			position = self.position_component.position + v(r*math.cos(angle), r*math.sin(angle))
			newball = EnemyBall(self.lifecycle.parent_screen, location=position, rad=30)
			
			vel = random.uniform(0.0, self.max_velocity)
			angle = random.uniform(0.0, 2*math.pi)
			newball.physics_component.vel = v( vel*math.cos(angle), vel*math.sin(angle) )

			self.lifecycle.parent_screen.add_entity(newball)

			self.spawn_count = self.spawn_count + 1

class EnemyBall(Entity):
	""" An enemy ball, which can be destroyed by bullets. """
	def __init__(self, pscreen, location=v(0,0), rad=30):
		self.lifecycle = Lifecycle(owner=self, screen=pscreen)
		self.position_component = PositionComponent(owner=self, position=location)
		
		self.shape = shapes.Circle(owner=self, rad=rad, drawtype="fill")
		self.physics_component = PhysicsBody(owner=self)
		self.renderable_component = ShapeRenderer(owner=self, color=(0.5,0.5,0.5))
		
		self.collision_component = Collider(owner=self)
		self.collision_component.collide = self.collide
		
		self.enemy = True
	def collide(self,other):
		if hasattr(other.owner,"bullet") and other.owner.bullet: self.lifecycle.dead = True

