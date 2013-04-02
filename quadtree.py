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
bucket_indices = (0,1,2,3)

def center_from_object(thing):
	return thing.pos.x, thing.pos.y

def center_from_group(things):
	#sampling = random.sample(things, min(len(things), 10))
	# Average their positions based on their pos attributes.
	center = sum(map(lambda x: x.pos, things),v(0,0))/len(things)
	return center.x, center.y

def intersects(a, b):
	"""Return whether or not me and you are colliding. May very well be overwritten by the caller of the library."""
	if a.test_for_collision and b.test_for_collision:
		return shapes.intersect(a,b)


class QuadTree(object):
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

	def __init__(self, items=None, center=None, height=8):
		self.leaf_node = True
		self.height = height

		if center is None: center = v(0,0)
		self.xc, self.yc = center.x, center.y

		self.children = []
		self.contents = SortSearchList()

		# Pass the filling of the tree to the extend method.
		if items is not None: self.extend(items)

	def get_bucket_label(self, obj):
		"""Return the label for the bucket this should go in."""
		if self.height is 0: return -1
		if x_min(obj) > self.xc: # If it's east of center
			if y_min(obj) > self.yc: return 0 # ne of center
			elif y_max(obj) < self.yc: return 1 # If it's southeast of center
			else: return -1
		elif x_max(obj) < self.xc: # If it's west of center
			if y_min(obj) > self.yc: return 2 # If it's northwest of center
			elif y_max(obj) < self.yc: return 3 # If it's southwest of center
			else: return -1 # Should return Items. or 5. or something.
		else: return -1

	def collisions(self, thing):
		"""Return a set of all the objects in self colliding with thing.
		
		TODO: change this to fit with the new system, so... this shouldn't include references to x_min etc."""
		if self.leaf_node: return set()
		
		# Any object could be touching the contents of the current level of the tree.
		output = self.contents.collisions(thing)
		# An object would need to satisfy certain constraints to be intersecting the children.
		# In order to touch an object in the northeast child, its maxima need to be greater than our center.
		if x_max(thing) > self.xc and y_max(thing) > self.yc: output = output | self.children[0].collisions(thing)
		if x_max(thing) > self.xc and y_min(thing) < self.yc: output = output | self.children[1].collisions(thing) # And so on.
		if x_min(thing) < self.xc and y_max(thing) > self.yc: output = output | self.children[2].collisions(thing)
		if x_min(thing) < self.xc and y_min(thing) < self.yc: output = output | self.children[3].collisions(thing)
		return output

	def append(self, item):
		if self.leaf_node:
			# If this is a leaf node, well, that's not going to stay. First off, we undo that marker.
			self.leaf_node = False
			# Now we initialize all of the children, so that they're going to be leaf node quadtrees..
			self.children = [QuadTree(height = self.height-1) for i in bucket_indices]
			# Now make sure that the center is marked correctly given that the object we're adding is in the center.
			self.xc, self.yc = center_from_object(item)
			# Now we're not a leaf node, so regular append logic will apply.
			self.append(item)
		else:
			bucket_label = self.get_bucket_label(item)
			if self.height is 0 or bucket_label is -1:
				self.contents.append(item)
			else:
				self.children[bucket_label].append(item)

	def extend(self, items):
		# Seriously, who extends by an empty list? Dick.
		if len(items) is 0: 
			return
		# If only one object is being added, append it instead. Why are you using extend? Dolt.
		if len(items) is 1:
			self.append(items[0])
			return
		if self.leaf_node:
			# First things first, this is no longer a leaf node.
			self.leaf_node = False
			# Second things second, we're going to initialize the children.
			self.children = [QuadTree(height = self.height-1) for i in bucket_indices]
			# Third things third, we need to figure out where to locate our center. I'm not sure how this should be done!
			self.xc, self.yc = center_from_group(items)
			# Now just extend as normal.
			self.extend(items)
		else:
			# First off, let's get the ones that should go in the contents bucket.
			self.contents.extend([x for x in items if self.get_bucket_label(x) is -1])
			# For each bucket, extend it by those objects which should go in that bucket.
			for i in bucket_indices: self.children[i].extend([x for x in items if self.get_bucket_label(x) is i])

	def remove(self, item):
		"""Removes item from self. Returns False if the item isn't here, True if it was removed."""
		# TODO: check child nodes in order.
		# TODO: remove empty nodes.
		if self.leaf_node: return False

		if item in self.contents:
			self.contents.remove(item)
			# TODO: change this, and the other instance of this below, because len() might be slow?
			if len(self) is 0: 
				self.leaf_node = True
				self.children = []
			return True

		# Might be worth it to optimize this to check the most likely quadtrees first.
		for child in self.children:
			if child.remove(item): 
				if len(self) is 0: 
					self.leaf_node = True
					self.children = []
				return True
		return False

	def __contains__(self, item):
		"""Checks if item is in self.

		TODO: check children in order."""
		if self.leaf_node: return False

		if item in self.contents: return True
		# Might be worth it to optimize this to check the most likely quadtrees first.
		for child in self.children:
			if item in child: return True
	
	def __len__(self):
		if self.leaf_node: return 0

		return len(self.contents) + sum(len(tree) for tree in self.children)
	
	def status_rep(self, indent=''):
		if self.leaf_node: return []
		output = []
		output.append(indent + '{0} total, {1} here'.format(len(self), len(self.contents)))
		for child in self.children:
			output.extend(child.status_rep(indent + '--'))
		if indent is '': return '\n'.join(output)
		else: return output
	
class BruteList(list):
	"""A list with support for collision detection. This is mostly for comparison.

	I wrote this when I realized that the SortSearchList doesn't actually *work*, and I think I'm going to leave it here, because I like
	  that the way I've structured my classes meant that implementing a brute-force collision checker involved two new lines and one reference
	  changed (in QuadTree.__init__). Simplicity! Also, so straightforward. I feel good about this.
	"""
	def collisions(self, item): return set(x for x in self if x is not item and intersects(x, item))

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
	It's a big improvement over a brute-force search, but it's not as good as a quadtree. However, it produced really 
	  noticeable improvements when I used it as the supporting data structure for a quadtree. So that's why it's here.

	WARNING: This does NOT handle inverted shapes correctly. I'm not even sure if that's possible.
	CRIPES THIS IS SO BROKEN
	"""
	def __init__(self, input_list=None):
		list.__init__(self)
		if input_list is None: input_list = []
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

		#for other_item in self.minimums[index_minimum:]:
		for other_item in self.minimums:
			if other_item == item: continue
			# This is probably the most important part of this class. This says that we stop checking in
			# this direction, when we find an object whose minimum is beyond our maximum.
			if x_min( other_item ) > x_max( item ): break
			# If item intersects the item under consideration, then add it to the collision set.
			if intersects(item, other_item) is not None: output.add(other_item) 

		#for other_item in self.maximums[index_maximum:]:
		for other_item in self.maximums:
			if other_item == item: continue
			# As above, important line here - Except that now, we're going through the list of right extents (maxima), and therefore backwards.
			if x_max( other_item ) < x_min( item ): break
			if intersects(item, other_item) is not None: output.add(other_item)
		
		return output
