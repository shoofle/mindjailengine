#!/usr/bin/env python

import pyglet
from pyglet import gl, graphics

import math
from vectors import v

d = 3
defaultTS = 0.04
SHAPE_LINE = 2
SHAPE_CIRCLE = 1
""" Collisions! And shapes!
This file defines the behavior of various shape objects, which, as the name implies, describe the shapes of objects within the world.
This is heavily relied on for collision detection - the intersect(me, you) function, which takes two objects with "shape" attributes,
  is used for all collision detection.
Furthermore, these functions are actually called significantly more often than they need to. This is, in the future, a major potential
  spot for optimization, given how often these are called.
The only collision that is particularly robust is circle/circle collisions. The circle/circle code can handle inverted circles, and also
  extrapolates based on velocities.
"""

# TODO: implement collision with circles such that circles are represented as extruded circles, so that they cannot move through objects at high speed.

def intersect(me, you):
	"""This function takes two objects and returns, uh, the smallest vector to fix their intersection. """
	if not hasattr(me, "shape"): pass
	if not hasattr(you, "shape"): pass
	if me.shape.name is SHAPE_CIRCLE and you.shape.name is SHAPE_CIRCLE:
		return circlecircle(me,you)
	if me.shape.name is SHAPE_LINE and you.shape.name is SHAPE_CIRCLE:
		return linecircle(me,you)
	if me.shape.name is SHAPE_CIRCLE and you.shape.name is SHAPE_LINE:
		output = linecircle(you,me)
		return -output if output is not None else None

def linecircle(lineobj, circleobj):
	"""If I am intersecting you, find the shortest vector by which to change my position to no longer be intersecting.
	
	This function takes two objects with shape attributes, the first of which is a line. It checks to see if they are colliding, 
	  not taking into account velocity particularly well, and returns the shortest vector by which to move the circle to remedy 
	  the collision.
	If the objects do not collide, it returns None.
	"""
	# TODO: Clean this up to be more readable, especially in the end bit.
	# Comes from http://blog.generalrelativity.org/actionscript-30/collision-detection-circleline-segment-circlecapsule/ , pretty much.
	sep = circleobj.pos - lineobj.pos
	line = lineobj.shape
	circle = circleobj.shape

	# factor holds the location along the line's central axis of the closest point to the circle.
	factor = sep.projs(line.v)
	if factor < 0: factor = 0 
	if factor > abs(line.v): factor = abs(line.v)

	# Newsep is the distance from the center of the circle to the closest point on the axis of the line.
	newsep = circleobj.pos - (lineobj.pos + factor*line.v.unit()) 

	# Now we've got the newsep, which is the vector from the closest point on the line to the circle's center.
	# If abs(newsep) is 0, then output should be circle.rad
	# If abs(newsep) is circle.rad, then output should be 0.
	if newsep.x == 0 and newsep.y == 0:
		return -line.v.unit() * (circle.rad + line.thickness)
	if abs(newsep) < circle.rad + defaultTS*abs(circleobj.vel*line.normal) + line.thickness:
		# If the separation is less than the combination of circle radius, line radius, and the perpendicular component of the circle's velocity...
		return newsep.unit() * (circle.rad + defaultTS*abs(circleobj.vel*line.normal) + line.thickness - abs(newsep))
	return None

