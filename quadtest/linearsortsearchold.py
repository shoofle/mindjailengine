from vectors import v
from shapes import intervalcompare

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

x_min = lambda obj: obj.xmin
x_max = lambda obj: obj.xmax
###
# Linear Sort Search (on the x-axis)
# Very unfinished.
###
def linearsortsearch(input_list):
	index_list = range(len(input_list)) # List holding the indices of all the objects.
	get_object = lambda index: input_list[index]

	x_min_index = lambda index: x_min( get_object(index) )
	x_max_index = lambda index: x_max( get_object(index) )

	# Sort the index list by minimum on the axis, ascending.
	ascending_minimum = sorted(index_list, key=x_min_index) 
	# Sort the index list by maximum on the axis, descending.
	descending_maximum= sorted(index_list, key=x_max_index, reverse = True)
	
	for index in index_list:
		index_minimum = minimum_ascending.index(index)
		index_maximum = maximum_descending.index(index)

		this_object = get_object(index)

		# Search through the [list of indices sorted by xmin, ascending] starting from our index and traveling up.
		# Stop when we're outside our object's extents.
		for other_index in minimum_ascending[index_minimum:]:
			if other_index == index: continue
			other_object = get_object(other_index)

			# Check to see if we're outside our test object's extents
			if x_min_index( other_index ) > x_max_index( index ): break	# We could check with a call by the indices...
			#if x_min( other_object ) > x_max( this_object ): break		# ... or call by the object.

			# Check to see if the objects are unintersecting.
			if not intersects(this_object, other_object): continue		# Same dichotomy as before.
			#if not intersects( get_object(index), get_object(other_index) ): continue
			
			# Collide the two objects. Same dichotomy as before.
			do_collide(this_object, other_object)
			#do_collide( get_object(index), get_object(other_index) )
			do_collide(other_object, this_object)
			#do_collide( get_object(other_index), get_object(index) )

		# Remove our current index from the ascending minimum list.
		minimum_ascending.remove(index)

		# Similarly to before, now search through the indices sorted by xmax, descending starting at our index, going down.
		for other_index in maximum_descending[index_maximum:]:
			if other_index == index: continue

			# Check to see if we're outside our test object's extents
			if x_max_index( other_index ) < x_min_index( index ): break	# We could check with a call by the indices...
			#if x_min( other_object ) > x_max( this_object ): break		# ... or call by the object.

			# Check to see if the objects are unintersecting.
			if not intersects(this_object, other_object): continue		# Same dichotomy as before.
			#if not intersects( get_object(index), get_object(other_index) ): continue

			# Collide the two objects. Same dichotomy as before.
			do_collide(this_object, other_object)
			#do_collide( get_object(index), get_object(other_index) )
			do_collide(other_object, this_object)
			#do_collide( get_object(other_index), get_object(index) )

		# Remove our current index from the descending maximum list.
		maximum_descending.remove(index)

