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
		self.position = position

class CollisionComponent(AbstractComponent):
	def __init__(self, shape=None, pos=None, immobile=None, *args, **keyword_args):
		super(CollisionComponent, self).__init__(*args, **keyword_args)
		if shape is None:
			if hasattr(self.owner, 'shape'):
				shape = self.owner.shape
		self.shape = shape
		if immobile is None:
			if hasattr(self.owner, 'physics_component'):
				immobile = self.owner.physics_component.immobile
			else: immobile = True
		self.immobile = immobile
		self.update(0)
	@property
	def pos(self):
		if hasattr(self.owner, 'position_component'):
			return self.owner.position_component.position
	def collides_with(self, other): return True
	def collide(self, other): pass
	def update(self, timestep):
		if self.shape is not None:
			if hasattr(self.owner, 'position_component'):
				pos = self.owner.position_component.position
			else:
				pos = v(0, 0)
			self.x_pos, self.y_pos = pos.x, pos.y
			self.x_min = self.x_pos + self.shape.xbounds[0]
			self.x_max = self.x_pos + self.shape.xbounds[1]
			self.y_min = self.y_pos + self.shape.ybounds[0]
			self.y_max = self.y_pos + self.shape.ybounds[1]

class PhysicsComponent(AbstractComponent):
	def __init__(self, pos=None, vel=None, acc=None, shape=None, tangible=True, immobile=False, world_forces=True, *args, **keyword_args):
		super(PhysicsComponent, self).__init__(*args, **keyword_args)
		if hasattr(self.owner, 'position_component'):
			self.pos = pos or self.owner.position_component.position
		else:
			self.pos = pos or v(0,0)
		self.vel = vel or v(0,0)
		self.acc = acc or v(0,0)
		
		if shape is None:
			if hasattr(self.owner, 'shape'):
				shape = self.owner.shape
		
		self.shape = shape
		self.tangible = tangible
		self.immobile = immobile
		self.world_forces = world_forces
	def update(self, timestep):
		if hasattr(self.owner, 'position_component'):
			self.pos = self.owner.position_component.position
		if not self.immobile:
			if self.world_forces:
				self.acc += timestep*self.owner.basic_component.parent_screen.constants['gravity']
				self.acc -= timestep*self.owner.basic_component.parent_screen.constants['drag']*self.vel
			self.vel = self.vel + timestep*self.acc
			self.pos = self.pos + timestep*self.vel
			self.acc = v(0,0)
		if hasattr(self.owner, 'position_component'):
			self.owner.position_component.position = self.pos

class RenderableComponent(AbstractComponent):
	def __init__(self, shape=None, pos=None, z=0, color=None, *args, **keyword_args):
		super(RenderableComponent, self).__init__(*args, **keyword_args)
		if shape is None:
			if hasattr(self.owner, 'shape'):
				shape = self.owner.shape
		self.shape = shape
		color = color or (0.0, 0.0, 0.0, 1.0)
		if len(color) is 3: color = (color[0], color[1], color[2], 1.0)
		self.color = color
		self.pos = pos or v(0,0)
		self.z = z
	def draw(self):
		opengl.glColor4f(*self.color)
		try:
			self.shape.draw(self.owner.position_component.position, self.z)
		except AttributeError as e:
			self.shape.draw(self.pos, self.z)

def phys_collide(self,other):
	""" Basic response to collisions. If they're immobile, move us out.	"""
	if not other.tangible: return
	if self.immobile and other.immobile: return
	if self.immobile and not other.immobile: return phys_collide(other, self)
	vector = shapes.intersect(self, other) # Returns the shortest vector by which to move 'self' to no longer be intersecting 'other'.
	screen = self.owner.basic_component.parent_screen
	if vector is None: return None
	else:
		velocity_perpendicular = self.vel.proj(vector) # The entity of self.vel which is parallel or anti-parallel to 'vector'.
		velocity_parallel = self.vel - velocity_perpendicular
		if vector*self.vel > 0: 
			# We are already moving in the direction to escape.
			self.vel = screen.constants['friction']*velocity_parallel + screen.constants['elasticity']*velocity_perpendicular
		else:
			# We are moving to be deeper into the object. We should reverse the perpendicular entity of our velocity.
			self.vel = screen.constants['friction']*velocity_parallel - screen.constants['elasticity']*velocity_perpendicular
		self.pos += screen.constants['displace'] * vector
	if other.immobile:
		self.pos += vector
	if screen.draw_debug:
		opengl.glBegin(opengl.GL_LINES)
		opengl.glVertex3f(self.pos.x, self.pos.y, 30.0)
		opengl.glVertex3f(self.pos.x + vector.x, self.pos.y + vector.y, 30.0)
		opengl.glEnd()