def circlecircle(me,you):
	"""If I am intersecting you, find the shortest vector by which to change my position to no longer be intersecting.
	
	This function takes two objects with shape attributes. It checks to see if they are colliding, extrapolating their positions
	  based on current velocities and a default timestep, and returns the shortest vector by which to move the object `me`, to 
	  remedy the collision.
	If the objects do not collide, it returns None.
	"""
	separation = me.pos - you.pos # My distance from you.
	if separation.x == 0 and separation.y == 0:
		unit_separation = v(0,-1)
		separation_magnitude = 0
	else:
		separation_magnitude = abs(separation)
		unit_separation = separation.unit()

	ts = defaultTS
	if not me.shape.invert and not you.shape.invert:
		val = separation_magnitude - (me.shape.rad + you.shape.rad - ts*(me.vel*unit_separation + you.vel*unit_separation))
		if val < 0: return val*unit_separation
	if not me.shape.invert and you.shape.invert: # You're inverted, I'm not.
		val = (separation_magnitude + me.shape.rad - ts*(me.vel*unit_separation)) - (you.shape.rad - ts*(you.vel*unit_separation))
		if val > 0: return -val*unit_separation
	if me.shape.invert and not you.shape.invert: # I'm inverted, you're not.
		val = (separation_magnitude + you.shape.rad - ts*(you.vel*unit_separation)) - (me.shape.rad - ts*(me.vel*unit_separation))
		if val > 0: return val*unit_separation
	#if you.shape.invert and not me.shape.invert:
	#	val = (me.shape.rad - ts*(me.vel*unit_separation))
	
	# When you're adding in the velocity correction, you subtract because unit_separation is going to be in the wrong direction.
	if hasattr(me, "vel"): my_extents = (-me.shape.rad - ts*(me.vel*unit_separation), me.shape.rad - ts*(me.vel*unit_separation))
	else: my_extents = (-me.shape.rad, me.shape.rad)

	if hasattr(you, "vel"): your_extents = (-you.shape.rad + ts*(you.vel*unit_separation), you.shape.rad + ts*(you.vel*unit_separation))
	else: your_extents = (-you.shape.rad, you.shape.rad)
	
	output = intervalcompare(my_extents, your_extents, separation_magnitude, me_inverted = me.shape.invert , other_inverted = you.shape.invert )

	if output is None : return None
	return output*unit_separation 

def intervalcompare(extentsme, extentsother, msep, me_inverted = False, other_inverted = False):
	"""Returns the amount by which to move 'me' to ensure that two (1D) intervals are no longer intersecting, or none if they're already fine.
	
	extentsme and extentsother are tuples of left and right extents. 
	msep is the amount by which their centers are separated.
	me_inverted and other_inverted are flags - if they're set, then different logic is used.
	"""
	a, b = extentsme[0], extentsme[1]
	c, d = extentsother[0]+msep, extentsother[1]+msep
	#Possibilities:
	# If we're both inverted, then it's like this:				]a	b[	}c	d{
	#   then there's nothing we can do.
	if me_inverted and other_inverted :
		return None
		#output = msep + (extentsother[0] - extentsme[0] + extentsother[1] - extentsme[1])/2
	# If I'm inverted and he's not, then it's like this:		]a	b[	{c	d}
	#   then we need to move to align b and d, or a and c.
	elif me_inverted and not other_inverted :
		#if (my_left < your_left and my_right > your_right) : return None
		if (a < c and d < b): return None
		#if (msep + extentsother[0] > extentsme[0]) and (msep + extentsother[1] < extentsme[1]): return None
		#return min(your_right - my_right, your_left - my_right, key=abs)
		return min(d-b, c-a, key=abs)
		#return min( msep + extentsother[1] - extentsme[1] , msep + extentsother[0] - extentsme[0] , key=abs)
	# If I'm he's inverted and I'm not, then it's like this:	[a	b]	}c	d{
	#   then we need to move to align b and d, or a and c.
	elif not me_inverted and other_inverted :
		if (a > c and b < d): return None
		#if (msep + extentsother[0] < extentsme[0]) and (msep + extentsother[1] > extentsme[1]): return None
		#return min(your_right - my_right, your_left - my_right, key=abs)
		return min(d-b, c-a, key=abs)
		#return min( msep + extentsother[1] - extentsme[1] , msep + extentsother[0] - extentsme[0] , key=abs)
	# If neither of us are inverted, then it's like this:		[a	{c	b]	d}
	#   then our options are a and d or b and c.
	elif not me_inverted and not other_inverted :
		if (a > d or b < c): return None
		#if (msep + extentsother[0] > extentsme[1]): return None
		#if (msep + extentsother[1] < extentsme[0]): return None
		return min(c-b, d-a, key=abs)
		#return min( msep + extentsother[1] - extentsme[0] , msep + extentsother[0] - extentsme[1] , key=abs)



