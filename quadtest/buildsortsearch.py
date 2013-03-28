from vectors import v
from shapes import intervalcompare
import bisect
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
def intersects(x,y):
	return abs(x.pos-y.pos) < x.radius + y.radius
def do_collide(x,y):
	pass

x_min = lambda obj: obj.xmin
x_max = lambda obj: obj.xmax

def get_object(index, self=None):
	return self.items[index]
###
# Linear Sort Search (on the x-axis)
# Very unfinished.
###
class SortSearch:
	def __init__(self, input_list=[]):
		self.items = input_list
		self.length = len(self.items)
		self.indices = range(self.length)
		self.make_minmax()

	def make_minmax(self):
		self.ascending_minimums = sorted(self.indices, key=self.get_x_min)
		self.descending_maximums= sorted(self.indices, key=self.get_x_max, reverse=True)

	def get_x_min(self,integer):
		return x_min(self.items[integer])
	def get_x_max(self,integer):
		return x_max(self.items[integer])

	def extend(self, itemlist):
		self.items.extend(itemlist)
		self.indices.extend(range(self.length,self.length+len(itemlist)))
		self.length = self.length + len(itemlist)
		self.make_minmax()
	def insert(self, item):
		self.items.append(item)
		self.indices = self.indices + [self.length]
		self.length = self.length + 1
		self.make_minmax()
	def remove(self, item):
		if item in self.items:
			index = self.items.index(item)
			output = self.items.remove(item)
			self.indices.remove(index)
			self.make_minmax()
			return output
		else: return False
		
	def collisions(self,item):
		# Gotta find out where item would be if it were in self.items. How do? binary search?
		pass
	def all_collisions(self):
		for item in self.items:
			index_minimum = ascending_minimum.index(item)
			index_maximum = descending_maximum.index(item)
	
			# Search through the [list of indices sorted by xmin, ascending] starting from our index and traveling up.
			# Stop when we're outside our object's extents.
			for other_item in ascending_minimum[index_minimum:]:
				if other_item == item: continue
				if x_min( other_item ) > x_min( item ): break # Check to see if we're outside our item's extents
				if intersects(item, other_item):
					do_collide(item, other_item)
			# Remove our current index from the ascending minimum list.
			#ascending_minimum.remove(index)
	
			# Now search through the indices sorted by xmax, descending starting at our index, going down.
			for other_item in descending_maximum[index_maximum:]:
				if other_item == item: continue
				if x_min( other_item ) < x_min( item ): break # Check to see if we're outside our item's extents
				if intersects(item, other_item):
					do_collide(item, other_item)
			# Remove our current index from the descending maximum list.
			#descending_maximum.remove(index)
