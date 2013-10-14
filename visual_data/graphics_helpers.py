#enter = glPushMatrix
#exit = glPopMatrix

class Transformation():
	"""A context for opengl transformations.

	The Old Way:
	glPushMatrix()
	glTransform3f(6.0, 7.0, 5.0)
	glRotate4f(10.0, 0.0, 0.0, 1.0)
	draw_model()
	glPopMatrix()

	The New Way:
	with transformation(glTransform3f, 6.0, 7.0, 5.0), transformation(glRotate4f, 10.0, 0.0, 0.0, 1.0):
		draw_model()
	# done!"""
	def __init__(self, function, *arguments, **keywords):
		self.function = function
		self.arguments = arguments
		self.keyword_arguments = keywords

	def __enter__(self):
		enter()
		return self.function(*self.arguments, **self.keyword_arguments)

	def __exit__(self, type, value, traceback):
		exit()