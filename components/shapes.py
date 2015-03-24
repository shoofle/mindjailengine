import pyglet
from pyglet import gl, graphics

import math
from vectors import v
from .base_components import PositionComponent, AbstractComponent

d = 3
defaultTS = 0.04
# This is probably really awful, I guess. This is like a fake enum. I feel kinda dirty.
SHAPE_CIRCLE = 1
SHAPE_LINE = 2
SHAPE_RECTANGLE = 3
SHAPE_POINT = 4
""" Collisions! And shapes!
This file defines the behavior of various shape objects, which, as the name implies, describe the shapes of objects within the world.
This is heavily relied on for collision detection - the intersect(me, you) function, which takes two objects with "shape" attributes,
  is used for all collision detection.
The only collision that is particularly robust is circle/circle collisions. The circle/circle code can handle inverted circles, and also extrapolates based on velocities.
In the future, this module is going to be used for nothing but collision detection. Graphics should be offloaded to files, except maybe for debug purposes.
"""

# TODO: implement collision with circles such that circles are represented as extruded circles, so that they cannot move through objects at high speed.

def intersect(me, you):
	"""This function takes two objects and returns, uh, the smallest vector to fix their intersection. """
	#if not hasattr(me, "shape"): pass
	#if not hasattr(you, "shape"): pass
	# Switch to use isinstance?
	if me.name == SHAPE_CIRCLE:
		if you.name == SHAPE_CIRCLE: return circlecircle(me, you)
		if you.name == SHAPE_LINE: return circleline(me, you)
		if you.name == SHAPE_RECTANGLE: return circlerect(me, you)
		if you.name == SHAPE_POINT: return circlepoint(me, you)
	if me.name == SHAPE_LINE:
		if you.name == SHAPE_CIRCLE: return linecircle(me, you)
		if you.name == SHAPE_LINE: return None
		if you.name == SHAPE_RECTANGLE: return None
		if you.name == SHAPE_POINT: return linepoint(me, you)
	if me.name == SHAPE_RECTANGLE:
		if you.name == SHAPE_CIRCLE: return rectcircle(me, you)
		if you.name == SHAPE_LINE: return None
		if you.name == SHAPE_RECTANGLE: return rectrect(me, you)
		if you.name == SHAPE_POINT: return rectpoint(me, you)
	if me.name == SHAPE_POINT:
		if you.name == SHAPE_CIRCLE: return pointcircle(me, you)
		if you.name == SHAPE_LINE: return pointline(me, you)
		if you.name == SHAPE_RECTANGLE: return pointrect(me, you)
		if you.name == SHAPE_POINT: return pointpoint(me, you)

def reverse_test(function):
	""" Utility to create an reversed collision test function.

	e.g., if you pass it a circle-rect collision function, it will return a rect-circle collision function. This just
	passes the output through if it's None and inverts it otherwise."""
	def new_func(shape_one, shape_two, *args, **kwargs):
		output = function(shape_two, shape_one, *args, **kwargs)
		return -output if output else None
		#if output is not None:
		#	return -output
		#return None
	new_func.__doc__ = function.__doc__
	new_func.__name__ = "reverse_" + function.__name__
	return new_func

def steal_docstring(to_function, from_function):
	"""Prepends the docstring from function_two to the docstring for function_one."""
	to_function.__doc__ = from_function.__doc__ + (to_function.__doc__ or "")





def circlecircle(me,you):
	"""If I am intersecting you, find the shortest vector by which to change my position to no longer be intersecting.
	
	This function takes two objects with shape attributes. It checks to see if they are colliding and returns the shortest vector by which to move the object `me`, to remedy the collision.
	If the objects do not collide, it returns None.
	"""
	separation = you.position_component.position - me.position_component.position # The vector from me to you.
	if separation.x == 0 and separation.y == 0:
		separation_direction = v(0,-1)
		separation_distance = 0
	else:
		separation_direction = separation.unit()
		separation_distance = abs(separation)

	my_extents = (-me.radius, me.radius)
	your_extents = (-you.radius, you.radius)
	
	output = compare_interval( my_extents, your_extents, separation_distance)

	if output is None : return None
	return output*separation_direction

