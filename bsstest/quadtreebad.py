from vectors import v
import math
import random

# lambdas which return the bounds of the object. yb = y minimum, yt = y maximum, xb = x minimum, xt = x maximum
#yb = yminfunction = lambda x: x.shape.ybounds[0]
#yt = ymaxfunction = lambda x: x.shape.ybounds[1]
#xb = xminfunction = lambda x: x.shape.xbounds[0]
#xt = xmaxfunction = lambda x: x.shape.xbounds[1]
yb = lambda x: x.ymin
yt = lambda x: x.ymax
xb = lambda x: x.xmin
xt = lambda x: x.xmax

split_threshhold = 2

def do_collide(me, you):
	"""Should be overwritten by the caller of this library. do_collide(a,b) is the action to take if a and b collide."""
	pass
def intersects(me, you):
	"""Return whether or not me and you are colliding. May very well be overwritten by the caller of the library."""
	return abs(me.pos-you.pos) <= me.radius + you.radius
	#return yb(me) <= yt(you) and yt(me) >= yb(you) and xb(me) <= xt(you) and xt(me) >= xb(you)

class EmptyTree:
	def __init__(self):
		self.empty = True
	def remove(self, *args, **kwargs):
		return False
	def collisions(self, *args, **kwargs):
		return False
	def __contains__(self, item):
		return False
	
