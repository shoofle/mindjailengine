from vectors import v
import pyglet
import math
import random
import bisect
import shapes

"""I seem to have written a startling number of data structures for collision detection. Currently using SpatialGrid, which is a spatial hashing implementation."""

# These get used a LOT.
y_min = lambda o: o.pos.y + o.shape.ybounds[0]
y_max = lambda o: o.pos.y + o.shape.ybounds[1]
x_min = lambda o: o.pos.x + o.shape.xbounds[0]
x_max = lambda o: o.pos.x + o.shape.xbounds[1]

split_threshhold = 5 # When you bulk-add a bunch of objects, this serves the purpose of saying "hey, if this quadtree's going to have 
# fewer than this many objects, we might as well just chuck'em all in the Items bucket." I don't even know if this is a good *idea*. 
# It's not used very much.
MAX_DEPTH = 15

def center_from_object(thing): return thing.pos

def center_from_group(things): return sum(map(lambda x: x.pos, things),v(0,0))/len(things)

def intersects(a, b):
	return a is not b and x_min(a) < x_max(b) and x_max(a) > x_min(b) and y_min(a) < y_max(b) and y_max(a) > y_min(b)

class DataStructure(object):
	def __init__(self, items): pass
	def collisions(self, item): return set()
	def append(self, item): pass
	def extend(self, items): pass
	def remove(self, item): pass
	def __contains__(self, item): pass
	def __len__(self): return 0
	def status_rep(self, indent=''): return '' # Optional. Used without checking if it's there, though.
	def draw(self): pass # Optional.


class BruteList(list):
	"""A list with support for brute-force collision detection. You *are* the brute squad."""
	def collisions(self, item): return set(x for x in self if x is not item and intersects(x, item))


class SpatialGrid(object):
	"""A loose spatial grid. Contains a dict mapping tuples to a secondary container. Indexes objects to the grid square containing their center.

	When you test to see if an object collides, you have to check a few grid squares around where it belongs, 
	  to make sure you get possible overlaps. 
	This structure relies on the supposition that the objects being stored in it are smaller than max_size - 
	  so all the objects they can collide with are either within the same square as them, or in one of the neighboring squares.
	"""
	def __init__(self, items=None, max_size=100):
		self.grid_size = max_size
		self.grid = dict()

		# Vertex list for drawing grid squares.
		self.vlist = pyglet.graphics.vertex_list(4, 'v3f')
		self.vlist.vertices[0:3] = [0, 0, 0]
		self.vlist.vertices[3:6] = [max_size, 0, 0]
		self.vlist.vertices[6:9] = [max_size, max_size, 0]
		self.vlist.vertices[9:12] = [0, max_size, 0]
		self.color = random.random(), random.random(), random.random()

		if max_size > 1000: self.secondary = BSPTree()
		else: self.secondary = SpatialGrid(max_size=self.grid_size*2) # TODO: Change this to generate these on demand, rather than immediately.
	def too_big(self, item): 
		""" Returns true if the object is too big to fit in this grid. """
		return x_max(item)-x_min(item) >= self.grid_size or y_max(item)-y_min(item) >= self.grid_size
