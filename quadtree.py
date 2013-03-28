from vectors import v
import math
import random
import buildsortsearch as sortsearchsolution

y_min = lambda o: o.pos.y + o.shape.ybounds[0]
y_max = lambda o: o.pos.y + o.shape.ybounds[1]
x_min = lambda o: o.pos.x + o.shape.xbounds[0]
x_max = lambda o: o.pos.x + o.shape.xbounds[1]
split_threshhold = 5

def intersects(me, you):
	"""Return whether or not me and you are colliding. May very well be overwritten by the caller of the library."""
	return abs(me.pos-you.pos) <= me.radius + you.radius

sortsearchsolution.intersects = intersects

class QuadTree(list):
	def __init__(self,items=[],center=v(0,0), height=8):
		self.height = height

		list.__init__(self, [ None, None, None, None ])

		self.xmin, self.xmax = center.x-1,center.x+1
		self.ymin, self.ymax = center.y-1,center.y+1
		self.xc,self.yc = center.x, center.y
		self.Items = sortsearchsolution.SortSearchList([])
		self.count = 0
		# Pass the filling of the tree to the extend method.
		self.extend(items)

	def all_collisions(self):
		output = set(self.Items.all_collisions()) or set()
		for thing in self.Items:
			for quad in self: 
				if quad is not None: 
					output = output | (quad.collisions(thing) or set())
		for quad in self:
			if quad is not None: output = output | (quad.all_collisions() or set())
		return output
			
	def collisions(self, obj):
		if y_min(obj) > self.ymax: return set()
		if y_max(obj) < self.ymin: return set()
		if x_min(obj) > self.xmax: return set()
		if x_max(obj) < self.xmin: return set()

		output = self.Items.collisions(obj) # Calls collisions from Items. Here's the problem maybe?
		if x_min(obj) < self.xc:
			if y_min(obj) < self.yc and self[3] is not None: output = output | self[3].collisions(obj)
			if y_max(obj) > self.yc and self[2] is not None: output = output | self[2].collisions(obj)
		if x_max(obj) > self.xc:
			if y_min(obj) < self.yc and self[1] is not None: output = output | self[1].collisions(obj)
			if y_max(obj) > self.yc and self[0] is not None: output = output | self[0].collisions(obj)
		return output
	
	def append(self, obj):
		""" Insert obj into this quadtree. Should throw it into the appropriate 
		quadrant if necessary, and otherwise throw it into the self.Items bin.
		Actually, the problem of where to locate the centers for the new quadrants 
		is quite a bit of a problem. Not really sure how I'm going to do that! The 
		solution I came up with for multiple insertions (at creation time) was to
		sample a random third of the points and average their positions.
		"""
		# If it extends our bounds, extend our bounds.
		if y_min(obj) < self.ymin: self.ymin = y_min(obj)
		if y_max(obj) > self.ymax: self.ymax = y_max(obj)
		if x_min(obj) < self.xmin: self.xmin = x_min(obj)
		if x_max(obj) > self.xmax: self.xmax = x_max(obj)

		if obj in self.Items: return self.height   ### If the object is in this level, go ahead and return the current height
		if x_min(obj) > self.xc: # If it's east of center
			if y_min(obj) > self.yc: # If it's north of center
				if self[0] is None: self[0] = QuadTree([obj], obj.pos, height=self.height-1)
				else: self[0].append(obj) # Add to box zero - NE, quadrant 1
			elif y_max(obj) < self.yc: # If it's south of center
				if self[1] is None: self[1] = QuadTree([obj], obj.pos, height=self.height-1)
				else: self[1].append(obj) # Add to box one - SE, quadrant 4
			else: self.Items.append(obj) # If it's not unambiguously in north/south, then stick it in this level.
		elif x_max(obj) < self.xc: # If it's west of center
			if y_min(obj) > self.yc: # If it's north of center
				if self[2] is None: self[2] = QuadTree([obj], obj.pos, height=self.height-1)
				else: self[2].append(obj) # Add to box two - NW, quadrant 2
			elif y_max(obj) < self.yc: # If it's south of center
				if self[3] is None: self[3] = QuadTree([obj], obj.pos, height=self.height-1)
				else: self[3].append(obj) # Add to box three - SW, quadrant 3
			else: self.Items.append(obj) # If it's not unambiguously in north/south, then drop it in this level.
		else: self.Items.append(obj) # If it's not unambiguously east/west, then drop it in this level.
		self.count = self.count + 1

	def insert(self, item):
		return self.append(item)

	def extend(self, items):
		""" Add a bunch of objects to the quadtree. """
		self.count = self.count + len(items)
		if self.height == 0 or len(self.Items) + len(items) < split_threshhold:
			self.Items.extend(items)
			return
		appendage = [ [], [], [], [] ]
		for thing in items:
			if x_min(thing) > self.xc:
				if y_min(thing) > self.yc: appendage[0].append(thing)
				elif y_max(thing) < self.yc: appendage[1].append(thing)
				else: self.Items.append(thing)
			elif x_max(thing) < self.xc:
				if y_min(thing) > self.yc: appendage[2].append(thing)
				elif y_max(thing) < self.yc: appendage[3].append(thing)
				else: self.Items.append(thing)
			else: self.Items.append(thing)
			if x_min(thing) < self.xmin: self.xmin = x_min(thing)
			if x_max(thing) > self.xmax: self.xmax = x_max(thing)
			if y_min(thing) < self.ymin: self.ymin = y_min(thing)
			if y_max(thing) > self.ymax: self.ymax = y_max(thing)
		for i, quadrantlist in enumerate(appendage):
			if len(quadrantlist) == 0: continue
			if self[i] is None:
				qcenter = v(0,0)
				for thing in random.sample(quadrantlist,min(10,len(quadrantlist))):
					qcenter = qcenter + thing.pos/min(10,len(quadrantlist))
				self[i] = QuadTree(quadrantlist, qcenter, height = self.height-1)
			else:
				self[i].extend(quadrantlist)

	def remove(self, obj):
		""" Remove obj from the tree. If it's already here, return the height of the object. Else return none. 
		In the future, I suppose that it should throw an exception if it tries to remove an object not in the tree.

		So here's a new thinking: to remove object from the thing, check if it is in this node of the tree.
			If object is in this node, return the height, remove the object, and End Operation.
			Else, check if object is in the most likely subnode.
			Else, check in the other subnodes.
		
		... How the crap do we update the maximums and minimums of the quadtree?
		... Also, there's no removal of empty subtrees.
		"""
		self.count = self.count - 1
		if obj in self.Items: 
			self.Items.remove(obj)
			return self.height

		out = False
		if x_min(obj) > self.xc:
			if y_min(obj) > self.yc: 
				if self[0] is not None: out = out or self[0].remove(obj)
				if self[1] is not None: out = out or self[1].remove(obj)
				if self[2] is not None: out = out or self[2].remove(obj)
				if self[3] is not None: out = out or self[3].remove(obj)
			if y_max(obj) < self.yc: 
				if self[1] is not None: out = out or self[1].remove(obj)
				if self[0] is not None: out = out or self[0].remove(obj)
				if self[2] is not None: out = out or self[2].remove(obj)
				if self[3] is not None: out = out or self[3].remove(obj)
			if not out: self.count = self.count + 1
			return out
		if x_max(obj) < self.xc:
			if y_min(obj) > self.yc: 
				if self[2] is not None: out = out or self[2].remove(obj)
				if self[3] is not None: out = out or self[3].remove(obj)
				if self[0] is not None: out = out or self[0].remove(obj)
				if self[1] is not None: out = out or self[1].remove(obj)
			if y_max(obj) < self.yc: 
				if self[3] is not None: out = out or self[3].remove(obj)
				if self[2] is not None: out = out or self[2].remove(obj)
				if self[0] is not None: out = out or self[0].remove(obj)
				if self[1] is not None: out = out or self[1].remove(obj)
			if not out: self.count = self.count + 1
			return out
		self.count = self.count + 1
		return False

	def clear(self):
		""" Not sure if this actually needs to go through and delete everything, but I figure I might as well. """
		del self.Items
		for quad in self:
			quad.clear()
			quad = None




