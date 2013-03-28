from vectors import v
from shapes import intervalcompare
import math
import random
import time
import quadtree
import linearsortsearch

# Restrictions on our random test items. (They are circles or squares!)
N_loops = 1
N_items = 300

max_radius = 10
min_radius = 10

max_x = 600.
min_x = 0.
max_y = 600.
min_y = 0.

squarefraction = .6

numcellsx = 60
numcellsy = 40

listcount = 6
diffcount = 4

sortlist = True
treelist = True
qsdiff = True
sqdiff = True





random.seed()

#    HEADER = '\033[95m'
c = {"purple":'\033[95m', "red":'\033[31;m'}
c[0],c[1],c[2],c[3],c[4],c[5],c[6],c[7] = \
	c["black"], c["red"], c["green"], c["yellow"], c["blue"], c["magenta"], c["cyan"], c["white"] = \
	'\033[30;m','\033[31;m','\033[32;m','\033[33;m','\033[34;m','\033[35;m','\033[36;m','\033[37;m'
c[10],c[11],c[12],c[13],c[14],c[15],c[16],c[17] = \
	c["onblack"], c["onred"], c["ongreen"], c["onyellow"], c["onblue"], c["onmagenta"], c["oncyan"], c["onwhite"] = \
	'\033[;40m','\033[;41m','\033[;42m','\033[;43m','\033[;44m','\033[;45m','\033[;46m','\033[;47m'

c["whiteonred"] = c["white"]+c["onred"]

c["bold"] = '\033[1m'

c["whiteonblack"] = '\033[0m'
c["none"] = c["whiteonblack"]
c["end"] = c["whiteonblack"]


# Test item class.
class RandomItem:
	def __init__(self):
		self.rect = False
		#if random.random() < squarefraction: self.rect = True
		self.radius = random.uniform(min_radius,max_radius)
		self.x = random.uniform(min_x,max_x)
		#if self.x - self.radius < min_x: self.x = self.x - ((self.x-self.radius)-min_x)
		#if self.x + self.radius > max_x: self.x = self.x - ((self.x+self.radius)-max_x)
		self.y = random.uniform(min_y,max_y)
		#if self.y - self.radius < min_y: self.y = self.y - ((self.y-self.radius)-min_y)
		#if self.y + self.radius > max_y: self.y = self.y - ((self.y+self.radius)-max_y)

		self.pos = v(self.x,self.y)

		self.halfheight = self.halfwidth = self.radius
		#if self.rect:
		#	self.halfheight = random.uniform(math.ceil(self.radius/10), self.radius)
		#	self.halfwidth = math.sqrt(self.radius*self.radius - self.halfheight*self.halfheight)
		self.xmin = self.x - self.halfwidth
		self.xmax = self.x + self.halfwidth
		self.ymin = self.y - self.halfheight
		self.ymax = self.y + self.halfheight

def intersection_vector(me, you): # returns the vector to move item1 to fix the intersection with item2
	sep = me.pos - you.pos
	if abs(sep) < me.radius+you.radius:
		return sep
	else:
		return None
	sep = me.pos - you.pos
	if sep.x == 0 and sep.y == 0:
		usep = v(0,-1)
		msep = 0
	else:
		msep = abs(sep)
		usep = sep.unit()

	output = intervalcompare( (-me.radius, me.radius), (-you.radius, you.radius), msep, meinv=0, othinv=0 )

	if output == None : return None
	return output*usep




print "Generating collection of items..."
# Generate a collection of N_items random items.
item_list = []
for i in range(N_items):
	item_list.append(RandomItem())
