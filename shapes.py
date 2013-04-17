#!/usr/bin/env python

import pyglet
from pyglet import gl, graphics

import math
from vectors import v

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
The only collision that is particularly robust is circle/circle collisions. The circle/circle code can handle inverted circles, and also
  extrapolates based on velocities.
In the future, this module is going to be used for nothing but collision detection. Graphics should be offloaded to files, except maybe for debug purposes.
"""

# TODO: implement collision with circles such that circles are represented as extruded circles, so that they cannot move through objects at high speed.

def intersect(me, you):
	"""This function takes two objects and returns, uh, the smallest vector to fix their intersection. """
#	if not hasattr(me, "shape"): pass
#	if not hasattr(you, "shape"): pass
	if me.shape.name is SHAPE_CIRCLE and you.shape.name is SHAPE_CIRCLE:
		return circlecircle(me,you)
	if me.shape.name is SHAPE_LINE and you.shape.name is SHAPE_CIRCLE:
		return linecircle(me,you)
	if me.shape.name is SHAPE_CIRCLE and you.shape.name is SHAPE_LINE:
		output = linecircle(you,me)
		return -output if output is not None else None
	# TODO: rectangle-circle collisions
	if me.shape.name is SHAPE_RECTANGLE and you.shape.name is SHAPE_CIRCLE:
		return None
	if me.shape.name is SHAPE_CIRCLE and you.shape.name is SHAPE_RECTANGLE:
		return None
	# TODO: (point, rectangle, circle, line) collisions. make them all work.
#		output = None
#		return -output if output is not None else None

def linecircle(lineobj, circleobj):
	"""If I am intersecting you, find the shortest vector by which to change my position to no longer be intersecting.
	
	This function takes two objects with shape attributes, the first of which is a line. It checks to see if they are colliding, 
	  not taking into account velocity particularly well, and returns the shortest vector by which to move the circle to remedy 
	  the collision.
	If the objects do not collide, it returns None.
	"""
	# TODO: Clean this up to be more readable, especially in the end bit.
	# Comes from http://blog.generalrelativity.org/actionscript-30/collision-detection-circleline-segment-circlecapsule/ , pretty much.
	separation = lineobj.position_component.position - circleobj.position_component.position
	line = lineobj.shape
	circle = circleobj.shape

	# factor holds the location along the line's central axis of the closest point to the circle.
	factor = (-separation).projs(line.v)
	if factor < 0: factor = 0 
	if factor > abs(line.v): factor = abs(line.v)

	# Newsep is the distance from the center of the circle to the closest point on the axis of the line.
	separation = (lineobj.position_component.position + factor*line.v.unit()) - circleobj.position_component.position

	# Now we've got the newsep, which is the vector from the closest point on the line to the circle's center.
	# If abs(newsep) is 0, then output should be circle.rad
	# If abs(newsep) is circle.rad, then output should be 0.
	if separation.x == 0 and separation.y == 0:
		return -line.v.unit() * (circle.rad + line.thickness)
	#if abs(separation) < circle.rad + defaultTS*abs(circleobj.vel*line.normal) + line.thickness:
	if abs(separation) < circle.rad + line.thickness:
		# If the separation is less than the combination of circle radius, line radius, and the perpendicular component of the circle's velocity...
		#return separation.unit() * (circle.rad + defaultTS*abs(circleobj.vel*line.normal) + line.thickness - abs(separation))
		return separation.unit() * (circle.rad + line.thickness - abs(separation))
	return None

def circlecircle(me,you):
	"""If I am intersecting you, find the shortest vector by which to change my position to no longer be intersecting.
	
	This function takes two objects with shape attributes. It checks to see if they are colliding, extrapolating their positions
	  based on current velocities and a default timestep, and returns the shortest vector by which to move the object `me`, to 
	  remedy the collision.
	If the objects do not collide, it returns None.
	"""
	separation = you.position_component.position - me.position_component.position # The vector from me to you.
	if separation.x == 0 and separation.y == 0:
		unit_separation = v(0,-1)
		separation_magnitude = 0
	else:
		separation_magnitude = abs(separation)
		unit_separation = separation.unit()

	ts = defaultTS
	# TODO: Decide whether to leave in velocity corrections.
	#if hasattr(me, "vel"): my_extents = (-me.shape.rad - ts*(me.vel*unit_separation), me.shape.rad - ts*(me.vel*unit_separation))
	#else: 
	my_extents = (-me.shape.rad, me.shape.rad)
	#if hasattr(you, "vel"): your_extents = (-you.shape.rad + ts*(you.vel*unit_separation), you.shape.rad + ts*(you.vel*unit_separation))
	#else: 
	your_extents = (-you.shape.rad, you.shape.rad)
	
	output = intervalcompare(my_extents, your_extents, separation_magnitude, me.shape.invert , you.shape.invert )

	if output is None : return None
	return output*unit_separation 

def intervalcompare(extentsme, extentsother, msep, me_inverted = False, other_inverted = False):
	"""Returns the amount by which to move 'me' to ensure that two (1D) intervals are no longer intersecting, or none if they're already fine.
	
	extentsme and extentsother are tuples of left and right extents. 
	msep is the amount by which their centers are separated.
	me_inverted and other_inverted are flags - if they're set, then different logic is used.
	"""
	my_left, my_right = extentsme
	your_left, your_right = extentsother[0]+msep, extentsother[1]+msep

# Got bored. Decided to pack this down. Don't use this, it's unreadable pretty much by intent.
#	mi, yi = me_inverted, other_inverted
#	ml, mr, yl, yr = my_left, my_right, your_left, your_right
#	if not mi and not yi and not (ml>yr or mr<yl): return min(yl-mr, yr-ml, key=abs)
#	elif mi and not yi and not (ml<yl and mr>yr): return min(yr-mr, yl-ml, key=abs)
#	elif not mi and yi and not (ml>yl and mr<yr): return min(yr-mr, yl-ml, key=abs)
#	return None

	#Possibilities:
	# If we're both inverted, then it's like this:				]a	b[	}c	d{   then there's nothing we can do.
	if me_inverted and other_inverted:
		return None
	# If I'm inverted and he's not, then it's like this:		]a	b[	{c	d}   then we need to move to align b and d, or a and c.
	elif me_inverted and not other_inverted:
		if (my_left < your_left and my_right > your_right) : return None
		return min(your_right - my_right, your_left - my_left, key=abs)
	# If I'm he's inverted and I'm not, then it's like this:	[a	b]	}c	d{   then we need to move to align b and d, or a and c.
	elif not me_inverted and other_inverted:
		if (my_left > your_left and my_right < your_right): return None
		return min(your_right - my_right, your_left - my_left, key=abs)
	# If neither of us are inverted, then it's like this:		[a	{c	b]	d}   then our options are a and d or b and c.
	elif not me_inverted and not other_inverted:
		if (my_left > your_right or my_right < your_left): return None
		return min(your_left - my_right, your_right - my_left, key=abs)

class Point(object):
	""" Just a point. """
	def __init__(self, *args, **kwargs):
		self.name = SHAPE_POINT
		self.xbounds, self.ybounds = (0, 0), (0, 0)

class Line(object):
	""" A line, potentially with rounded ends. """
	def __init__(self, vector, thickness=0, draw_type=None, num_points = 9, depth=20):
		self.name = SHAPE_LINE
		self.v = vector
		self.normal = self.v.rperp().unit()
		self.length = abs(vector)
		self.thickness = thickness
		self.angle = math.atan2(vector.y, vector.x)

		self.drawtype = draw_type

		# Build the vertex list.
		if thickness == 0:
			if draw_type is None: self.drawtype = "oneline"

			self.vlist = pyglet.graphics.vertex_list(2,'v3f')
			self.vlist.vertices = [0, 0, 0, vector.x, vector.y, 0]
		else:
			if draw_type is None: self.drawtype = "lines"

			self.vlist = pyglet.graphics.vertex_list(22,'v3f')
			self.vlist.vertices[0:d*1] = [thickness, 0.0, 0.0]
			self.vlist.vertices[d*1:d*2] = [thickness, self.length, 0.0]
			for i in range(9):
				self.vlist.vertices[d*2+d*i:d*3+d*i] = [thickness*math.cos(math.pi*(i+1)/num_points), \
														self.length + thickness*math.sin(math.pi*(i+1)/num_points), \
														0.0]
			self.vlist.vertices[d*(9+2):d*(9+3)] = [-thickness,self.length, 0.0]
			self.vlist.vertices[d*(9+3):d*(9+4)] = [-thickness,0.0, 0.0]
			for i in range(9):
				self.vlist.vertices[d*(9+4)+d*i:d*(9+4)+d*(i+1)] = [-thickness*math.cos(math.pi*(i+1)/num_points), \
																	-thickness*math.sin(math.pi*(i+1)/num_points), \
																	0.0]
			self.drawtype = "3d"

		self.vertex_lists_3d = make_3d(self.vlist, depth)

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
			self.vlist.draw(pyglet.gl.GL_POLYGON)
			pyglet.gl.glColor3f(0.0,0.0,0.0)
			self.vlist.draw(pyglet.gl.GL_LINE_LOOP)
		elif self.drawtype is "3d":
			for l in self.vertex_lists_3d: l[0].draw(l[1])
		elif self.drawtype == "points" :
			self.vlist.draw(pyglet.gl.GL_POINTS)
		elif self.drawtype == "lines" :
			self.vlist.draw(pyglet.gl.GL_LINE_LOOP)
		elif self.drawtype == "oneline" :
			self.vlist.draw(pyglet.gl.GL_LINE_STRIP)
		elif self.drawtype == "fill" :
			self.vlist.draw(pyglet.gl.GL_POLYGON)
		else: 
			self.vlist.draw(self.drawtype)

		pyglet.gl.glPopMatrix()

class Circle(object):
	""" Makes a circle object, which has simplified extents/projection code.
	Displays as a polygon with numpoints points.  Dynamic or fixed radius? For now, fixedish. or something.
	"""
	def __init__(self, numpoints = 30, rad = 30, drawtype = "lines", invert = False, depth=20):
		self.name = SHAPE_CIRCLE
		self.vlist = pyglet.graphics.vertex_list(numpoints,'v3f')
		self.rad=rad
		self.drawtype = drawtype
		self.invert = invert

		# Build the vertex list.
		for i in range(numpoints):
			self.vlist.vertices[d*i:d*(i+1)] = [math.cos(i*2*math.pi/numpoints), math.sin(i*2*math.pi/numpoints), 0]
		self.vertex_lists_3d = make_3d(self.vlist, depth)

		# Define the bounds.
		self.xbounds = (-rad, rad)
		self.ybounds = (-rad, rad)
	def draw(self, location=None, z=0):
		""" Draws the polygon at the polygon's self.x, self.y locations, scaled by self.r, rotated self.rot. """
		pyglet.gl.glPushMatrix()
		pyglet.gl.glTranslatef(location.x,location.y,z)
		pyglet.gl.glScalef(self.rad,self.rad,1.0)
		if self.drawtype is "outlined":
			pyglet.gl.glColor3f(1.0,1.0,1.0)
			self.vlist.draw(pyglet.gl.GL_POLYGON)
			pyglet.gl.glColor3f(0.0,0.0,0.0)
			self.vlist.draw(pyglet.gl.GL_LINE_LOOP)
		elif self.drawtype is "3d":
			for l in self.vertex_lists_3d: l[0].draw(l[1])
		elif self.drawtype == "points" :
			self.vlist.draw(pyglet.gl.GL_POINTS)
		elif self.drawtype == "lines" :
			self.vlist.draw(pyglet.gl.GL_LINE_LOOP)
		elif self.drawtype == "oneline" :
			self.vlist.draw(pyglet.gl.GL_LINE_STRIP)
		elif self.drawtype == "fill" :
			self.vlist.draw(pyglet.gl.GL_POLYGON)
		else: self.vlist.draw(self.drawtype)
		pyglet.gl.glPopMatrix()