#		return max(x_max(item)-x_min(item), y_max(item)-y_min(item)) >= self.grid_size
	def grid_square(self, item): 
		""" Return the grid square occupied by item. """
		return int(math.floor(item.pos.x/self.grid_size)), int(math.floor(item.pos.y/self.grid_size))
		# This uses math.floor, because int() casts toward zero rather than toward -inf. According to some quick timeit tests, this results in a loss of speed around 16%. Not huge, but not tiny.
	def grid_space(self, item): 
		""" Returns a generator for the grid squares the object might be contacting. Includes neighboring grid squares.. """
		min_x, min_y = int(math.floor(x_min(item)/self.grid_size)), int(math.floor(y_min(item)/self.grid_size))
		max_x, max_y = int(math.floor(x_max(item)/self.grid_size)), int(math.floor(y_max(item)/self.grid_size))
		return ((i,j) for i in range(min_x-1, max_x+2) for j in range(min_y-1, max_y+2) if (i,j) in self.grid)
	def collisions_with_rect(self, rect):
		if hasattr(self.secondary,'collisions_with_rect'): output = self.secondary.collisions_with_rect(rect)
		else: output = set()

		min_x, min_y = int(math.floor(rect[0][0]/self.grid_size)), int(math.floor(rect[1][0]/self.grid_size))
		max_x, max_y = int(math.floor(rect[0][1]/self.grid_size)), int(math.floor(rect[1][1]/self.grid_size))
		buckets = (self.grid[(i,j)] for i in range(min_x-1, max_x+2) for j in range(min_y-1, max_y+2) if (i,j) in self.grid)

		for b in buckets:
			output = output | set(item for item in b if x_max(item) > rect[0][0] and x_min(item) < rect[0][1] and y_max(item) > rect[1][0] and y_min(item) < rect[1][1])
		return output
	def collisions(self, item):
		""" Returns all objects colliding with this one. """
		# No idea how reduce compares to other things, in terms of speed.
		return reduce(lambda s, t: s | self.grid[t].collisions(item), self.grid_space(item), self.secondary.collisions(item))
	def append(self, item):
		""" Add item to the spatial grid. If it is too big, it will get bumped up to the secondary data structure. """
		if self.too_big(item): self.secondary.append(item)
		else:
			location = self.grid_square(item)
			if location not in self.grid: self.grid[location] = BruteList() # This decides the secondary data structure.
			self.grid[location].append(item)
	def extend(self, items): 
		self.secondary.extend([i for i in items if self.too_big(i)])
		for i in items: 
			if not self.too_big(i): self.append(i)
	def remove(self, item):
		if self.too_big(item) and item in self.secondary: self.secondary.remove(item)
		else:
			location = self.grid_square(item)
			if location in self.grid and item in self.grid[location]:
				self.grid[location].remove(item)
				if len(self.grid[location]) is 0: del self.grid[location]
			else: 
				for l in self.grid.keys():
					if item in self.grid[l]: self.grid[l].remove(item)
					if len(self.grid[l]) is 0: del self.grid[l]
	def __contains__(self, item):
		if self.too_big(item) and item in self.secondary: return True
		location = self.grid_square(item)
		if location in self.grid and item in self.grid[location]: return True
		return any(item in self.grid[l] for l in self.grid)
	def __len__(self): return len(self.secondary) + sum(map(lambda x: len(self.grid[x]), self.grid))
	def status_rep(self, indent=''):
		num_in_grid = len(self) - len(self.secondary)
		num_off_grid = len(self.secondary)
		if num_in_grid is 0: return "Nada.\n{}\n\n".format(self.secondary.status_rep() if len(self.secondary) > 0 else '')
		num_grid_squares = len(self.grid)
		ave_occupancy = 1.0*num_in_grid/num_grid_squares
		neighbors = 0
		n_max = 0
		for i,j in self.grid:
			n_here = 0
			for t,r in ((u,v) for u in range(i-1, i+2) for v in range(j-1, j+2) if (u,v) in self.grid):
				n_here += len(self.grid[(t,r)])
			n_max = max(n_here,n_max)
			neighbors += n_here
		ave_neighbors = 1.0*neighbors/num_in_grid
		return "Number in the grid: {}\nNumber off the grid: {}\nNumber of grid squares: {}\nAverage occupancy of grid squares: {}\nAverage number of neighbors: {}\nMax neighbors: {}\nTotal Neighbors: {}\n\n".format(num_in_grid, num_off_grid, num_grid_squares, ave_occupancy, ave_neighbors, n_max, neighbors) + (self.secondary.status_rep() if len(self.secondary) > 0 else '')
	def draw(self):
		for x,y in self.grid:
			pyglet.gl.glPushMatrix()
			pyglet.gl.glTranslatef(x*self.grid_size, y*self.grid_size, 0)
			pyglet.gl.glColor3f(self.color[0], self.color[1], self.color[2])
			self.vlist.draw(pyglet.gl.GL_LINE_LOOP)
			pyglet.gl.glPopMatrix()
		if hasattr(self.secondary, 'draw'): self.secondary.draw()









