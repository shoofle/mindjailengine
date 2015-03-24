import math
import random

import pyglet
from pyglet import gl as opengl, text
from pyglet.window import key

from vectors import v
from components.components import *
from components.base_components import *
from components import shapes

#############################################
### The objects which populate the level! ###
#############################################

def new_free_ball(pscreen, location=v(0,0), rad=20):
	""" A circular object that can move and bounce freely. It's a circle! Woo."""
	x = dict()
	x['basic'] = BasicComponent(owner=x, screen=pscreen)
	x['position'] = PositionComponent(owner=x, position=location)

	x['shape'] = shapes.Circle(owner=x, rad=rad, drawtype="3d")
	x['physics_body'] = PhysicsComponent(owner=x, immobile=False)
	x['rendering'] = RenderableComponent(owner=x)

	x['collision'] = CollisionComponent(owner=x)
	return x
	
def new_obstacle_ball(pscreen, location=v(0,0), rad=20):
	""" A ball fixed in space. """
	x = dict()
	x['basic'] = BasicComponent(owner=x, screen=pscreen)
	x['position'] = PositionComponent(owner=x, position=location)
	
	x['shape'] = shapes.Circle(owner=x, rad=rad, drawtype="3d")
	x['physics_body'] = PhysicsComponent(owner=x, immobile=True)
	x['rendering'] = RenderableComponent(owner=x)
	
	x['collision'] = CollisionComponent(owner=x)
	return x

def new_obstacle_line(pscreen, location=v(0,0), endpoint=v(0,1), thick = 0):
	""" A line, potentially with rounded ends, fixed in space. """
	x = dict()
	x['basic'] = BasicComponent(owner=x, screen=pscreen)
	x['position'] = PositionComponent(owner=x, position=location)
	
	x['shape'] = shapes.Line(owner=x, vector=endpoint - location, thickness=thick)
	x['physics_body'] = PhysicsComponent(owner=x, immobile=True)
	x['rendering'] = RenderableComponent(owner=x)
	
	x['collision'] = CollisionComponent(owner=x)
	return x

###################
### Opponents!? ###
###################

