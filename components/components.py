from vectors import v
from pyglet import gl as opengl
from . import shapes
from .base_components import *

class CollisionComponent(AbstractComponent):
	def __init__(self, shape=None, position_component=None, physics_component=None, immobile=None, *args, **keyword_args):
		super().__init__(*args, **keyword_args)
		
		if position_component is None:
			if hasattr(self.owner, 'position_component'):
				position_component = self.owner.position_component
			else:
				position_component = PositionComponent(owner=self.owner)
		self.position_component = position_component

		if shape is None:
			if hasattr(self.owner, 'shape'):
				shape = self.owner.shape
			else:
				shape = shapes.Point()
		self.shape = shape
		
		if physics_component is None:
			if hasattr(self.owner, 'physics_component'):
				physics_component = self.owner.physics_component
		self.physics_component = physics_component

		if immobile is None:
			if self.physics_component is None:
				immobile = True
			else: 
				immobile = self.physics_component.immobile
		self.immobile = immobile
		
		self.update()
	def collides_with(self, other): 
		return True
	def collide(self, other): 
		pass
	def update(self, timestep=0):
		self.x_pos, self.y_pos = self.position_component.position.x, self.position_component.position.y
		self.x_min = self.x_pos + self.shape.xbounds[0]
		self.x_max = self.x_pos + self.shape.xbounds[1]
		self.y_min = self.y_pos + self.shape.ybounds[0]
		self.y_max = self.y_pos + self.shape.ybounds[1]

def attach_collision(target, *arguments, **keyword_arguments):
	target.collision_component = CollisionComponent(*arguments, **keyword_arguments)

class PhysicsComponent(AbstractComponent):
	def __init__(self, position_component=None, pos=None, vel=None, acc=None, shape=None, tangible=True, immobile=False, world_forces=True, *args, **keyword_args):
		super().__init__(*args, **keyword_args)
		
		if position_component is None:
			if hasattr(self.owner, 'position_component'):
				position_component = self.owner.position_component
			else:
				position_component = PositionComponent(owner=self.owner, position=(pos or v(0,0)))
		self.position_component = position_component

		if shape is None:
			if hasattr(self.owner, 'shape'):
				shape = self.owner.shape
			else:
				shape = shapes.Point()
		self.shape = shape
		
		if hasattr(self.owner, 'basic_component'):
			self.screen = self.owner.basic_component.parent_screen
		
		self.vel = vel or v(0,0)
		self.acc = acc or v(0,0)
		
		self.tangible = tangible
		self.immobile = immobile
		self.world_forces = world_forces
	
	@property
	def pos(self): return self.position_component.position
	@pos.setter
	def pos(self, value): self.position_component.position = value

	def update(self, timestep):
		if not self.immobile:
			if self.world_forces:
				self.acc += timestep*self.screen.constants['gravity']
				self.acc -= timestep*self.screen.constants['drag']*self.vel
			self.vel = self.vel + timestep*self.acc
			self.position_component.position += timestep*self.vel
			self.acc = v(0,0)

def bounce(thing, other, vector=None):
	screen = thing.screen
	
	velocity_perpendicular = thing.vel.proj(vector)
	velocity_parallel = thing.vel - velocity_perpendicular
	
	if vector*thing.vel > 0:
		thing.vel = screen.constants['friction'] * velocity_parallel + screen.constants['elasticity'] * velocity_perpendicular
	else:
		thing.vel = screen.constants['friction'] * velocity_parallel - screen.constants['elasticity'] * velocity_perpendicular
	
	thing.position_component.position += screen.constants['displace'] * vector

	if other.immobile:
		thing.position_component.position += vector

	if screen.draw_debug:
		opengl.glBegin(opengl.GL_LINES)
		p = thing.position_component.position
		opengl.glVertex3f(p.x, p.y, 11)
		opengl.glVertex3f(p.x + 5*vector.x, p.y + 5*vector.y, 11)
		opengl.glEnd()

class RenderableComponent(AbstractComponent):
	"""A component describing rendering behavior. This just draws the shape at the owner's position."""
	def __init__(self, shape=None, position_component=None, pos=None, priority=False, z=0, color=None, *args, **keyword_args):
		super().__init__(*args, **keyword_args)

		if position_component is None:
			if hasattr(self.owner, 'position_component'):
				position_component = self.owner.position_component
			else:
				position_component = PositionComponent(owner=self.owner, position=(pos or v(0,0)))
		self.position_component = position_component

		if shape is None:
			if hasattr(self.owner, 'shape'):
				shape = self.owner.shape
			else:
				shape = shapes.Point()
		self.shape = shape

		self.color = color or (0, 0, 0, 1)
		self.z = z
		self.priority=priority
		self.update()

	@property
	def color(self): return self._color
	@color.setter
	def color(self, value): self._color = value if len(value) is 4 else value + (1.0,) 
	def update(self, timestep=0):
		self.x_pos, self.y_pos = self.position_component.position.x, self.position_component.position.y
		self.x_min = self.x_pos + self.shape.xbounds[0]
		self.x_max = self.x_pos + self.shape.xbounds[1]
		self.y_min = self.y_pos + self.shape.ybounds[0]
		self.y_max = self.y_pos + self.shape.ybounds[1]

	def draw(self):
		opengl.glColor4f(*self._color)
		self.shape.draw(self.position_component.position, self.z)