class MultistoreSpatialGrid(object):
	"""A loose spatial grid. Contains a dict mapping tuples to a secondary container. Indexes objects into *all* the grid squares they occupy.

	When you test to see if an object collides, you have to check a few grid squares around where it belongs, 
	  to make sure you get possible overlaps. 
	This structure relies on the supposition that the objects being stored in it are smaller than max_size - 
	  so all the objects they can collide with are either within the same square as them, or in one of the neighboring squares.
	"""
	def __init__(self, items=None, max_size=100):
		self.grid_size = max_size
		self.grid = dict()
		self.count = 0

		self.vlist = pyglet.graphics.vertex_list(4, 'v3f')
		self.vlist.vertices[0:3] = [0, 0, 0]
		self.vlist.vertices[3:6] = [max_size, 0, 0]
		self.vlist.vertices[6:9] = [max_size, max_size, 0]
		self.vlist.vertices[9:12] = [0, max_size, 0]
		self.color = random.random(), random.random(), random.random()

		if max_size > 1000: self.secondary = BSPTree()
		else: self.secondary = MultistoreSpatialGrid(max_size = max_size*2) # SpatialGrid(max_size=self.grid_size*2)
	def too_big(self, item): return max(x_max(item)-x_min(item), y_max(item)-y_min(item)) > self.grid_size/2
	def grid_squares(self, item):
		min_x, min_y = int(math.floor(x_min(item)/self.grid_size)), int(math.floor(y_min(item)/self.grid_size))
		max_x, max_y = int(math.floor(x_max(item)/self.grid_size)), int(math.floor(y_max(item)/self.grid_size))
		return ((i,j) for i in range(min_x, max_x+1) for j in range(min_y, max_y+1))
	def collisions(self, item):
		output = self.secondary.collisions(item)
		for l in self.grid_squares(item):
			if l in self.grid:
				output = output | self.grid[l].collisions(item)
		return output
	def append(self, item):
		if self.too_big(item): self.secondary.append(item)
		else: 
			self.count = self.count + 1
			for l in self.grid_squares(item): 
				if l not in self.grid: self.grid[l] = BruteList()
				self.grid[l].append(item)
	def extend(self, items): 
		self.secondary.extend([i for i in items if self.too_big(i)])
		for i in items:
			if not self.too_big(i): self.append(i)
	def remove(self, item):
		if self.too_big(item): 
			self.secondary.remove(item)
		else:
			self.count = self.count - 1
			for l, g in self.grid.items():
				if item in g: g.remove(item)
				if len(g) is 0: del self.grid[l]
	def __contains__(self, item):
		return any(item in self.grid[l] for l in self.grid_squares(item) if l in self.grid) or any(item in self.grid[l] for l in self.grid)
	#	for l in self.grid_squares(item):
	#		if l in self.grid and item in self.grid[l]: return True
	#	return any(item in self.grid[l] for l in self.grid)
	def __len__(self): return self.count + len(self.secondary)
	def draw(self):
		for x,y in self.grid:
			pyglet.gl.glPushMatrix()
			pyglet.gl.glTranslatef(x*self.grid_size, y*self.grid_size, 0)
			pyglet.gl.glColor3f(self.color[0], self.color[1], self.color[2])
			self.vlist.draw(pyglet.gl.GL_LINE_LOOP)
			pyglet.gl.glPopMatrix()
		if hasattr(self.secondary, 'draw'): self.secondary.draw()


