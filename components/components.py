from vectors import v
from pyglet import gl as opengl
from . import shapes
from .base_components import *

class Renderable(AbstractComponent):
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
