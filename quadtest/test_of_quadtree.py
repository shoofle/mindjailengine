from vectors import v
from shapes import intervalcompare
import math
import random
import time
import quadtree

# Restrictions on our random test items. (They are circles or squares!)
N_loops = 1
N_items = 100

max_radius = 100
min_radius = 10

max_x = 2000.
min_x = 0.
max_y = 2000.
min_y = 0.

squarefraction = .6

numcellsx = 300
numcellsy = 150

listcount = 6
diffcount = 4







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
# We want to generate a collection of 50 random items.

item_list = []

# Generate our items.
for i in range(N_items):
	item_list.append(RandomItem())


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



print "Defining stuff for the comparison..."
collist = set()
def do_collide(item1, item2, vector=v(0,0)):
	collist.add("{0} vs {1}:     \t({2.x:0.2f},{2.y:0.2f}) - ({3.x:0.2f},{3.y:0.2f})   \t[distance: {4:0.3f}]\t [radius sum: {5:0.3f}]".format(item_list.index(item1),item_list.index(item2),item1, item2,abs(item1.pos-item2.pos),item1.radius+item2.radius))
print "Done."




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


collist = set()
sumna = sumna2 = sumqb = sumqb2 = sumqs = sumqs2 = sumqa = sumqa2 = 0

for k in range(N_loops):
	item_list = []
	# Generate our items.
	for i in range(N_items):
		item_list.append(RandomItem())
	starttime = time.time()
	naive(item_list)
	naivetime = time.time()-starttime
	collist_naive = set(collist)
	starttime = time.time()
	tree = quadtree.QuadTree(item_list, center=v((max_x-min_x)/2,(max_y-min_y)/2), height=5)
	treebuildtime = time.time() - starttime
	starttime = time.time()
	for obj in item_list:
		tree.collisions(obj)
	treesearchtime = time.time() - starttime

	sumna += naivetime
	sumna2 += naivetime**2
	sumqb += treebuildtime
	sumqb2 += treebuildtime**2
	sumqs += treesearchtime
	sumqs2 += treesearchtime**2
	sumqa += treebuildtime + treesearchtime
	sumqa2 += (treebuildtime + treesearchtime)**2


average_naive_everything = sumna / N_loops
average_tree_everything = sumqa / N_loops
average_tree_search = sumqs / N_loops
print "Ran {0} tests with {1} randomly-generated circles.".format(N_loops, N_items)
print "Sort search: {0:.3f}".format(average_naive_everything)
print "Tree search: {0:.3f}".format(average_tree_everything)
print "Average tree-build time: {0:.3f}".format(sumqb / N_loops)
print "Average tree-search time: {0:.3f}".format(average_tree_search)
print "Search time improvement: {0:.1f}% of the naive time".format(100*average_tree_search / average_naive_everything)



"""
collist = set()
print "Searching with quadtree..."
###
# Quadtree Sorting
###

def newdocollide(me,you,vec=v(0,0)):
	fixvect = intersection_vector(me,you)
	if fixvect is None: return
	do_collide(me,you)
quadtree.do_collide = newdocollide

tree = quadtree.QuadTree(item_list, center=v((max_x-min_x)/2,(max_y-min_y)/2), height=5)
starttime = time.time()
for obj in item_list:
	tree.collisions(obj)
quadtime = time.time() - starttime

print "Done searching with quadtree."
collist_quad = collist


print "New stuff:"
print "\n\n\nCollisions detected by the sort:"
for i,string in enumerate(collist_naive):
	print "{0}. {1}".format(i,string)
	if i > listcount:
		print "..."
		break
print "Total collisions found: {0}".format(len(collist_naive))
print "\nCollisions detected by the quadtree:"
for i,string in enumerate(collist_quad):
	print "{0}. {1}".format(i,string)
	if i > listcount:
		print "..."
		break
print "Total collisions found: {0}".format(len(collist_quad))


print "\n\nCollisions found by the sort but not by the quadtree:"
for i,string in enumerate(collist_naive - collist_quad):
	print "{0}. {1}".format(i,string)
	if i > diffcount:
		print "..."
		break
print "Difference length: {0}".format(len(collist_naive - collist_quad))


print "\nCollisions found by the quadtree but not by the sort:"""
"""for i,stringin enumerate(collist_quad - collist_naive):
	print "{0}. {1}".format(i,string)
	if len(collist_quad-collist_naive) < 30:
		continue
	if i > diffcount:
		print "..."
		break""""""
print "Difference length: {0}".format(len(collist_quad - collist_naive))

print "Took {0:.2f} seconds to sortsearch.".format(naivetime)
print "Took {0:.2f} seconds to quadtree search.".format(quadtime)"""
