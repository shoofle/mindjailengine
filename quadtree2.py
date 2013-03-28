from vectors import v
import math
import random
import bisect
import shapes

y_min = lambda o: o.pos.y + o.shape.ybounds[0]
y_max = lambda o: o.pos.y + o.shape.ybounds[1]
x_min = lambda o: o.pos.x + o.shape.xbounds[0]
x_max = lambda o: o.pos.x + o.shape.xbounds[1]
split_threshhold = 5

def intersects(me, you):
	"""Return whether or not me and you are colliding. May very well be overwritten by the caller of the library."""
	return False if me.tangible == 0 or you.tangible == 0 else shapes.intersect(me, you)


class QuadTree(list):
	def __init__(self,items=[],center=v(0,0), height=8):
		self.height = height

		list.__init__(self, [ None, None, None, None ])

		self.xc,self.yc = center.x, center.y
		self.Items = SortSearchList([])
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
		
		... Also, there's no removal of empty subtrees.
		"""
		self.count = self.count - 1
		if obj in self.Items: 
			self.Items.remove(obj)
			return self.height

		out = False
		if x_min(obj) > self.xc:
			if y_min(obj) > self.yc: 
				# If it's in the northeast corner, we use this order.
				if self[0] is not None: out = out or self[0].remove(obj)
				if self[1] is not None: out = out or self[1].remove(obj)
				if self[2] is not None: out = out or self[2].remove(obj)
				if self[3] is not None: out = out or self[3].remove(obj)
			if y_max(obj) < self.yc: 
				# If it's in the southeast corner, we use this order.
				if self[1] is not None: out = out or self[1].remove(obj)
				if self[0] is not None: out = out or self[0].remove(obj)
				if self[2] is not None: out = out or self[2].remove(obj)
				if self[3] is not None: out = out or self[3].remove(obj)
			if not out: self.count = self.count + 1 
			# If it didn't get removed from any of them, then add 1 to the count again. Also, there was a problem.
			return out
		if x_max(obj) < self.xc:
			if y_min(obj) > self.yc: 
				# And so on.
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
		# If we didn't enter either of those if blocks, then the object overlaps the center line, but is not contained in self.Items. 
		# What we know now is that: if the object is in the quadtree, it's in a subtree. However, now, it would be found in the Items bucket.
		# Let's search to see if it's in any of the subtrees, just to be sure.
		if self[0] is not None: out = out or self[0].remove(obj)
		if self[1] is not None: out = out or self[1].remove(obj)
		if self[2] is not None: out = out or self[2].remove(obj)
		if self[3] is not None: out = out or self[3].remove(obj)
		if not out: self.count = self.count + 1
		return out

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




""" Library/whatever to do collision detection using a middle-complexity algorithm.

* x_min(obj), x_max(obj)  - utility functions which get the minimum and maximum extents of their input objects. May be discarded later for speed - rather than calling these functions, directly access the minimum and maximum fields in the object. For generality, these functions will remain for now.
* linearsortsearch(input_list)  - function which attempts to detect all collisions between objects in the input list.
  * input_list  - a list of objects. These have an accessible scalar x minimum property, as well as a maximum. They also need a position property, which is a vectors.vector.

The basic functioning is this: We wish to find all collisions in the input list of objects.
Before we start searching, we define some lists which will be useful in the main search.

* index_list  - this contains the list of indices of the input_list. It might be entirely unnecessary, if searching through (and sorting) input_list isn't too slow. However, if that *is* too slow, then we'll search through and sort the list of indices as here.
  The point of index_list is essentially to have a list of identifiers for all the objects we're searching. This will be useful for two lists which are the crux of this algorithm, which are...
* ascending_minimum  - The list of indices (thus, object identifiers) sorted by the object's minimum extent. Thusly, if Alice comes after Bob in the list, then Alice's minimum value is greater than Bob's minimum value.
* descending_maximum  - Similarly, the list of indices, sorted by their maximum extents in descending order. If Alice comes after Bob in the list, then Alice's maximum value is less than Bob's maximum value.

Now we move onto the search. We go through all the indices/identifiers in the index list.
For each index/identifier, we find the position in our ascending and descending search lists:
* index_minimum  - For our identifier, this variable holds the position of the identifier in the ascending_minimum list.
* index_maximum  - The same as index_minimum, but in the descending_maximum list instead.
Now we search through the ascending minimum list, starting at index_minimum. 
This step is sort of like scanning upward through our space, starting at the bottom edge of 
 the current object, and pausing each time we hit the bottom edge of an object.
 (Then, we check if the current object intersects with the object we encountered.)
 Also, at each object, we ask "is the object's bottom above our current object's top?"
 If it is, then we can break and move onto the next bit.
 If it's not, then we need to continue scanning upward.
