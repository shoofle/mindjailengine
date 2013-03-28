from vectors import v
import math
import random
import bisect
import shapes

y_min = lambda o: o.pos.y + o.shape.ybounds[0]
y_max = lambda o: o.pos.y + o.shape.ybounds[1]
x_min = lambda o: o.pos.x + o.shape.xbounds[0]
x_max = lambda o: o.pos.x + o.shape.xbounds[1]

split_threshhold = 5 # When you bulk-add a bunch of objects, this serves the purpose of saying "hey, if this quadtree's going to have 
# fewer than this many objects, we might as well just chuck'em all in the Items bucket." I don't even know if this is a good *idea*. 
# It's not used very much.

def intersects(me, you):
	"""Return whether or not me and you are colliding. May very well be overwritten by the caller of the library."""
	return shapes.intersect(me, you) if me.tangible and you.tangible else False


class QuadTree(list):
	"""A QuadTree partitions a planar space into four sections, for a recursive data structure that makes collision detection fast.

	Okay, the low-down is this: we've got four subtrees and an Items bucket. Objects in the northeast, southeast, northwest, and southwest
	  respectively go into the 0, 1, 2, and 3 subtrees. Things that are ambiguous go in the Items bucket. If the height of the tree is zero
	  then everything goes in the Items bucket.
	TODO: The problem of where to locate the centers of new trees is unfinished.
	TODO: There's no pruning of empty trees.
	This relies on some sort of also-efficient data structure for the Items bucket. At the moment it's hard to explain, but it's basically
	  a list that keeps two directions of sort in memory at all times - sorted by leftmost extent ascending and by rightmost extent descending.
	  Collision detection is fast for reasons. Check it out, it's not too confusing, I think. Well, it's confusing, but it works. Should.
	TODO: Efficiently reorganize the quadtree when necessary.
	TODO: Switch from using self[0::3] + self.Items to just using self[0::4]. Thinking that I should just use a get_bucket function which
	  would also encapsulate the relationship of the quadtree to the space it's in. That's a thing I should really do.
	"""
	def __init__(self,items=[],center=v(0,0), height=8):
		self.height = height

		list.__init__(self, [ None, None, None, None ])

		self.xc,self.yc = center.x, center.y
		self.Items = SortSearchList([])
		# Pass the filling of the tree to the extend method.
		self.extend(items)

	def get_quadrant(self, item):
		"""Finds which bucket the item should go in - that is, if we added the item to the quadtree, what bucket would it be in."""
		if x_min(obj) > self.xc: # If it's east of center
			if y_min(obj) > self.yc: return 0 # If it's northeast of center
			elif y_max(obj) < self.yc: return 1 # If it's southeast of center
			# Should return Items. or 5. or something.
		elif x_max(obj) < self.xc: # If it's west of center
			if y_min(obj) > self.yc: return 2 # If it's northwest of center
			elif y_max(obj) < self.yc: return 3 # If it's southwest of center
			# Should return Items. or 5. or something.
		# Should return Items or 5 or whatever

	def collisions(self, obj):
		"""Returns a set of objects with which the passed-in thing is colliding."""
		output = self.Items.collisions(obj) # Calls collisions from Items. Here's the problem maybe?
		if x_min(obj) < self.xc: # This is different from just getting the bucket the item is in. This is actually completely different.
			if y_min(obj) < self.yc and self[3] is not None: output = output | self[3].collisions(obj)
			if y_max(obj) > self.yc and self[2] is not None: output = output | self[2].collisions(obj)
		if x_max(obj) > self.xc:
			if y_min(obj) < self.yc and self[1] is not None: output = output | self[1].collisions(obj)
			if y_max(obj) > self.yc and self[0] is not None: output = output | self[0].collisions(obj)
		return output

	def append(self, obj):
		""" Insert obj into this quadtree. Should throw it into the appropriate 
		quadrant if necessary, and otherwise throw it into the self.Items bin.
		"""

		if obj in self.Items: return self.height   ### If the object is in this level, go ahead and return the current height
		if self.height is 0: self.Items.append(obj) # If you're at the bottom, put it straight into the Items bucket. No deeper.
		elif x_min(obj) > self.xc: # If it's east of center
			if y_min(obj) > self.yc: # If it's north of center
				if self[0] is None: self[0] = QuadTree([obj], obj.pos, height=self.height-1)
				else: 
					output = self[0].append(obj)
					if output: return output  # Add to box zero - NE, quadrant 1
			elif y_max(obj) < self.yc: # If it's south of center
				if self[1] is None: self[1] = QuadTree([obj], obj.pos, height=self.height-1)
				else: 
					output = self[1].append(obj)
					if output: return output # Add to box one - SE, quadrant 4
			else: self.Items.append(obj) # If it's not unambiguously in north/south, then stick it in this level.
		elif x_max(obj) < self.xc: # If it's west of center
			if y_min(obj) > self.yc: # If it's north of center
				if self[2] is None: self[2] = QuadTree([obj], obj.pos, height=self.height-1)
				else: 
					output = self[2].append(obj) 
					if output: return output# Add to box two - NW, quadrant 2
			elif y_max(obj) < self.yc: # If it's south of center
				if self[3] is None: self[3] = QuadTree([obj], obj.pos, height=self.height-1)
				else: 
					output = self[3].append(obj) 
					if output: return output# Add to box three - SW, quadrant 3
			else: self.Items.append(obj) # If it's not unambiguously in north/south, then drop it in this level.
		else: self.Items.append(obj) # If it's not unambiguously east/west, then drop it in this level.

	def insert(self, item):
		return self.append(item)

	def extend(self, items):
		""" Add a large number of objects at once to the quadtree.

		Actually, the problem of where to locate the centers for the new quadrants 
		is quite a bit of a problem. Not really sure how I'm going to do that! The 
		solution I came up with for multiple insertions (at creation time) was to
		sample a random third of the points and average their positions.
		"""
		if self.height == 0 or len(self.Items) + len(items) < split_threshhold: # Not sure if I want split_threshhold.
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
		""" Remove obj from the tree. Returns falsy if the object was not found. 

		In the future, I suppose that it should throw an exception if it tries to remove an object not in the tree.
		So here's a new thinking: to remove object from the thing, check if it is in this node of the tree.
		  If object is in this node, return the height, remove the object, and End Operation.
		  Else, check if object is in the most likely subnode.
		  Else, check in the other subnodes.
		TODO: remove empty subtrees. Whoops.
		"""
		# Use get_quadrant function (not yet in use).
		# order = ((0,1,2,3),(1,0,2,3),(2,3,0,1),(3,2,0,1),(0,1,2,3))[self.get_quadrant(obj)]
		# When everything's in an index, 4 (for the Items bucket) should go in the second spot in the first four, and the first spot in the last.

		# If it's in the Items bucket, remove it and return True for successfully removing the object.
		if obj in self.Items: 
			self.Items.remove(obj)
			return True

		# Define what order we should check the quadrants in.
		if x_min(obj) > self.xc and y_min(obj) > self.yc: order = (0,1,2,3)
		elif x_min(obj) > self.xc: order = (1,0,2,3)
		elif y_min(obj) > self.yc: order = (2,3,0,1)
		else: order = (3,2,0,1)

		for i in order:
			if self[i] is not None and self[i].remove(obj): return True
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
		if item in self.Items: return True
		if x_min(item) > self.xc:
			if y_min(item) > self.yc: return (item in self[0]) or (item in self[1]) or (item in self[2]) or (item in self[3])
			if y_max(item) < self.yc: return (item in self[1]) or (item in self[0]) or (item in self[3]) or (item in self[2])
		if x_max(item) < self.xc:
			if y_min(item) > self.yc: return (item in self[2]) or (item in self[3]) or (item in self[0]) or (item in self[1])
			if y_max(item) < self.yc: return (item in self[3]) or (item in self[2]) or (item in self[1]) or (item in self[0])
		return False

	def __len__(self):
		return len(self.Items) + (len(self[0]) if self[0] is not None else 0) + (len(self[1]) if self[1] is not None else 0) + (len(self[2]) if self[2] is not None else 0) + (len(self[3]) if self[3] is not None else 0)

	def statusrep(self, indent):
		output = indent + " count: " + str(len(self)) + "   here: " +  str(len(self.Items)) 
		if self[0] is not None: output += "\n" + self[0].statusrep(indent + "-|")
		if self[1] is not None: output += "\n" + self[1].statusrep(indent + "-|")
		if self[2] is not None: output += "\n" + self[2].statusrep(indent + "-|")
		if self[3] is not None: output += "\n" + self[3].statusrep(indent + "-|")
		return output