def lineline(me, you): # TODO: write this test.
	return None
steal_docstring(to_function=lineline, from_function=circlecircle)

def linecircle(line, circle):
	separation = line.position_component.position - circle.position_component.position
	
	# TODO: Clean this up to be more readable, especially in the end bit.
	# Comes from http://blog.generalrelativity.org/actionscript-30/collision-detection-circleline-segment-circlecapsule/ , pretty much.

	# factor holds the location along the line's central axis of the closest point to the circle.
	factor = (-separation).projs(line.v)
	if factor < 0: factor = 0 
	if factor > abs(line.v): factor = abs(line.v)

	# Newsep is the distance from the center of the circle to the closest point on the axis of the line.
	separation = (line.position_component.position + factor*line.v.unit()) - circle.position_component.position

	# Now we've got the newsep, which is the vector from the closest point on the line to the circle's center.
	# If abs(newsep) is 0, then output should be circle.rad
	# If abs(newsep) is circle.rad, then output should be 0.
	if separation.x == 0 and separation.y == 0:
		return -line.v.unit() * (circle.radius + line.thickness)
	#if abs(separation) < circle.rad + defaultTS*abs(circleobj.vel*line.normal) + line.thickness:
	if abs(separation) < circle.radius + line.thickness:
		# If the separation is less than the combination of circle radius, line radius, and the perpendicular component of the circle's velocity...
		#return separation.unit() * (circle.rad + defaultTS*abs(circleobj.vel*line.normal) + line.thickness - abs(separation))
		return separation.unit() * (circle.radius + line.thickness - abs(separation))
	return None
circleline = reverse_test(linecircle)
steal_docstring(to_function=linecircle, from_function=circlecircle)
steal_docstring(to_function=circleline, from_function=circlecircle)


def rectrect(me, you):
	separation = you.position_component.position - me.position_component.position
	x = compare_interval(me.xbounds, you.xbounds, separation.x)
	y = compare_interval(me.ybounds, you.ybounds, separation.y)
	if x is None or y is None: 
		return None
	if abs(x) < abs(y):
		return v(x, 0)
	else:
		return v(0, y)
steal_docstring(to_function=rectrect, from_function=circlecircle)

def rectcircle(me, you):
	rect_min_corner = v(me.xbounds[0], me.ybounds[0]) + me.position_component.position
	rect_max_corner = v(me.xbounds[1], me.ybounds[1]) + me.position_component.position
	rect_center = (rect_min_corner + rect_max_corner) / 2

	displacement = you.position_component.position - me.position_component.position
	if displacement.x < me.xbounds[0]:
		edge_x = -1
	elif me.xbounds[0] < displacement.x < me.xbounds[1]:
		edge_x = 0
	elif me.xbounds[1] < displacement.x:
		edge_x = +1
	
	if displacement.y < me.ybounds[0]:
		edge_y = -1
	elif me.ybounds[0] < displacement.y < me.ybounds[1]:
		edge_y = 0
	elif me.ybounds[1] < displacement.y:
		edge_y = +1
	
	if abs(edge_x) == 1 and abs(edge_y) == 1:
		x = rect_min_corner.x if edge_x < 0 else rect_max_corner.x
		y = rect_min_corner.y if edge_y < 0 else rect_max_corner.y
		corner = v(x, y)

		vect = you.position_component.position - corner
		if abs(vect) < you.radius:
			return vect.unit() * (you.radius - abs(vect))
		else:
			return None

	x_vect = compare_interval(me.xbounds, you.xbounds, displacement.x)
	y_vect = compare_interval(me.ybounds, you.ybounds, displacement.y)

	if x_vect is not None and y_vect is not None:
		if abs(x_vect) > abs(y_vect):
			return v(x_vect, 0)
		else:
			return v(0, y_vect)
	elif x_vect is not None:
		return v(x_vect, 0)
	elif y_vect is not None:
		return v(0, y_vect)