class SpawnerBrain(AbstractComponent):
	def __init__(self, spawn_count=0, spawn_count_max=20, spawn_chance=0.01, max_velocity=1000, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.spawn_count = spawn_count
		self.spawn_count_max = spawn_count_max
		self.spawn_chance = spawn_chance
		self.max_velocity = max_velocity
	def update(self, timestep):
		if self.spawn_count > self.spawn_count_max: return

		owner = self.owner
		if random.random() < self.spawn_chance:
			r = random.random()*owner['shape'].radius
			angle = random.random()*2*math.pi
			position = owner['position'].position + v(r*math.cos(angle), r*math.sin(angle))
			newball = new_enemy_ball(owner['basic'].parent_screen, location=position, rad=30)
			
			vel = random.uniform(0.0, self.max_velocity)
			angle = random.uniform(0.0, 2*math.pi)
			newball['physics_body'].vel = v( vel*math.cos(angle), vel*math.sin(angle) )

			owner['basic'].parent_screen.add_entity(newball)

			self.spawn_count = self.spawn_count + 1

def new_spawner(pscreen, location=v(0,0), rad=100, z=0.25):
	"""A spawner, it'll make enemy balls."""
	x = dict()
	x['basic'] = BasicComponent(owner=x, screen=pscreen)
	x['spawner'] = SpawnerBrain(owner=x) # default args are good enough for me
	x['basic'].update = x['spawner'].update
	
	x['position'] = PositionComponent(owner=x, position=location)
	x['shape'] = shapes.Circle(owner=x, rad=rad, invert=0, drawtype="fill")
	x['rendering'] = RenderableComponent(owner=x, z=z, color=(0.6, 0, 0.6, 0.4))
	return x

def new_enemy_ball(pscreen, location=v(0,0), rad=30):
	"""An enemy ball, which can be destroyed by bullets. """
	x = dict()
	x['basic'] = BasicComponent(owner=x, screen=pscreen)
	x['position'] = PositionComponent(owner=x, position=location)
	
	x['shape'] = shapes.Circle(owner=x, rad=rad, drawtype="fill")
	x['physics_body'] = PhysicsComponent(owner=x, position_component=x.position_component)
	x['rendering'] = RenderableComponent(owner=x, position_component=x.position_component, color=(0.5,0.5,0.5))
	
	collider = CollisionComponent(owner=x, position_component=x.position_component, physics_component=x.physics_component)
	def collide(other):
		if BulletBall.is_a_bullet(other): collider.owner['basic'].dead = True
	collider.collide = collide
	x['collision'] = collider
	
	x['enemy'] = True

################################
### Player-related stuff!    ###
### Player, Bullets, Camera. ###
################################

class PlayerBall(dict):
	""" The player. Oh my, but this is a big class. Oh well. It's an important object. """
	def __init__(x, pscreen, location=v(0,0)):
		super().__init__(self)
		self['basic'] = BasicComponent(owner=self, screen=pscreen)
		self['basic'].update = self.time_step
		self['position'] = PositionComponent(owner=self, position=location)
		
		self['shape'] = shapes.Circle(owner=self, rad=15)
		self['physics'] = PhysicsComponent(owner=self)
		self['renderable'] = RenderableComponent(owner=self, color=(0.0, 0.6, 0.0))
		self['input_listeners'] = None #TODO: input listener component.

		self['collision'] = CollisionComponent(owner=self)
		
		self.thrust = 30000
		self.thrustdir = v(0,0)

		self.player = True
		#self.shape2 = shapes.Circle(10, rad=self.rad/4, drawtype="fill", invert=0)

	def fire_bullet(self):
		newthing = BulletBall(self.basic_component.parent_screen, self, location=self.position_component.position)
		svel = self.physics_component.vel
		if abs(svel) == 0: newthing.physics_component.vel = v(0, 800)
		else: newthing.physics_component.vel = svel + 800*svel.unit()
		self.basic_component.parent_screen.add_entity(newthing)

	def fire_bomb(self):
		newthing = BombBall(self.basic_component.parent_screen, self, location=self.position_component.position)
		svel = self.physics_component.vel
		if abs(svel) == 0: newthing.physics_component.vel = v(0, 800)
		else: newthing.physics_component.vel = svel + 800*svel.unit()
		self.basic_component.parent_screen.add_entity(newthing)

	def fire_laser(self):
		svel = self.physics_component.vel
		if abs(svel) == 0: direct = v(0,1)
		else: direct = svel.unit()
		newlaser = LaserLine(self.basic_component.parent_screen, self, location=self.position_component.position, direction=direct)
		self.basic_component.parent_screen.add_entity(newlaser)

	def gotkill(self, other): self.basic_component.parent_screen.killcountincrease()
	def time_step(self,timestep): self.physics_component.acc += self.thrust*timestep*self.thrustdir
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
	def __init__(self, pscreen, parent, location=v(0,0), *args, **kwargs):
		self.parent = parent
		self.bullet = True
		self.time_to_live = 4
		self.time=0

		self.basic_component = BasicComponent(owner=self, screen=pscreen)
		self.basic_component.update = self.update
		self.position_component = PositionComponent(owner=self, position=location)

		self.shape = shapes.Circle(owner=self, rad=5)
		self.physics_component = PhysicsComponent(owner=self, position_component=self.position_component)
		self.renderable_component = RenderableComponent(owner=self, position_component=self.position_component, color=(1.0, 0.2, 0.5))
		
		self.collision_component = CollisionComponent(owner=self, position_component=self.position_component, physics_component=self.physics_component)
		self.collision_component.collides_with = lambda other: other is not self.parent
		self.collision_component.collide = self.collide
	def collide(self,other):
		if hasattr(other.owner,"enemy") and other.owner.enemy:
			self.basic_component.dead = True
			self.parent.gotkill(other.owner)
	def update(self,timestep):
		self.time += timestep
		if self.time>self.time_to_live:
			self.basic_component.dead = True
	@classmethod
	def is_a_bullet(querent):
		if isinstance(querent, CollisionComponent):
			querent = querent.owner
		return 'bullet' in querent

class LaserLine(Entity):
	""" A laser beam! """
	def __init__(self, pscreen, parent,location=v(0,0), direction=v(0,1), length=1000, *args, **kwargs):
		self.parent = parent
		self.bullet = True
		self.time_to_live = 0.5
		self.time=0

		self.basic_component = BasicComponent(owner=self, screen=pscreen)
		self.basic_component.update = self.update
		self.position_component = PositionComponent(owner=self, position=location)
		
		self.shape=shapes.Line(owner=self, vector=direction*length)
		self.physics_component = PhysicsComponent(owner=self, position_component=self.position_component, tangible=False, immobile=True)
		self.renderable_component = RenderableComponent(owner=self, position_component=self.position_component, color=(0.0, 0.0, 1.0, 1.0))
		
		self.collision_component = CollisionComponent(owner=self, position_component=self.position_component, physics_component=self.physics_component)
		self.collision_component.collides_with = lambda other: other is not self.parent
		self.collision_component.collide = self.collide
	def collide(self,other):
		if hasattr(other, "enemy") and other.enemy:
			self.basic_component.dead = True
			self.parent.gotkill(other)
	def update(self,timestep):
		self.time += timestep
		self.renderable_component.color = (0.0, 0.0, 1.0-(self.time/self.time_to_live), 1.0-(self.time/self.time_to_live))
		if self.time>self.time_to_live: self.basic_component.dead = True

class BombBall(Entity):
	""" A bomb, which explodes after a certain amount of time to throw things flying. """
	def __init__(self, pscreen, parent, location=v(0,0)):
		self.parent = parent
		self.time_to_live=2
		self.time=0

		self.basic_component = BasicComponent(owner=self, screen=pscreen)
		self.basic_component.update = self.update
		self.position_component = PositionComponent(owner=self, position=location)
		
		self.shape = shapes.Circle(owner=self, rad=8)
		self.physics_component = PhysicsComponent(owner=self, pos=location)
		self.renderable_component = RenderableComponent(owner=self, color=(0.0, 0.0, 0.0, 1.0))
		
		self.collision_component = CollisionComponent(owner=self)
		self.collision_component.collides_with = lambda other: other is not self.parent
	def update(self,timestep):
		self.time += timestep
		if self.time > self.time_to_live: 
			new_explosion = BombExplosion(self.basic_component.parent_screen, self, location=self.position_component.position)
			self.basic_component.parent_screen.add_entity( new_explosion  )
			self.basic_component.dead = True
		self.renderable_component.color = ((self.time/self.time_to_live), 0.0, 0.0, 1.0)
class BombExplosion(Entity):
	""" The explosion for the bomb. This is a non-tangible object which needs to collide with things. """
	def __init__(self, pscreen, parent, location=v(0,0)):
		self.parent = parent
		self.time_to_live=0.5
		self.time=0

		self.basic_component = BasicComponent(owner=self, screen=pscreen)
		self.basic_component.update = self.update
		self.position_component = PositionComponent(owner=self, position=location)
		
		self.shape = shapes.Circle(owner=self, rad=100, drawtype="fill")
		self.physics_component = PhysicsComponent(owner=self, position_component=self.position_component, tangible=False, immobile=True)
		self.renderable_component = RenderableComponent(owner=self, position_component=self.position_component, color=(1, 0, 0, 1))
		
		self.collision_component = CollisionComponent(owner=self, position_component=self.position_component, physics_component=self.physics_component)
		self.collision_component.collide = self.collide
	def collide(self, other): 
		vector = other.owner.position_component.position - self.position_component.position
		other.owner.physics_component.acc += 100*(1-self.time/self.time_to_live)*vector
	def update(self, timestep):
		self.time += timestep
		if self.time > self.time_to_live:
			self.basic_component.dead = True
		self.renderable_component.color = (1.0-self.time/self.time_to_live, 0, 0, 1.0-self.time/self.time_to_live)

class CameraFollower(Entity):
	""" This object follows the latch and defines the drawing frustrum and basically sets up cameras. """
	def __init__(self, pscreen, latch=None, spring=30, damping=2):
		self.template_text = "FPS: {0:.2f}\n# of Objects: {1}\n# of Non-Static: {2}"
		label_x, label_y = 3*pscreen.width/4.0, 1*pscreen.height/4.0
		label_width, label_height = pscreen.width/4.0, pscreen.height/8.0
		self.hud_label = text.Label(
				self.template_text.format(0, 0, 0), 
				font_name='Arial', font_size=12, color=(0,0,0,255), 
				x=label_x, y=label_y, width=label_width, height=label_height, 
				anchor_x="center", anchor_y="center", multiline = 1 )

		self.hud_background = pyglet.graphics.vertex_list(4, 'v3f', 'c3f') 
		self.hud_background.vertices = (label_x-label_width/2, label_y-label_height/2, -1, label_x+label_width/2, label_y-label_height/2, -1, label_x+label_width/2, label_y+label_height/2, -1, label_x-label_width/2, label_y+label_height/2, -1)
		self.hud_background.colors = (1, 1, 1)*4

		self.target = latch
		self.spring = spring
		self.damping = damping

		self.scale = 0.5
		self.decay = 0.4

		self.basic_component = BasicComponent(owner=self, screen=pscreen)
		self.basic_component.update = self.update
		self.position_component = PositionComponent(owner=self, position=latch.position_component.position)
		
		self.physics_component = PhysicsComponent(owner=self, position_component=self.position_component, tangible=False, world_forces=False)
		self.renderable_component = RenderableComponent(owner=self, position_component=self.position_component, priority=True)
		self.renderable_component.draw = self.draw
	def update(self,timestep):
		# The reason this doesn't call update_inertia is that that also deals with the collision tree.
		self.physics_component.acc += self.spring*(self.target.position_component.position-self.position_component.position)
		self.physics_component.acc -= self.damping*self.physics_component.vel

		targvel = abs(self.target.physics_component.vel)/1000
		scalefactor = 1 + 2/(1+math.exp(-targvel))
		self.scale = self.decay*self.scale + (1-self.decay)/scalefactor

		screen = self.basic_component.parent_screen
		
		self.hud_label.text = self.template_text.format(screen.window.framerate, len(screen.coltree), len(screen.nonstatic_objects))

	def draw(self):
		parent_screen = self.basic_component.parent_screen # Need this a lot, so we should pull it into the local namespace.
		opengl.glMatrixMode(opengl.GL_PROJECTION)
		opengl.glLoadIdentity()
		camera_position = self.position_component.position
		#z = 1000.0 + 500/self.scale
		z=600
		clipping_plane_z_coordinates = (-400.0,500.0)

		dist_to_near_plane = min(z-clipping_plane_z_coordinates[0], z-clipping_plane_z_coordinates[1])
		dist_to_near_plane = max(dist_to_near_plane, 0.1) # Ensure that it's not negative.
		dist_to_far_plane = max(z-clipping_plane_z_coordinates[0], z-clipping_plane_z_coordinates[1])

		# Aspect ratio!
		width = 1000.0
		height = width * parent_screen.height / parent_screen.width

		# Define clipping planes.
		left_at_near_plane = -(dist_to_near_plane/z)*width/2
		right_at_near_plane = (dist_to_near_plane/z)*width/2
		bottom_at_near_plane = -(dist_to_near_plane/z)*height/2
		top_at_near_plane = (dist_to_near_plane/z)*height/2

		# Set camera position.
		opengl.glFrustum(left_at_near_plane, right_at_near_plane, bottom_at_near_plane, top_at_near_plane, dist_to_near_plane, dist_to_far_plane)
		opengl.glTranslatef( -camera_position.x, -camera_position.y, -z )

		# Define the rect of what objects should be drawn.
		camera_rect = parent_screen.camera_rect
		camera_rect.x_min, camera_rect.x_max = camera_position.x - width/2.0, camera_position.x + width/2.0
		camera_rect.y_min, camera_rect.y_max = camera_position.y - height/2.0, camera_position.y + height/2.0

		# Draw the HUD.
		opengl.glPushMatrix() # Push onto the stack, so that we can recover after.
		opengl.glLoadIdentity() # Load a blank matrix.
		opengl.glOrtho(0, parent_screen.width, 0, parent_screen.height, -1, 200) # Put us in orthogonal projection.
		
		self.hud_background.draw(opengl.GL_QUADS)
		self.hud_label.draw() # Okay, this is REALLY GODDAMN WEIRD: Removing this line makes it so that the screen is just always blank.

		opengl.glPopMatrix() # Recover the old projection matrix.
		opengl.glMatrixMode(opengl.GL_MODELVIEW)