print "Done."
"""
# Draw our random items (more or less) in the terminal.
xpercell = (max_x - min_x)/(numcellsx+1)
xoffset = xpercell/2
ypercell = (max_y - min_y)/(numcellsy+1)
yoffset = ypercell/2

current = v(xoffset,yoffset)
curx = xoffset
cury = yoffset

print "\n\nWorking on (very slow) display of stage."

alphabet = "abcdefghijklmnopqrstuvwxyz"
alphabet = alphabet + alphabet.swapcase()
outputstring = ""+ c['none']
for j in range(numcellsy):
	for i in range(numcellsx):
		current = v(xoffset + i*xpercell, yoffset + j*ypercell)
		cellstring = "."
		countofoverlaps=0
		for num, item in enumerate(item_list):
			inside = False
			if item.rect: 
				if (item.xmin < current.x < item.xmax) and (item.ymin < current.y < item.ymax): inside = True
			else:
				if abs((current-item.pos).x) > item.radius: continue
				if abs((current-item.pos).y) > item.radius: continue
				if abs(current-item.pos) < item.radius: inside = True
			if inside:
				countofoverlaps += 1
				numout = num
				cellstring = alphabet[num % 52]
				if countofoverlaps > 1: cellstring = c['bold'] + c['whiteonred'] + "{0}".format(countofoverlaps)
				#if countofoverlaps > 2: cellstring = c['bold'] + cellstring
		cellstring = '\b' + cellstring + c['none']
		#print cellstring,
		outputstring += " " + cellstring + c['none']
	outputstring += "\n"
print outputstring + c['none']
print "Done."
"""






"""
###
# Linear Sort Search (x-axis)
# Very unfinished.
###
def naive(inlist):
	minimumy = lambda obj: obj.xmin
	maximumy = lambda obj: obj.xmax
	testmin = lambda num: inlist[num].xmin
	testmax = lambda num: inlist[num].xmax
	listofobjects = range(len(inlist))
	minimum_ascending = sorted(range(len(inlist)), key=testmin)
	maximum_descending = sorted(range(len(inlist)), key=testmax, reverse = True)
	
	for obj_index in listofobjects:
		min_index = minimum_ascending.index(obj_index)
		max_index = maximum_descending.index(obj_index)
		for otherobj_index in minimum_ascending[min_index:]:
			if otherobj_index == obj_index: continue
			if minimumy(inlist[otherobj_index]) > maximumy(inlist[obj_index]): break
			if abs(inlist[obj_index].pos - inlist[otherobj_index].pos) > inlist[obj_index].radius + inlist[otherobj_index].radius: continue
			do_collide(inlist[obj_index],inlist[otherobj_index])
			do_collide(inlist[otherobj_index],inlist[obj_index])
		minimum_ascending.remove(obj_index)
		for otherobj_index in maximum_descending[max_index:]:
			if otherobj_index == obj_index: continue
			if maximumy(inlist[otherobj_index]) < minimumy(inlist[obj_index]): break
			if abs(inlist[obj_index].pos - inlist[otherobj_index].pos) > inlist[obj_index].radius + inlist[otherobj_index].radius: continue
			do_collide(inlist[obj_index],inlist[otherobj_index])
			do_collide(inlist[otherobj_index],inlist[obj_index])
		maximum_descending.remove(obj_index)
"""

print "Defining stuff for the comparison and collision reaction..."
collist  = set()
collist2 = set()
def do_collide(x, y, vector=v(0,0)):
	#collist.add("{0} vs {1}:    \t[distance: {4:0.3f}]\t [radius sum: {5:0.3f}]".format(\
	#	item_list.index(x),item_list.index(y), x,y, abs(x.pos-y.pos),x.radius+y.radius ) )
	collist.add((item_list.index(x),item_list.index(y)))
	collist2.add((item_list.index(x),item_list.index(y)))
def intersects(x, y):
	return abs(x.pos - y.pos) < x.radius + y.radius
quadtree.intersects = intersects
quadtree.do_collide = do_collide
linearsortsearch.intersects = intersects
linearsortsearch.do_collide = do_collide
print "Done."

lss = lss_sq = 0
tree_build = tree_build_sq = 0
tree_search = tree_search_sq = 0
tree_time = tree_time_sq = 0