circlerect = reverse_test(rectcircle)
steal_docstring(to_function=rectcircle, from_function=circlecircle)
steal_docstring(to_function=circlerect, from_function=circlecircle)

def rectline(rect, line): # TODO: write this test
	return None
linerect = reverse_test(rectline)
steal_docstring(to_function=rectline, from_function=circlecircle)
steal_docstring(to_function=linerect, from_function=circlecircle)


def pointpoint(me, you):
	return v(0,1) if me.position_component.position == you.position_component.position else None
steal_docstring(to_function=pointpoint, from_function=circlecircle)

def circlepoint(me, you):
	difference = you.position_component.position - me.position_component.position
	if abs(difference) < me.radius:
		return difference.unit()*(abs(difference) - me.radius)
pointcircle = reverse_test(circlepoint)
steal_docstring(to_function=circlepoint, from_function=circlecircle)
steal_docstring(to_function=pointcircle, from_function=circlecircle)

def linepoint(line, point):
	separation = line.position_component.position - point.position_component.position
	
	# TODO: Clean this up to be more readable, especially in the end bit.
	# Comes from http://blog.generalrelativity.org/actionscript-30/collision-detection-circleline-segment-circlecapsule/ , pretty much.

	# factor holds the location along the line's central axis of the closest point to the circle.
	factor = (-separation).projs(line.v)
	if factor < 0: factor = 0 
	if factor > abs(line.v): factor = abs(line.v)

	separation = (line.position_component.position + factor*line.v.unit()) - point.position_component.position

	# If abs(separation) is 0, then output should be thickness.
	# If abs(separation) is thickness, then output should be 0.
	if separation.x == 0 and separation.y == 0:
		return -line.v.unit() * line.thickness
	#if abs(separation) < circle.rad + defaultTS*abs(circleobj.vel*line.normal) + line.thickness:
	if abs(separation) < line.thickness:
		# If the separation is less than the combination of circle radius, line radius, and the perpendicular component of the circle's velocity...
		#return separation.unit() * (circle.rad + defaultTS*abs(circleobj.vel*line.normal) + line.thickness - abs(separation))
		return separation.unit() * (line.thickness - abs(separation))
	return None
pointline = reverse_test(linepoint)
steal_docstring(to_function=linepoint, from_function=circlecircle)
steal_docstring(to_function=pointline, from_function=circlecircle)

def rectpoint(me, you):
	my_min = v(me.xbounds[0], me.ybounds[0]) + me.position_component.position
	my_max = v(me.xbounds[1], me.ybounds[1]) + me.position_component.position
	you_pos = you.position_component.position
	center = (my_min + my_max) / 2
	vect = you_pos - center

	if my_min.x < you_pos.x < my_max.x and my_min.y < you_pos.y < my_max.y:
		if abs(vect.x) < abs(vect.y):
			if vect.x > 0:
				return v(you_pos.x - me.xbounds[1], 0)
			else:
				return v(you_pos.x - me.xbounds[0], 0)
		else:
			if vect.y > 0:
				return v(0, you_pos.y - me.ybounds[1])
			else:
				return v(0, you_pos.y - me.ybounds[0])
pointrect = reverse_test(rectpoint)
steal_docstring(to_function=rectpoint, from_function=circlecircle)
steal_docstring(to_function=pointrect, from_function=circlecircle)