The next bit is very similar to above, but it searches through the descending maximum list.
Rather than looking at the top edge of our object and scanning up, we look at the bottom
 and scan down - this is why the list of maximum extents is sorted in descending order!
 It's basically the same as before.
Now that we're done scanning, we can remove our current object from the lists to prevent 
 double-counting collisions


Okay, this is all well and good and stuff but there're obviously some problems.
Actually, not too many. The biggest problem is that this doesn't necessarily detect all the collisions. Say we're looking through our loop and checking some object A for all its collisions. 
We start at A's bottom and search upward. This misses all objects with bottom below A's. 
We then start at A's top and search downward. This misses all objects with top above A's.
If there is some object in both lists, then it will be missed altogether! Oops!
 So we miss all objects that have both extents outside of A's extents.
Also, if there are objects with bottom above A's bottom and top below A's top, they could be double-counted.
 So we (may?) double-count all objects that have both extents inside A's extents.

... Those are actually some pretty serious problems.

As for efficiency, the execution time depends on how fast the sorting runs. Also, if the world we're searching through is heavily squished along our sorting axis, then we'll do lots of comparisons between objects which are far away on the other axis.
However, it doesn't seem to run all that slowly, at least compared to the first working version of the quadtree. In fact, it runs about as fast as it takes to build and search a quadtree. Actually, no. Sometimes it does that. Sometimes it takes twice as long. It's not conclusive.

How can I improve this?
The biggest problem is the missed objects.
Now, how can we ensure that we find these objects?
We could just roll with the double-counting, which makes it run more loops.
"""


def get_object(index, self=None):
	return self.items[index]
###
# Linear Sort Search (on the x-axis)
###
class SortSearchList(list):
	def __init__(self, input_list=[]):
		list.__init__(self)
		list.extend(self,input_list)
		self.indices = range(len(self))
		self.make_minmax()


	def make_minmax(self):
		self.minimums = sorted(self.indices, key=self.get_x_min)
		self.maximums = sorted(self.indices, key=self.get_x_max)

	def get_x_min(self,integer):
		return x_min(self[integer])
	def get_x_max(self,integer):
		return x_max(self[integer])

	def extend(self, itemlist):
		list.extend(self, itemlist)
		self.indices = range(len(self))
		self.make_minmax()
	def insert(self, item):
		index = len(self)
		self.append(item)
		self.indices.append(index)
		# YO CHANGE THIS
		bisect.insort(self.minimums, index, key=self.get_x_min, testval=x_min(item))
		bisect.insort(self.maximums, index, key=self.get_x_max, testval=x_max(item))

	def remove(self, item):
		if item in self:
			index = self.index(item)
			try: self.minimums.remove(index)
			except ValueError: pass
			try: self.maximums.remove(index)
			except ValueError: pass
			try: self.indices.remove(index)
			except ValueError: pass
			return list.remove(self,item)
		else: return False
		
	def collisions(self,item):
		# Gotta find out where item would be if it were in self.items. How do? binary search?
		output = set()

		# YO CHANGE THIS
		index_minimum = bisect.bisect_left(self.minimums, x_min(item), key=self.get_x_min)
		index_maximum = bisect.bisect_left(self.maximums, x_max(item), key=self.get_x_max)

		for other_item in self.minimums[index_minimum:]:
			if self[other_item] == item: continue
			if x_min( self[other_item] ) > x_max( item ): break # Check to see if we're outside our item's extents
			inter = intersects(item,self[other_item])
			if inter is not None:
				output.add(self[other_item])
		for other_item in reversed(self.maximums[:index_maximum]):
			if self[other_item] == item: continue
			if x_max( self[other_item] ) < x_min( item ): break # Check to see if we're outside our item's extents
			inter = intersects(item,self[other_item])
			if inter is not None:
				output.add(self[other_item])
		return output

	def all_collisions(self):
		output = set()
		for item in self.indices:
			index_minimum = self.minimums.index(item)
			index_maximum = self.maximums.index(item)
	
			# Search through the [list of indices sorted by xmin, ascending] starting from our index and traveling up.
			# Stop when we're outside our object's extents.
			for other_item in self.minimums[index_minimum:]:
				if other_item == item: continue
				if x_min( self[other_item] ) > x_max( self[item] ): break # Check to see if we're outside our item's extents
				inter = intersects(self[item],self[other_item])
				if inter is not None:
					output.add((self[item],self[other_item],inter))
			# Remove our current index from the ascending minimum list.
			#self.minimums.remove(index)
	
			# Now search through the indices sorted by xmax, descending starting at our index, going down.
			for other_item in reversed(self.maximums[:index_maximum]):
				if other_item == item: continue
				if x_max( self[other_item] ) < x_min( self[item] ): break # Check to see if we're outside our item's extents
				inter = intersects(self[item],self[other_item])
				if inter is not None:
					output.add((self[item],self[other_item],inter))
			# Remove our current index from the descending maximum list.
			#self.maximums.remove(index)
		return output
