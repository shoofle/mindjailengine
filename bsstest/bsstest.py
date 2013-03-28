from vectors import v
import math
import random
import time
import buildsortsearch
#import linearsortsearch
import quadtree
import quadtreebad

# Restrictions on our random test items. (They are circles or squares!)
N_loops = 1
N_items = 300

max_radius = 50
min_radius = 2

max_x = 600.
min_x = 0.
max_y = 600.
min_y = 0.










random.seed()
# Test item class.
class RandomItem:
	def __init__(self):
		self.radius = random.uniform(min_radius,max_radius)
		self.x,self.y = random.uniform(min_x,max_x), random.uniform(min_y,max_y)
		self.pos = v(self.x,self.y)
		self.xmin,self.xmax = self.x - self.radius, self.x + self.radius
		self.ymin,self.ymax = self.y - self.radius, self.y + self.radius


print "Generating collection of items...",
# Generate a collection of N_items random items.
item_list = []
for i in range(N_items):
	item_list.append(RandomItem())
print "Done."
print "Defining stuff for the comparison and collision reaction...",
collist  = set()
collist2 = set()
def do_collide(x, y):
	collist.add((item_list.index(x),item_list.index(y)))
def intersects(x, y):
	return abs(x.pos - y.pos) < x.radius + y.radius
#linearsortsearch.intersects = intersects
#linearsortsearch.do_collide = do_collide
buildsortsearch.intersects = intersects
buildsortsearch.do_collide = do_collide
quadtree.intersects = intersects
quadtree.do_collide = do_collide
print "Done."





print "Doing stats!"
bss_stats = [0,0, 0,0, 0,0]
tree_stats = [0,0, 0,0, 0,0]
ratio_mean = [0,0]
# Helper function for updating the stats.
def stat_update(stats, num, i=0):
	stats[2*i] += num
	stats[2*i+1] += num**2
# Helper function for outputting the stats.
def stat_print(stats, labels, num=N_loops):
	for i in range(0,len(stats),2):
		mean = stats[i]/num
		stdev = math.sqrt( (stats[i+1]/num) - mean**2 )
		print "{0} {1:.6f} +/- {2:.6f}".format(labels[int(i/2)],mean,stdev)




for k in range(N_loops):
	# Generate our items.
	item_list = []
	for i in range(N_items):
		item_list.append(RandomItem())
	###
	# Test the build sort search.
	###
	start = time.time()
	sortlist = buildsortsearch.SortSearchList(item_list)
	build_time = time.time() - start
	start = time.time()
	sortlist.all_collisions()
	search_time= time.time() - start

	# Update our stats.
	stat_update(bss_stats, build_time+search_time, 0)
	stat_update(bss_stats, build_time, 1)
	stat_update(bss_stats, search_time, 2)

	###
	# Test the quadtree search.
	###
	start = time.time()
	sorttree = quadtree.QuadTree(item_list)
	t_build_time = time.time() - start
	start = time.time()
	sorttree.all_collisions()
	t_search_time= time.time() - start

	# Update our stats.
	stat_update(tree_stats, t_build_time+t_search_time, 0)
	stat_update(tree_stats, t_build_time, 1)
	stat_update(tree_stats, t_search_time, 2)

	stat_update(ratio_mean, (t_build_time + t_search_time)/(build_time + search_time))

print "Ran {0} tests with {1} randomly-generated circles.".format(N_loops, N_items)
labels = ["Total search time: ", "Build time: ", "Search time:"]
print "Build/Sort/Search list:"
stat_print(bss_stats, labels)
print "Quadtree:"
stat_print(tree_stats, labels)
stat_print(ratio_mean, ["Average ratio Quadtree time / BSS time:"])



collist2=set()
item_list = []
for i in range(N_items):
	item_list.append(RandomItem())

quad = quadtreebad.QuadTree(item_list)
for item in item_list:
	quad.collisions(item)
badlist = set(collist2)
collist2 = set()
quad = quadtree.QuadTree(item_list)
quad.all_collisions()
print len(badlist-collist2)
print len(collist2-badlist)
