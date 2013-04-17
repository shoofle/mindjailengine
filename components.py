from vectors import v
from pyglet import gl as opengl
import shapes

class AbstractComponent(object):
	def __init__(self, owner=None, *positional_arguments, **keyword_args):
		self.owner = owner
		self.__dict__.update(keyword_args)

class BasicComponent(AbstractComponent):
	def __init__(self, screen=None, dead=False, *args, **keyword_args):
		super(BasicComponent, self).__init__(*args, **keyword_args)
		self.parent_screen = screen
		self.dead = dead
	def update(self, timestep): pass

class PositionComponent(AbstractComponent):
	def __init__(self, position=None, *args, **keyword_args):
		super(PositionComponent, self).__init__(*args, **keyword_args)
		self.position = position or v(0,0)

class CollisionComponent(AbstractComponent):
	def __init__(self, shape=None, position_component=None, physics_component=None, immobile=None, *args, **keyword_args):
		super(CollisionComponent, self).__init__(*args, **keyword_args)
		
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
			if hasattr(self.owner, 'physics_component'):
				immobile = self.owner.physics_component.immobile
			else: 
				immobile = True
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

class PhysicsComponent(AbstractComponent):
	def __init__(self, position_component=None, pos=None, vel=None, acc=None, shape=None, tangible=True, immobile=False, world_forces=True, *args, **keyword_args):
		super(PhysicsComponent, self).__init__(*args, **keyword_args)
		
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

class RenderableComponent(AbstractComponent):
	def __init__(self, shape=None, position_component=None, pos=None, priority=False, z=0, color=None, *args, **keyword_args):
		super(RenderableComponent, self).__init__(*args, **keyword_args)
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
	def color(self, value): self._color = value if len(value) is 4 else (value[0], value[1], value[2], 1.0) 
	
	def update(self, timestep=0):
		self.x_pos, self.y_pos = self.position_component.position.x, self.position_component.position.y
		self.x_min = self.x_pos + self.shape.xbounds[0]
		self.x_max = self.x_pos + self.shape.xbounds[1]
		self.y_min = self.y_pos + self.shape.ybounds[0]
		self.y_max = self.y_pos + self.shape.ybounds[1]

	def draw(self):
		opengl.glColor4f(*self._color)
		self.shape.draw(self.position_component.position, self.z)

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