class BSPTree(object):
	"""This is a Binary Space Partitioning tree, which at every level divides space into two half-planes.

	TODO: This is in need of a (more) efficient data structure for storing the contents bucket.
	TODO: Efficiently rebalance when necessary.
	TODO: Right now it is always axis-aligned - alternating height values alternate whether it splits on the x axis or the y axis. In theory, it should
	  adjust its splitting axis to the data it's holding.
	"""
	def __init__(self, items=None, center=None, height=0, normal=None, offset=0):
		self.leaf_node = True
		self.offset = offset
		self.height = height

		if self.height%2: 
			self.min_extent, self.max_extent = x_min, x_max
			e = y_min, y_max
		else: 
			self.min_extent, self.max_extent = y_min, y_max
			e = x_min, x_max

		if self.height <= MAX_DEPTH+1:
			self.left, self.center, self.right = BSPTree(height=self.height+1), BruteList(), BSPTree(height=self.height+1)
		else:
			self.left, self.center, self.right = None, BruteList(), None
		
		if items is not None: self.extend(items)

	def collisions(self, thing):
		"""Return a set of all the objects in self colliding with thing."""
		if self.leaf_node: return set()
		
		output = self.center.collisions(thing)
		if self.min_extent(thing) < self.offset: output = output | self.left.collisions(thing)
		if self.max_extent(thing) > self.offset: output = output | self.right.collisions(thing)

		return output

	def append(self, item):
		if self.leaf_node:
			self.leaf_node = False # First things first, this is no longer a leaf node.
			center = center_from_object(item)
			self.offset = center.x if self.height%2 else center.y # Fix these references to vectors

			self.append(item) # Now we're not a leaf node, so regular append logic will apply.
		else:
			if self.height > MAX_DEPTH: return self.center.append(item)

			if self.max_extent(item) < self.offset: return self.left.append(item)
			if self.min_extent(item) > self.offset: return self.right.append(item)
			return self.center.append(item)

	def extend(self, items):
		if len(items) is 0: return # Seriously, who extends by an empty list? Dick.
		if len(items) is 1: return self.append(items[0])# If only one object is being added, append it instead. Why are you using extend? Dolt.
		if self.leaf_node:
			self.leaf_node = False # First things first, this is no longer a leaf node.
			center = center_from_group(items)
			self.offset = center.x if self.height%2 else center.y # Fix these references to vectors
			
			self.extend(items) # Now just extend as normal.
		else:
			if self.height > MAX_DEPTH: return self.center.extend(items)

			self.left.extend([a for a in items if self.max_extent(a) < self.offset])
			self.center.extend([a for a in items if self.min_extent(a) <= self.offset <= self.max_extent(a)])
			self.right.extend([a for a in items if self.max_extent(a) > self.offset])

	def remove(self, item):
		"""Removes item from self. Returns False if the item isn't here, True if it was removed."""
		if self.leaf_node: return False

		if item in self.left: self.left.remove(item)
		elif item in self.center: self.center.remove(item)
		elif item in self.right: self.right.remove(item)

		if len(self) is 0: self.leaf_node = True
	def __contains__(self, item):
		if self.leaf_node: return False
		return item in self.left or item in self.center or item in self.right
	def __len__(self): 
		if self.leaf_node: return 0 
		return len(self.left) + len(self.center) + len(self.right)
	def status_rep(self, indent=''):
		if self.leaf_node: return []
		output = []
		output.extend(self.left.status_rep(indent + '--'))
		output.append(indent + '{0} total, {1} here, divided on {2} at {3}'.format(len(self), len(self.center), 'x' if self.height%2 else 'y', self.offset))
		output.extend(self.right.status_rep(indent + '--'))
		if indent is '': return '\n'.join(output)
		return output


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
	bucket_indices = (0,1,2,3)
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
			self.children = [QuadTree(height = self.height-1) for i in QuadTree.bucket_indices]
			# Now make sure that the center is marked correctly given that the object we're adding is in the center.
			center = center_from_object(item)
			self.xc, self.yc = center.x, center.y
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
			self.children = [QuadTree(height = self.height-1) for i in QuadTree.bucket_indices]
			# Third things third, we need to figure out where to locate our center. I'm not sure how this should be done!
			center = center_from_group(items)
			self.xc, self.yc = center.x, center.y
			# Now just extend as normal.
			self.extend(items)
		else:
			# First off, let's get the ones that should go in the contents bucket.
			self.contents.extend([x for x in items if self.get_bucket_label(x) is -1])
			# For each bucket, extend it by those objects which should go in that bucket.
			for i in QuadTree.bucket_indices: self.children[i].extend([x for x in items if self.get_bucket_label(x) is i])

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
	