# Shouldn't be much of interest past here.
##
##
#
	# Lazy contains. May miss stuff if it's moved.
	def lazy__contains__(self, item):
		""" Discover if the tree contains item. """
		if item in self.Items: return True
		if x_min(item) > self.xc:
			if y_min(item) > self.yc: return item in self[0]
			if y_max(item) < self.yc: return item in self[1]
		if x_max(item) < self.xc:
			if y_min(item) > self.yc: return item in self[2]
			if y_max(item) < self.yc: return item in self[3]
		return False
	def __contains__(self,item):
		""" Discover if the tree contains item, in a less lazy way. """
		if self.empty: return False
		if item in self.Items: return True
		if x_min(item) > self.xc:
			if y_min(item) > self.yc: return item in self[0] or item in self[1] or item in self[2] or item in self[3]
			if y_max(item) < self.yc: return item in self[1] or item in self[0] or item in self[3] or item in self[2]
		if x_max(item) < self.xc:
			if y_min(item) > self.yc: return item in self[2] or item in self[3] or item in self[0] or item in self[1]
			if y_max(item) < self.yc: return item in self[3] or item in self[2] or item in self[1] or item in self[0]
		return False

	def __len__(self):
		return self.count

	def statusrep(self, indent):
		output = indent + " count: " + str(self.__len__()) + "   here: " +  str(self.Items.__len__()) 
		if self[0] is not None: output += "\n" + self[0].statusrep(indent + "-|")
		if self[1] is not None: output += "\n" + self[1].statusrep(indent + "-|")
		if self[2] is not None: output += "\n" + self[2].statusrep(indent + "-|")
		if self[3] is not None: output += "\n" + self[3].statusrep(indent + "-|")
		return output