class Rectangle(object):
	""" A rectangle. """
	def __init__(self, x_min, x_max, y_min, y_max, drawtype = "3d", depth=20, color=(1.0, 1.0, 1.0)):
		self.name = SHAPE_RECTANGLE
		self.drawtype = drawtype
		self.vlist = pyglet.graphics.vertex_list(4, 'v3f')

		self.vlist.vertices = [x_min, y_min, 0, x_max, y_min, 0, x_max, y_max, 0, x_min, y_max, 0]
		vertex_lists_3d = make_3d(self.vlist, depth)
		
		self.xbounds = (x_min, x_max)
		self.ybounds = (y_min, y_max)
	def draw(self, location=None, z=0):
		pyglet.gl.glPushMatrix()
		pyglet.gl.glTranslatef(location.x, location.y, z)
		if self.drawtype is "outlined":
			pyglet.gl.glColor3f(1.0,1.0,1.0)
			self.vlist.draw(pyglet.gl.GL_POLYGON)
			pyglet.gl.glColor3f(0.0,0.0,0.0)
			self.vlist.draw(pyglet.gl.GL_LINE_LOOP)
		elif self.drawtype is "3d":
			for l in self.vertex_lists_3d: l[0].draw(l[1])
		elif self.drawtype == "points" :
			self.vlist.draw(pyglet.gl.GL_POINTS)
		elif self.drawtype == "lines" :
			self.vlist.draw(pyglet.gl.GL_LINE_LOOP)
		elif self.drawtype == "oneline" :
			self.vlist.draw(pyglet.gl.GL_LINE_STRIP)
		elif self.drawtype == "fill" :
			self.vlist.draw(pyglet.gl.GL_POLYGON)
		else: self.vlist.draw(self.drawtype)
		pyglet.gl.glPopMatrix()