for k in range(N_loops):
	# Generate our items.
	item_list = []
	for i in range(N_items):
		item_list.append(RandomItem())

	# Test the linear sort search.
	starttime = time.time()
	linearsortsearch.collisions(item_list)
	timediff = time.time()-starttime

	lss += timediff
	lss_sq += timediff**2

	collist_lss = set(collist)

	collist = set()

	# Test the quadtree search.
	starttime = time.time()
	tree = quadtree.QuadTree(item_list, center=v((max_x-min_x)/2,(max_y-min_y)/2), height=5)
	tree_build_time = time.time() - starttime

	tree_build += tree_build_time
	tree_build_sq += tree_build_time**2

	starttime = time.time()
	for obj in item_list:
		tree.collisions(obj)
	tree_search_time = time.time() - starttime

	tree_search += tree_search_time
	tree_search_sq += tree_search_time**2

	tree_time += tree_build_time+tree_search_time
	tree_time_sq += (tree_build_time+tree_search_time)**2


lss_average = lss / N_loops
tree_time_average = tree_time / N_loops
tree_build_average = tree_build / N_loops
tree_search_average = tree_search / N_loops
print "Ran {0} tests with {1} randomly-generated circles.".format(N_loops, N_items)
print "Sort search: {0:.3f}".format(lss_average)
print "Tree search: {0:.3f}".format(tree_time_average)
print "Average tree-build time: {0:.3f}".format(tree_build_average)
print "Average tree-search time: {0:.3f}".format(tree_search_average)
print "Search time improvement: {0:.1f}% of the naive time".format( 100*tree_search_average / lss_average )




# Generate our items.
item_list = []
for i in range(N_items):
	item_list.append(RandomItem())

collist = set()
collist2 = set()
# Test the linear sort search.
starttime = time.time()
linearsortsearch.collisions(item_list)
lsstime = time.time() - starttime
collist_lss = set(collist)
collist2_lss = set(collist2)

collist = set()
collist2 = set()
# Test the quadtree search.
starttime = time.time()
tree = quadtree.QuadTree(item_list, center=v((max_x-min_x)/2,(max_y-min_y)/2), height=5)
for obj in item_list:
	tree.collisions(obj)
quadtime = time.time() - starttime
collist_tree = set(collist)
collist2_tree = set(collist2)


print "\n\nExample search results:"
if sortlist:
	print "Collisions detected by the sort:"
	for i,string in enumerate( sorted(collist_lss) ):
		print "{0}. {1}".format(i,string)
		if i > listcount:
			print "..."
			break
	print "Total collisions found: {0}".format(len(collist_lss))
if treelist:
	print "\nCollisions detected by the quadtree:"
	for i,string in enumerate( sorted(collist_tree) ):
		print "{0}. {1}".format(i,string)
		if i > listcount:
			print "..."
			break
	print "Total collisions found: {0}".format(len(collist_tree))


if sqdiff:
	print "\nCollisions found by the sort but not by the quadtree:"
	for i,string in enumerate( sorted(collist_lss-collist_tree) ):
		print "{0}. {1}".format(i,string)
		if len(collist_lss-collist_tree) < 10: continue
		if i > diffcount:
			print "..."
			break
	print "Difference length: {0}".format(len(collist_lss - collist_tree))
if qsdiff:
	print "\nCollisions found by the quadtree but not by the sort:"
	for i,string in enumerate( sorted(collist_tree-collist_lss) ):
		print "{0}. {1}".format(i,string)
		if len(collist_tree-collist_lss) < 10: continue
		if i > diffcount:
			print "..."
			break
	print "Difference length: {0}".format(len(collist_tree - collist_lss))

print "Took {0:.2f} seconds to sortsearch.".format(lsstime)
print "Took {0:.2f} seconds to quadtree search.".format(quadtime)