class IntervalTree(object):
	"""A tree for storing intervals along some axis.
	
	This wasn't found to make a noticeable improvement over the BruteList on the testbed level. Let's leave it here in the graveyard.
	The point of this data structure is to store the intervals a bunch of objects occupy on some axis. This was supposed to improve the BSPTree.
	It didn't. Too slow in python. This'd probably make sense in an external library, but it doesn't work here."""
	def __init__(self, input_list=None, extents=(x_min, x_max)):
		self.leaf_node = True
		self.center = 0
		self.left, self.right = None, None
		self.by_left_extent, self.by_right_extent = [], []
		self.min_extent, self.max_extent = extents

		if input_list is not None: self.extend(input_list)
	
	def append(self, item):
		if self.leaf_node:
			self.leaf_node = False
			self.left, self.right = IntervalTree(), IntervalTree()
			self.center = (self.min_extent(item) + self.max_extent(item))/2
		
			self.append(item)
		else:
			if self.max_extent(item) < self.center: return self.left.append(item)
			if self.min_extent(item) > self.center: return self.right.append(item)

			self.by_left_extent.append(item)
			self.by_left_extent.sort(key=self.min_extent)
			self.by_right_extent.append(item)
			self.by_right_extent.sort(key=self.max_extent)
	def extend(self, items):
		if len(items) is 0: return
		if len(items) is 1: self.append(items[0])
		if self.leaf_node:
			self.leaf_node = False
			self.left, self.right = IntervalTree(), IntervalTree()
			self.center = (sum(map(self.min_extent, items)) + sum(map(self.max_extent, items)))/(2*len(items))

			self.extend(items)
		else:
			self.left.extend([a for a in items if self.max_extent(a) < self.center])
			self.right.extend([a for a in items if self.min_extent(a) > self.center])

			here = [a for a in items if self.min_extent(a) < self.center < self.max_extent(a)]
			self.by_left_extent.extend(here)
			self.by_left_extent.sort(key=self.min_extent)
			self.by_right_extent.extend(here)
			self.by_right_extent.sort(key=self.max_extent)
	def remove(self, item):
		if self.leaf_node: return False
		if item in self.by_left_extent:
			self.by_left_extent.remove(item)
			self.by_right_extent.remove(item)
		elif item in self.left: self.left.remove(item)
		elif item in self.right: self.right.remove(item)
		if len(self) is 0: self.leaf_node = True
	def collisions(self, item):
		if self.leaf_node: return set()
		output = set()
		min_item, max_item = self.min_extent(item), self.max_extent(item)
		if max_item < self.center:
			output = output | self.left.collisions(item)
			for i in self.by_left_extent:
				if self.min_extent(i) > max_item: break
				elif intersects(i, item) and i is not item: output.add(i)
		elif min_item < self.center < max_item:
			output = output | self.left.collisions(item)
			output = set(a for a in self.by_left_extent if intersects(a, item) and a is not item)
			output = output | self.right.collisions(item)
		elif self.center < min_item:
			output = output | self.right.collisions(item)
			for i in self.by_right_extent:
				if self.max_extent(i) < min_item: break
				elif intersects(i, item) and i is not item: output.add(i)
		return output
	def __contains__(self, item):
		if self.leaf_node: return False
		return item in self.by_left_extent or item in self.left or item in self.right
	def __len__(self):
		if self.leaf_node: return 0
		return len(self.left) + len(self.right) + len(self.by_left_extent)


# Linear Sort Search (on the x-axis)
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

	This collision detector only works if you run every object through it - in other words, if you only test some portion of your world against this structure,
	  it won't find some collisions. You have to test every object *in* this structure against this structure.
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
