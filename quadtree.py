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
	TODO: Implement empty Leaf Nodes. right now you have to handle empty nodes everywhere; that is very suboptimal.
	"""
	def __init__(self,items=[],center=v(0,0), height=8):
		self.height = height

		list.__init__(self, [ None, None, None, None ])

		self.xc, self.yc = center.x, center.y
		self.Items = SortSearchList([])
		# Pass the filling of the tree to the extend method.
		self.extend(items)

	def get_quadrant(self, obj):
		"""Finds which bucket the item should go in - that is, if we added the item to the quadtree, what bucket would it be in."""
		if x_min(obj) > self.xc: # If it's east of center
			if y_min(obj) > self.yc: return 0 # If it's northeast of center
			elif y_max(obj) < self.yc: return 1 # If it's southeast of center
			else: return -1 # Should return Items. or 5. or something.
		elif x_max(obj) < self.xc: # If it's west of center
			if y_min(obj) > self.yc: return 2 # If it's northwest of center
			elif y_max(obj) < self.yc: return 3 # If it's southwest of center
			else: return -1 # Should return Items. or 5. or something.
		else: return -1
		# Should return Items or 5 or whatever
	
	def do_recursively(self, some_function):
		some_function(self)
		if self[0] is not None: some_function(self[0])
		if self[1] is not None: some_function(self[1])
		if self[2] is not None: some_function(self[2])
		if self[3] is not None: some_function(self[3])

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
		if self.height is 0: self.Items.append(obj) # If you're at the bottom, put it straight into the Items bucket. No deeper.
		quadrant = self.get_quadrant(obj)
		if quadrant is -1 or self.height is 0: self.Items.append(obj) # Maybe offload the self.height check into get_quadrant? nah, don't think so
		elif self[quadrant] is None: self[quadrant] = QuadTree([obj], obj.pos, height=self.height-1)
		else: self[quadrant].append(obj)

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
			quadrant = self.get_quadrant(thing)
			if quadrant is -1 or self.height is 0: self.Items.append(thing)
			else: appendage[quadrant].append(thing)
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
		  If object is in this node, return the height, remove the object, and End Operation.
		  Else, check if object is in the most likely subnode.
		  Else, check in the other subnodes.
		TODO: remove empty subtrees. Whoops.
		"""
		# If it's in the Items bucket, remove it and return True for successfully removing the object.
		if self.Items.remove(obj): return True

		if self.get_quadrant(obj) is -1: order = (0,1,2,3)
		else: order = ((0,1,2,3),(1,0,2,3),(2,3,0,1),(3,2,0,1))[self.get_quadrant(obj)]

		for i in order:
			if self[i] is not None:
				self[i].remove(obj)

		return False 

	def clear(self):
		""" Not sure if this actually needs to go through and delete everything, but I figure I might as well. """
		del self.Items
		for quad in self:
			quad.clear()
			quad = None

	def __contains__(self,item):
		""" Discover if the tree contains item, in a less lazy way. """
		if item in self.Items: return True
		if self.get_quadrant(item) is -1: order = (0,1,2,3)
		else: order = ((0,1,2,3),(1,0,2,3),(2,3,0,1),(3,2,0,1))[self.get_quadrant(item)]

		for i in order:
			if self[i] is not None and item in self[i]: return True

		return False

	def __len__(self):
		return len(self.Items) + sum(map(lambda x: len(self[x]) if self[x] is not None else 0, range(4))) #ugh.

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
			return True
		return False
		
	def collisions(self,item):
		# Gotta find out where item would be if it were in self.items. How do? binary search?
		output = set()

		# If the item being tested were in here, then its index in the list of minimums would be like so
		index_minimum = bisect.bisect_left(self.minimums, self.min_key(item), key=self.min_key)
		# Similarly for the list of maxima.
		index_maximum = bisect.bisect_left(self.maximums, self.max_key(item), key=self.max_key)

		for other_item in self.minimums[index_minimum:]:
			if other_item == item: continue
			# This is probably the most important part of this class. This says that we stop checking in
			# this direction, when we find an object whose minimum is beyond our maximum.
			if x_min( other_item ) > x_max( item ): break
			# If item intersects the item under consideration, then add it to the collision set.
			if intersects(item, other_item) is not None: output.add(other_item) 

		for other_item in self.maximums[index_maximum:]:
			if other_item == item: continue
			# As above, important line here - Except that now, we're going through the list of right extents (maxima), and therefore backwards.
			if x_max( other_item ) < x_min( item ): break
			if intersects(item, other_item) is not None: output.add(other_item)
		
		return output