class Line(object):
	""" A line, potentially with rounded ends. """
	def __init__(self, vector, thickness=0):
		self.name = SHAPE_LINE
		self.v = vector
		self.normal = self.v.rperp().unit()
		self.length = abs(vector)
		self.thickness = thickness
		self.angle = math.atan2(vector.y, vector.x)

		# Build the vertex list.
		if thickness == 0:
			self.vlist = pyglet.graphics.vertex_list(2,'v3f')
			self.vlist.vertices = [0, 0, 0, vector.x, vector.y, 0]
		else:
			self.vlist = pyglet.graphics.vertex_list(22,'v3f')
			self.vlist.vertices[0:d*1] = [thickness, 0.0, 0.0]
			self.vlist.vertices[d*1:d*2] = [thickness, self.length, 0.0]
			for i in range(9):
				self.vlist.vertices[d*2+d*i:d*3+d*i] = [thickness * math.cos(math.pi*(i+1)/9),\
													self.length + thickness * math.sin(math.pi*(i+1)/9), 0.0]
			self.vlist.vertices[d*(9+2):d*(9+3)] = [-thickness,self.length, 0.0]
			self.vlist.vertices[d*(9+3):d*(9+4)] = [-thickness,0.0, 0.0]
			for i in range(9):
				self.vlist.vertices[d*(9+4)+d*i:d*(9+4)+d*(i+1)] = [-thickness*math.cos(math.pi*(i+1)/9), -thickness*math.sin(math.pi*(i+1)/9), 0.0]
	
		# Define the bounds.
		self.xbounds = ( min(0,vector.x)-thickness, max(0,vector.x)+thickness )
		self.ybounds = ( min(0,vector.y)-thickness, max(0,vector.y)+thickness )
	def draw(self, location, z=0):
		pyglet.gl.glPushMatrix()
		pyglet.gl.glTranslatef(location.x,location.y,z)
		if self.thickness == 0:
			self.vlist.draw(pyglet.gl.GL_LINE_STRIP)
		else:
			pyglet.gl.glRotatef(self.angle*180.0/math.pi - 90, 0.0, 0.0, 1.0)
			self.vlist.draw(pyglet.gl.GL_LINE_LOOP)
		pyglet.gl.glPopMatrix()
class Circle(object):
	""" Makes a circle object, which has simplified extents/projection code.
	Displays as a polygon with numpoints points.  Dynamic or fixed radius? For now, fixedish. or something.
	"""
	def __init__(self, numpoints = 10, rad = 30, drawtype = "oneline", invert = False):
		self.name = SHAPE_CIRCLE
		self.vlist = pyglet.graphics.vertex_list(numpoints,'v3f')
		for i in range(numpoints):
			self.vlist.vertices[d*i:d*(i+1)] = [math.cos(i*2*math.pi/numpoints), math.sin(i*2*math.pi/numpoints), 0]
		self.rad=rad
		self.rot=0
		self.drawtype=drawtype
		self.invert = invert
		self.xbounds = (-rad, rad)
		self.ybounds = (-rad, rad)
	def draw(self, location, z=0):
		""" Draws the polygon at the polygon's self.x, self.y locations, scaled by self.r, rotated self.rot. """
		pyglet.gl.glPushMatrix()
		pyglet.gl.glTranslatef(location.x,location.y,z)
		pyglet.gl.glScalef(self.rad,self.rad,1.0)
		pyglet.gl.glRotatef(self.rot, 0, 0, 1)
		if self.drawtype == "points" :
			self.vlist.draw(pyglet.gl.GL_POINTS)
		elif self.drawtype == "lines" :
			self.vlist.draw(pyglet.gl.GL_LINE_LOOP)
		elif self.drawtype == "oneline" :
			self.vlist.draw(pyglet.gl.GL_LINE_STRIP)
		elif self.drawtype == "fill" :
			self.vlist.draw(pyglet.gl.GL_POLYGON)
		else: self.vlist.draw(self.drawtype)
		pyglet.gl.glPopMatrix()

