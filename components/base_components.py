from vectors import v

class AbstractComponent(object):
	""" A component describes one facet of one entity in a game world. """
	def __init__(self, owner=None):
		self.owner = owner

class Lifecycle(AbstractComponent):
	"""Every object should have a Lifecycle. It basically centralizes access to the containing screen as well as knowing whether it's dead or not."""
	def __init__(self, screen=None, dead=False, *arguments, **keyword_args):
		super().__init__(*arguments, **keyword_args)
		self.parent_screen = screen
		self.dead = dead
	def update(self, timestep): pass

class PositionComponent(AbstractComponent):
	def __init__(self, position=None, *arguments, **keyword_args):
		super().__init__(*arguments, **keyword_args)
		self.position = position or v(0,0)