class QuadTree:
	def __init__(self,items=[],center=v(0,0),height=8):
		self.height = height
		self._count = len(items)

		#self.Items = items
		self.quadrants = [ None, None, None, None ]
		self.NE = self.quadrants[0] = None
		self.SE = self.quadrants[1] = None
		self.NW = self.quadrants[2] = None
		self.SW = self.quadrants[3] = None

		self.xmin, self.xmax = -1,1
		self.ymin, self.ymax = -1,1
		self.center = center
		self.xc,self.yc = self.center.x, self.center.y

		#yb=yminfunction
		#yt=ymaxfunction
		#xb=xminfunction
		#xt=xmaxfunction

		# If we're at zero height, chuck it all in the Items bin.
		self.Items = []
		if self.height == 0:
			self.Items = items
			return

		self.extend(items)

	def collisions(self, obj):
		#if yb(obj) > self.ymax: return None
		#if yt(obj) < self.ymin: return None
		#if xb(obj) > self.xmax: return None
		#if xt(obj) < self.xmin: return None
		_count = 0

		for other in self.Items: 
			if other is obj: continue
			if intersects(obj,other):
				do_collide(obj,other)

		if xb(obj) < self.xc:
			if yb(obj) < self.yc: 
				if self.SW is not None: self.SW.collisions(obj)
			if yt(obj) > self.yc: 
				if self.NW is not None: self.NW.collisions(obj)
		if xt(obj) > self.xc:
			if yb(obj) < self.yc: 
				if self.SE is not None: self.SE.collisions(obj)
			if yt(obj) > self.yc: 
				if self.NE is not None: self.NE.collisions(obj)
	
	def insert(self, obj):
		""" Insert obj into this quadtree. Should throw it into the appropriate 
		quadrant if necessary, and otherwise throw it into the self.Items bin.
		Actually, the problem of where to locate the centers for the new quadrants 
		is quite a bit of a problem. Not really sure how I'm going to do that! The 
		solution I came up with for multiple insertions (at creation time) was to
		sample a random third of the points and average their positions.
		"""
		if yb(obj) < self.ymin: self.ymin = yb(obj)
		if yt(obj) > self.ymax: self.ymax = yt(obj)
		if xb(obj) < self.xmin: self.xmin = xb(obj)
		if xt(obj) > self.xmax: self.xmax = xt(obj)

		if obj in self.Items: return self.height   ### If the object is in this level, go ahead and return the current height
		if xb(obj) > self.xc:
			if yb(obj) > self.yc: 
				if self.NE is None: self.NE = QuadTree([obj], obj.pos, height=self.height-1)
				else: self.NE.insert(obj)
			elif yt(obj) < self.yc:
				if self.SE is None: self.SE = QuadTree([obj], obj.pos, height=self.height-1)
				else: self.SE.insert(obj)
			else: self.Items.append(obj)
		elif xt(obj) < self.xc:
			if yb(obj) > self.yc:
				if self.NW is None: self.NW = QuadTree([obj], obj.pos, height=self.height-1)
				else: self.NW.insert(obj)
			elif yt(obj) < self.yc:
				if self.SW is None: self.SW = QuadTree([obj], obj.pos, height=self.height-1)
				else: self.SW.insert(obj)
			else: self.Items.append(obj)
		else: self.Items.append(obj)
	def append(self, item):
		return self.insert(item)

	def extend(self, items):
		""" Add a bunch of objects to the quadtree. """
		self._count = self._count + len(items)
		if self.height == 0 or self._count < split_threshhold:
			self.Items.extend(items)
			self.NE = self.quadrants[0] = None
			self.SE = self.quadrants[1] = None
			self.NW = self.quadrants[2] = None
			self.SW = self.quadrants[3] = None
			return
		appendage = [ [], [], [], [] ]
		for thing in items:
			if xb(thing) > self.xc:
				if yb(thing) > self.yc: appendage[0].append(thing)
				elif yt(thing) < self.yc: appendage[1].append(thing)
				else: self.Items.append(thing)
			elif xt(thing) < self.xc:
				if yb(thing) > self.yc: appendage[2].append(thing)
				elif yt(thing) < self.yc: appendage[3].append(thing)
				else: self.Items.append(thing)
			else: self.Items.append(thing)
			if xb(thing) < self.xmin: self.xmin = xb(thing)
			if xt(thing) > self.xmax: self.xmax = xt(thing)
			if yb(thing) < self.ymin: self.ymin = yb(thing)
			if yt(thing) > self.ymax: self.ymax = yt(thing)
		for i, quadrantlist in enumerate(appendage):
			if len(quadrantlist) == 0: continue
			qcenter = v(0,0)
			#for thing in random.sample(quadrantlist,int(math.ceil(len(quadrantlist)/3))):
			for thing in random.sample(quadrantlist,min(4,len(quadrantlist))):
				qcenter = qcenter + thing.pos/min(4,len(quadrantlist))
			self.quadrants[i] = QuadTree(quadrantlist, qcenter, height = self.height-1)
		self.NE, self.SE, self.NW, self.SW = self.quadrants


	def remove(self, obj):
		""" Remove obj from the tree. If it's already here, return the height of where it was removed from. Else return none.
		In the future, I suppose that it should throw an exception if it tries to remove an object not in the tree.

		So here's a new thinking: to remove object from the thing, check if it is in this node of the tree.
			If object is in this node, return the height, remove the object, and End Operation.
			Else, check if object is in the most likely subnode.
			Else, check in the other subnodes.
		"""
		self._count = self._count - 1
		if obj in self.Items: 
			self.Items.remove(obj)
			return self.height

		out = False
		if xb(obj) > self.xc:
			if yb(obj) > self.yc: 
				if self.NE is not None: out = out or self.NE.remove(obj)
				if self.SE is not None: out = out or self.SE.remove(obj)
				if self.NW is not None: out = out or self.NW.remove(obj)
				if self.SW is not None: out = out or self.SW.remove(obj)
				return out
			if yt(obj) < self.yc: 
				if self.SE is not None: out = out or self.SE.remove(obj)
				if self.NE is not None: out = out or self.NE.remove(obj)
				if self.NW is not None: out = out or self.NW.remove(obj)
				if self.SW is not None: out = out or self.SW.remove(obj)
				return out
		if xt(obj) < self.xc:
			if yb(obj) > self.yc: 
				if self.NW is not None: out = out or self.NW.remove(obj)
				if self.SW is not None: out = out or self.SW.remove(obj)
				if self.NE is not None: out = out or self.NE.remove(obj)
				if self.SE is not None: out = out or self.SE.remove(obj)
				return out
			if yt(obj) < self.yc: 
				if self.SW is not None: out = out or self.SW.remove(obj)
				if self.NW is not None: out = out or self.NW.remove(obj)
				if self.NE is not None: out = out or self.NE.remove(obj)
				if self.SE is not None: out = out or self.SE.remove(obj)
				return out
		self._count = self._count + 1
		return False

	def clear(self):
		""" Not sure if this actually needs to go through and delete everything, but I figure I might as well. """
		self.Items = []
		for quad in self.quadrant:
			quad.clear()
			quad = None

	# Lazy contains. May miss stuff if it's moved.
	def lazy__contains__(self, item):
		""" Discover if the tree contains item. """
		if item in self.Items: return True
		if xb(item) > self.xc:
			if yb(item) > self.yc: return item in self.NE
			if yt(item) < self.yc: return item in self.SE
		if xt(item) < self.xc:
			if yb(item) > self.yc: return item in self.NW
			if yt(item) < self.yc: return item in self.SW
		return False
	def __contains__(self,item):
		""" Discover if the tree contains item, in a less lazy way. """
		if self.empty: return False
		if item in self.Items: return True
		if xb(item) > self.xc:
			if yb(item) > self.yc: return item in self.NE or item in self.SE or item in self.NW or item in self.SW
			if yt(item) < self.yc: return item in self.SE or item in self.NE or item in self.SW or item in self.NW
		if xt(item) < self.xc:
			if yb(item) > self.yc: return item in self.NW or item in self.SW or item in self.NE or item in self.SE
			if yt(item) < self.yc: return item in self.SW or item in self.NW or item in self.SE or item in self.NE
		return False

	#@property
	#def count(self):
	#	self._count = len(self.Items)
	#	for quadrant in self.
	#	return self._count


#class QTIterator:
#	def __init__(self, quadtree):
#		self.treehead = quadtree
#		self.stack = [quadtree]
#		self.quadrant = 0
#		self.currentnode = quadtree
#		while self.currentnode.NE is not None:
#			self.currentnode = self.currentnode.SE
#		while self.currentnode.SE is not None:
#			self.currentnode = self.currentnode.NW
#		while self.currentnode.NW is not None:
#			self.currentnode = self.currentnode.SW
#		while self.currentnode.SW is not None:
#	def __iter__(self):
#		return self
#	def next(self):		