###
# Linear Sort Search (on the x-axis)
###
class SortSearchList(list):
	""" A data structure for fast collision detection, which has an optimization over brute-force.

	The basic idea of this structure is that, in order to do fast collision detection on a set of objects, you keep
	  two lists of them - one sorted by their rightmost extent, and one sorted by their leftmost extent, sorted in 
	  opposite directions. The huge benefit to this is that when you check for collisions, you just need to look left 
	  and right until you find objects which can't possibly be colliding with this one.
	You store them sorted by their minimum extent, in ascending order. This way, checking through in order for collisions,
	  when you get to an object whose minimum extent is greater than your maximum extent, you know you're done in that 
	  direction. Likewise, you check in descending order by maximum extent - when you find one whose maximum extent
	  is less than your minimum extent, you know that every other object in the list is going to be far outside your bounds.
	It's a big improvement over a brute-force search, but it's not as good as a quadtree (I think). However, it produced
	  really noticeable improvements when I used it as the Item bucket for a quadtree. So that's why it's here.
	"""
	def __init__(self, input_list=[]):
		list.__init__(self)
		self.extend(input_list)

	def min_key(self, thing):
		return x_min(thing)
	def max_key(self, thing):
		return -x_max(thing)

	def extend(self, item_list):
		list.extend(self, item_list)
		self.minimums = sorted(self, key=self.min_key)
		self.maximums = sorted(self, key=self.max_key)

	def append(self, item):
		list.append(self, item)
		# Inserts the item into the minimum and maximum lists, keeping them sorted appropriately.
		bisect.insort(self.minimums, item, key=self.min_key, testval=self.min_key(item))
		bisect.insort(self.maximums, item, key=self.max_key, testval=self.max_key(item))

	def insert(self, item):
		self.append(item)

	def remove(self, item):
		if item in self:
			list.remove(self, item)
			self.minimums.remove(item)
			self.maximums.remove(item)
			return item
		else: return False
		
	def collisions(self,item):
		# Gotta find out where item would be if it were in self.items. How do? binary search?
		output = set()

		# If the item being tested were in here, then its index in the list of minimums would be like so
		index_minimum = bisect.bisect_left(self.minimums, self.max_key(item), key=self.min_key)
		# Similarly for the list of maxima.
		index_maximum = bisect.bisect_left(self.maximums, self.max_key(item), key=self.max_key)

		for other_item in self.minimums[index_minimum:]:
			if other_item == item: continue
			# This is probably the most important part of this class. This says that we stop checking in
			# this direction, when we find an object whose minimum is beyond our maximum.
			if x_min( other_item ) > x_max( item ): break
			# If item intersects the item under consideration, then add it to the collision set.
			if intersects(item, other_item) is not None: output.add(other_item) 

		for other_item in self.maximums[:index_maximum]:
			if other_item == item: continue
			# As above, important line here - Except that now, we're going through the list of right extents (maxima), and therefore backwards.
			if x_max( other_item ) < x_min( item ): break
			if intersects(item, other_item) is not None: output.add(other_item)

		return output