def compare_interval(extentsme, extentsother, msep, me_inverted = False, other_inverted = False):
	"""Returns the amount by which to move 'me' to ensure that two (1D) intervals are no longer intersecting, or none if they're already fine.
	
	extentsme and extentsother are tuples of left and right extents. 
	msep is the amount by which their centers are separated.
	me_inverted and other_inverted are flags - if they're set, then different logic is used.
	"""
	my_left, my_right = extentsme
	your_left, your_right = extentsother[0]+msep, extentsother[1]+msep

	#Possibilities:
	# If neither of us are inverted, then it's like this:		[a	{c	b]	d}   then our options are a and d or b and c.
	if not me_inverted and not other_inverted:
		if (my_left > your_right or my_right < your_left): return None
		return min(your_left - my_right, your_right - my_left, key=abs)
	# If I'm inverted and he's not, then it's like this:		]a	b[	{c	d}   then we need to move to align b and d, or a and c.
	elif me_inverted and not other_inverted:
		if (my_left < your_left and my_right > your_right) : return None
		return min(your_right - my_right, your_left - my_left, key=abs)
	# If I'm he's inverted and I'm not, then it's like this:	[a	b]	}c	d{   then we need to move to align b and d, or a and c.
	elif not me_inverted and other_inverted:
		if (my_left > your_left and my_right < your_right): return None
		return min(your_right - my_right, your_left - my_left, key=abs)
	# If we're both inverted, then it's like this:				]a	b[	}c	d{   then there's nothing we can do.
	elif me_inverted and other_inverted:
		return None


def point_in_object(vect, obj):
	""" Test if a point (specified by a vector) is within with a given object. """
	point = Point(position=vect)
	if intersects(point, obj):
		return True
	else:
		return False


class Shape(AbstractComponent):
	""" An abstract "shape" component. """
	def __init__(self, position = None, *args, **kwargs):
		super().__init__(*args, **kwargs)

		new_position = None
		if position is None:
			if self.owner is not None:
				if hasattr(self.owner, 'position_component'):
					new_position = self.owner.position_component
			else:
				new_position = PositionComponent(owner=self)
		elif isinstance(position, v):
			new_position = PositionComponent(owner=self, position=position)
		elif isinstance(position, PositionComponent):
			new_position = position

		self.position_component = new_position

		self.name = None

class Point(Shape):
	""" Just a point. """
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		self.name = SHAPE_POINT
		self.xbounds, self.ybounds = (0, 0), (0, 0)