def make_3d(vlist, depth, edge_color=(0.1,0.1,0.1), cap_color=(0.8,0.8,0.8)):
	num_vertices = len(vlist.vertices)/3
	vlist_3d = pyglet.graphics.vertex_list(2*num_vertices + 2, 'v3f', 'c3f')
	for i in range(num_vertices):
		start = i*2*3
		verts1, verts2 = vlist.vertices[i*3:(i+1)*3], vlist.vertices[i*3:(i+1)*3]
		verts1[2] -= depth/2.0
		verts2[2] += depth/2.0
		vlist_3d.vertices[start:start+3], vlist_3d.vertices[start+3:start+6] = verts1, verts2
	end = (len(vlist.vertices)-3)*2
	vlist_3d.vertices[end:end+3] = vlist.vertices[0:3]
	vlist_3d.vertices[end+3:end+6] = vlist.vertices[0:3]
	vlist_3d.vertices[end+2] -= depth/2.0
	vlist_3d.vertices[end+2+3] += depth/2.0
	vlist_3d.colors = edge_color*(2*num_vertices+2)

	back_cap = pyglet.graphics.vertex_list(num_vertices, 'v3f', 'c3f')
	back_cap.vertices, back_cap.colors = vlist.vertices, cap_color*num_vertices
	front_cap = pyglet.graphics.vertex_list(num_vertices, 'v3f', 'c3f')
	front_cap.vertices, front_cap.colors = vlist.vertices, cap_color*num_vertices
	for i in range(num_vertices):
		back_cap.vertices[3*i+2] -= depth/2
		front_cap.vertices[3*i+2] += depth/2

	return (vlist_3d, pyglet.gl.GL_TRIANGLE_STRIP), (back_cap, pyglet.gl.GL_POLYGON), (front_cap, pyglet.gl.GL_POLYGON)
