from pyglet import gl as opengl
from vectors import v

from . import shapes
from .base_components import *

class Renderable(AbstractComponent):
	"""Components which are renderable might inherit from this?"""
	x_pos, y_pos = 0, 0
	x_min, x_max = 0, 0
	y_min, y_max = 0, 0
	def __init__(self, position=None, priority=False, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		# Alternately, what if we intelligently decide how to handle a more general position argument?
		if position is None: # If no position was given to us, be smart about it:
			if not hasattr(self.owner, 'position_component'):
				# If the owner doesn't have a position component AND we didn't get passed one, then... uh... TODO: logging... framework... time?
				position = v(0,0)
			else:
				# if the owner has a position component, fall through to that.
				# TODO: more full-featured fallthrough behavior
				position = self.owner.position_component
		if isinstance(position, v):
			position = PositionComponent(owner=self.owner, position=position)
		if isinstance(position, PositionComponent):
			self.position_component = position
		
		self.priority=priority
	
	def update(self, timestep=0):
		"""Update code may be required for renderables to, for example, update their position for bounds checks."""
		self.x_pos, self.y_pos = self.position_component.position.xytuple()
		self.x_min, self.x_max = self.x_pos, self.x_pos
		self.y_min, self.y_max = self.y_pos, self.y_pos
	def draw(self):
		"""Draw in the current state."""
		pass

class ShapeRenderer(Renderable):
	"""A component which draws the attached shape With a color.
	
	This is heavily entwined with the `shape` library/components. They actually store their vertex lists; this just tells opengl when and where (and what color) to draw them.
	This component requires a `shape`."""
	def __init__(self, shape=None, z=0, color=None, *args, **keyword_args):
		super().__init__(*args, **keyword_args)

		if shape is None:
			if hasattr(self.owner, 'shape'):
				shape = self.owner.shape
			else:
				shape = shapes.Point()
		self.shape = shape

		self.color = color or (0, 0, 0, 1)
		self.z = z
		self.update()

	@property
	def color(self): return self._color
	@color.setter
	def color(self, value): self._color = value if len(value) is 4 else value + (1.0,)

	def update(self, timestep=0):
		super().update(timestep)
		self.x_min = self.x_pos + self.shape.xbounds[0]
		self.x_max = self.x_pos + self.shape.xbounds[1]
		self.y_min = self.y_pos + self.shape.ybounds[0]
		self.y_max = self.y_pos + self.shape.ybounds[1]

	def draw(self):
		opengl.glColor4f(*self._color)
		self.shape.draw(self.position_component.position, self.z)