class Line(Shape):
	""" A line, potentially with rounded ends. """
	def __init__(self, vector=v(1,0), thickness=0, draw_type=None, num_points = 9, depth=20, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		self.name = SHAPE_LINE
		self.v = vector
		self.normal = self.v.rperp().unit()
		self.length = abs(vector)
		self.thickness = thickness
		self.angle = math.atan2(vector.y, vector.x)

		self.drawtype = draw_type

		# Build the vertex list.
		if thickness == 0:
			self.drawtype = draw_type or "oneline"

			self.vertex_list = pyglet.graphics.vertex_list(2, 'v3f')
			self.vertex_list.vertices = [0, 0, 0, vector.x, vector.y, 0]
		else:
			self.drawtype = draw_type or "lines"

			self.vertex_list = pyglet.graphics.vertex_list(4+2*num_points,'v3f')

			# For the record, here's the logic of this vertex-generation code:
			# We start at `thickness` distance out on the x-axis. Then, we travel up on the y-axis a distance of self.length. This is the first sidewall of the capsule shape.
			self.vertex_list.vertices[0:d*1] = [thickness, 0.0, 0.0]
			self.vertex_list.vertices[d*1:d*2] = [thickness, self.length, 0.0]

			# Next, we draw the far end cap.
			# This starts at the specified thickness away from the end anchor of the line, pointing in the direction of the positive x-axis. It proceeds counterclockwise around until it arrives at the location on the other side of the x-axis.
			for i in range(num_points):
				self.vertex_list.vertices[d*2+d*i:d*3+d*i] = [
					thickness*math.cos(math.pi*(i+1)/num_points),
					self.length + thickness*math.sin(math.pi*(i+1)/num_points),
					0.0]

			# A vertical connection is next, vertically back down to the negative x-axis.
			self.vertex_list.vertices[d*(num_points+2):d*(num_points+3)] = [-thickness, self.length, 0.0]
			self.vertex_list.vertices[d*(num_points+3):d*(num_points+4)] = [-thickness, 0.0, 0.0]

			# And again we proceed in a half-circle, this time around the origin, to draw the near end cap.
			for i in range(num_points):
				self.vertex_list.vertices[d*(num_points+4+i):d*(num_points+4+i+1)] = [
					-thickness*math.cos(math.pi*(i+1)/num_points),
					-thickness*math.sin(math.pi*(i+1)/num_points),
					0.0]

			self.drawtype = "3d"

		self.vertex_lists_3d = make_3d(self.vertex_list, depth)

		# Define the bounds.
		self.xbounds = ( min(0,vector.x)-thickness, max(0,vector.x)+thickness )
		self.ybounds = ( min(0,vector.y)-thickness, max(0,vector.y)+thickness )
	def draw(self, location, z=0):
		pyglet.gl.glPushMatrix()
		pyglet.gl.glTranslatef(location.x,location.y,z)

		if self.thickness is not 0:
			pyglet.gl.glRotatef(self.angle*180.0/math.pi - 90, 0.0, 0.0, 1.0)

		if self.drawtype is "outlined":
			pyglet.gl.glColor3f(1.0,1.0,1.0)
			self.vertex_list.draw(pyglet.gl.GL_POLYGON)
			pyglet.gl.glColor3f(0.0,0.0,0.0)
			self.vertex_list.draw(pyglet.gl.GL_LINE_LOOP)
		elif self.drawtype is "3d":
			for l in self.vertex_lists_3d: l[0].draw(l[1])
		elif self.drawtype == "points" :
			self.vertex_list.draw(pyglet.gl.GL_POINTS)
		elif self.drawtype == "lines" :
			self.vertex_list.draw(pyglet.gl.GL_LINE_LOOP)
		elif self.drawtype == "oneline" :
			self.vertex_list.draw(pyglet.gl.GL_LINE_STRIP)
		elif self.drawtype == "fill" :
			self.vertex_list.draw(pyglet.gl.GL_POLYGON)
		else: 
			self.vertex_list.draw(self.drawtype)

		pyglet.gl.glPopMatrix()

class Circle(Shape):
	""" A simple circle. """
	def __init__(self, num_points = 30, rad = 30, drawtype = "lines", invert = False, depth=20, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		self.name = SHAPE_CIRCLE
		self.vertex_list = pyglet.graphics.vertex_list(num_points,'v3f')
		self.radius=rad
		self.drawtype = drawtype
		self.invert = invert

		# Build the vertex list.
		for i in range(num_points):
			self.vertex_list.vertices[d*i:d*(i+1)] = [math.cos(i*2*math.pi/num_points), math.sin(i*2*math.pi/num_points), 0]
		self.vertex_lists_3d = make_3d(self.vertex_list, depth)

		# Define the bounds.
		self.xbounds = (-rad, rad)
		self.ybounds = (-rad, rad)
	def draw(self, location=None, z=0):
		""" Draws the polygon at the provided location, scaled by self.r, rotated self.rot. """
		pyglet.gl.glPushMatrix()
		pyglet.gl.glTranslatef(location.x, location.y, z)
		pyglet.gl.glScalef(self.radius, self.radius, 1.0)
		if self.drawtype is "outlined":
			pyglet.gl.glColor3f(1.0,1.0,1.0)
			self.vertex_list.draw(pyglet.gl.GL_POLYGON)
			pyglet.gl.glColor3f(0.0,0.0,0.0)
			self.vertex_list.draw(pyglet.gl.GL_LINE_LOOP)
		elif self.drawtype is "3d":
			for l in self.vertex_lists_3d: l[0].draw(l[1])
		elif self.drawtype == "points" :
			self.vertex_list.draw(pyglet.gl.GL_POINTS)
		elif self.drawtype == "lines" :
			self.vertex_list.draw(pyglet.gl.GL_LINE_LOOP)
		elif self.drawtype == "oneline" :
			self.vertex_list.draw(pyglet.gl.GL_LINE_STRIP)
		elif self.drawtype == "fill" :
			self.vertex_list.draw(pyglet.gl.GL_POLYGON)
		else: self.vertex_list.draw(self.drawtype)
		pyglet.gl.glPopMatrix()

class Rectangle(Shape):
	""" A rectangle. """
	def __init__(self, x_min, x_max, y_min, y_max, drawtype = "3d", depth=20, color=(1.0, 1.0, 1.0), *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.name = SHAPE_RECTANGLE
		self.drawtype = drawtype
		self.vertex_list = pyglet.graphics.vertex_list(4, 'v3f')

		self.vertex_list.vertices = [x_min, y_min, 0, x_max, y_min, 0, x_max, y_max, 0, x_min, y_max, 0]
		self.vertex_lists_3d = make_3d(self.vertex_list, depth)
		
		self.xbounds = (x_min, x_max)
		self.ybounds = (y_min, y_max)
	def draw(self, location=None, z=0):
		pyglet.gl.glPushMatrix()
		pyglet.gl.glTranslatef(location.x, location.y, z)
		if self.drawtype is "outlined":
			pyglet.gl.glColor3f(1.0,1.0,1.0)
			self.vertex_list.draw(pyglet.gl.GL_POLYGON)
			pyglet.gl.glColor3f(0.0,0.0,0.0)
			self.vertex_list.draw(pyglet.gl.GL_LINE_LOOP)
		elif self.drawtype is "3d":
			for face in self.vertex_lists_3d: face[0].draw(face[1])
		elif self.drawtype == "points" :
			self.vertex_list.draw(pyglet.gl.GL_POINTS)
		elif self.drawtype == "lines" :
			self.vertex_list.draw(pyglet.gl.GL_LINE_LOOP)
		elif self.drawtype == "oneline" :
			self.vertex_list.draw(pyglet.gl.GL_LINE_STRIP)
		elif self.drawtype == "fill" :
			self.vertex_list.draw(pyglet.gl.GL_POLYGON)
		else: self.vertex_list.draw(self.drawtype)
		pyglet.gl.glPopMatrix()


def make_3d(vertex_list, depth, edge_color=(0.1,0.1,0.1), cap_color=(0.8,0.8,0.8)):
	num_vertices = int(len(vertex_list.vertices)/3)
	vertex_list_3d = pyglet.graphics.vertex_list(2*num_vertices + 2, 'v3f', 'c3f')
	for i in range(num_vertices):
		start = i*2*3
		verts1, verts2 = vertex_list.vertices[i*3:(i+1)*3], vertex_list.vertices[i*3:(i+1)*3]
		verts1[2] -= depth/2.0
		verts2[2] += depth/2.0
		vertex_list_3d.vertices[start:start+3], vertex_list_3d.vertices[start+3:start+6] = verts1, verts2
	end = (len(vertex_list.vertices)-3)*2
	vertex_list_3d.vertices[end:end+3] = vertex_list.vertices[0:3]
	vertex_list_3d.vertices[end+3:end+6] = vertex_list.vertices[0:3]
	vertex_list_3d.vertices[end+2] -= depth/2.0
	vertex_list_3d.vertices[end+2+3] += depth/2.0
	vertex_list_3d.colors = edge_color*(2*num_vertices+2)

	back_cap = pyglet.graphics.vertex_list(num_vertices, 'v3f', 'c3f')
	back_cap.vertices, back_cap.colors = vertex_list.vertices, cap_color*num_vertices
	front_cap = pyglet.graphics.vertex_list(num_vertices, 'v3f', 'c3f')
	front_cap.vertices, front_cap.colors = vertex_list.vertices, cap_color*num_vertices
	for i in range(num_vertices):
		back_cap.vertices[3*i+2] -= depth/2
		front_cap.vertices[3*i+2] += depth/2

	return (vertex_list_3d, pyglet.gl.GL_TRIANGLE_STRIP), (back_cap, pyglet.gl.GL_POLYGON), (front_cap, pyglet.gl.GL_POLYGON)
