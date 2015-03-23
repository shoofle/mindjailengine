from vectors import v

class AbstractComponent(object):
	""" A component which describes one facet of an entity in a game world. """
	def __init__(self, owner=None, *positional_arguments, **keyword_args):
		self.owner = owner
		self.__dict__.update(keyword_args)

class BasicComponent(AbstractComponent):
	def __init__(self, screen=None, dead=False, *args, **keyword_args):
		super(BasicComponent, self).__init__(*args, **keyword_args)
		self.parent_screen = screen
		self.dead = dead
	def update(self, timestep): pass

def attach_basic(target, *arguments, **keyword_arguments):
	target.basic_component = BasicComponent(*arguments, **keyword_arguments)

class PositionComponent(AbstractComponent):
	def __init__(self, position=None, *args, **keyword_args):
		super(PositionComponent, self).__init__(*args, **keyword_args)
		self.position = position or v(0,0)

def attach_position(target, *arguments, **keyword_arguments):
	target.position_component = PositionComponent(*arguments, **keyword_arguments)
# TODO: keep writing these attach functions, I guess
