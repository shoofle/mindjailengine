from vectors import v

import pyglet
from pyglet import gl as opengl

from math import floor
import random

from components import shapes

"""I seem to have written a startling number of data structures for collision detection. Currently using SpatialGrid, which is a spatial hashing implementation."""

def intersects(a, b):
	return a is not b and a.x_min < b.x_max and a.x_max > b.x_min and a.y_min < b.y_max and a.y_max > b.y_min

class DataStructure(object):
	def __init__(self, items): pass
	def collisions(self, item): return set()
	def append(self, item): pass
	def extend(self, items): pass
	def remove(self, item): pass
	def __contains__(self, item): pass
	def __len__(self): return 0
	def status_report(self): return '' # Optional. Returns a string representing the current status of the data structure.
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

		self.secondary = None
		if items is not None:
			self.extend(items)
	
	def too_big(self, item): 
		""" Returns true if the object is too big to fit in this grid. """
		return item.x_max-item.x_min >= self.grid_size or item.y_max-item.y_min >= self.grid_size
	
	def grid_square(self, item): 
		""" Return the grid square occupied by item. """
		return int(floor( item.x_pos /self.grid_size)), int(floor( item.y_pos /self.grid_size)) # int() rounds toward zero.
	
	def grid_space(self, item):
		""" Returns a generator for the grid squares the object might be contacting, including neighbors. """
		grid_size = self.grid_size
		min_x = int(floor(item.x_min / grid_size))
		max_x = int(floor(item.x_max / grid_size))
		min_y = int(floor(item.y_min / grid_size))
		max_y = int(floor(item.y_max / grid_size))
		
		return ((i,j) for i in range(min_x-1, max_x+2) for j in range(min_y-1, max_y+2) if (i,j) in self.grid)

	def collisions(self, item):
		""" Returns all objects colliding with the argument. """
		if self.secondary is not None: output = self.secondary.collisions(item)
		else: output = set()

		for location in self.grid_space(item):
			output |= self.grid[location].collisions(item)

		return output

	def append(self, item):
		""" Add item to the spatial grid. If it is too big, it will get bumped up to the secondary data structure. """
		if self.too_big(item):
			if self.secondary is None:
				self.secondary = SpatialGrid(max_size=self.grid_size*2)
			self.secondary.append(item)
		else:
			location = self.grid_square(item)
			if location not in self.grid: 
				self.grid[location] = BruteList() # This decides the secondary data structure.
			self.grid[location].append(item)
	
	def extend(self, items): 
		for i in items: 
			self.append(i)
	
	def remove(self, item):
		if self.secondary is not None and self.too_big(item) and item in self.secondary:
			self.secondary.remove(item)
		else:
			location = self.grid_square(item)
			if location in self.grid and item in self.grid[location]:
				self.grid[location].remove(item)
				if len(self.grid[location]) is 0: 
					del self.grid[location]
			else: 
				for k in self.grid.keys():
					if item in self.grid[k]: self.grid[k].remove(item)
					if len(self.grid[k]) is 0: 
						del self.grid[k]
	
	def __contains__(self, item):
		if self.secondary is not None and self.too_big(item): 
			return item in self.secondary
		location = self.grid_square(item)
		if location in self.grid and item in self.grid[location]: 
			return True
		return any(item in self.grid[l] for l in self.grid)

	def __len__(self): 
		if self.secondary is None: 
			return sum(map(lambda x: len(self.grid[x]), self.grid))
		else:
			return sum(map(lambda x: len(self.grid[x]), self.grid)) + len(self.secondary)
	
	def status_report(self, indent=''):
		if self.secondary is None:
			secondary_rep = "Nothing."
			num_off_grid = 0
		else:
			secondary_rep = self.secondary.status_report()
			num_off_grid = len(self.secondary)
		
		num_in_grid, num_grid_squares = len(self) - num_off_grid, len(self.grid)
		
		if num_in_grid is 0: 
			return "Nada.\n{}\n\n".format(secondary_rep)
		
		ave_occupancy = 1.0*num_in_grid/num_grid_squares
		neighbors, max_neighbors = 0, 0
		
		for i,j in self.grid:
			neighbors_here = sum(map(len, ((u,v) for u in range(i-1, i+2) for v in range(j-1, j+2) if (u,v) in self.grid)))
			max_neighbors = max(neighbors_here, max_neighbors)
			neighbors += neighbors_here
		
		ave_neighbors = 1.0*neighbors/num_in_grid
		
		return "\
Number in the grid: {}\n\
Number off the grid: {}\n\
Number of grid squares: {}\n\
Average occupancy of grid squares: {}\n\
Average number of neighbors: {}\n\
Max neighbors: {}\n\
Total Neighbors: {}\n\n".format(num_in_grid, num_off_grid, num_grid_squares, ave_occupancy, ave_neighbors, max_neighbors, neighbors)
	
	def draw(self):
		for x,y in self.grid:
			opengl.glPushMatrix()
			opengl.glTranslatef(x*self.grid_size, y*self.grid_size, 0)
			opengl.glColor3f(self.color[0], self.color[1], self.color[2])
			self.vlist.draw(pyglet.gl.GL_LINE_LOOP)
			opengl.glPopMatrix()
		if self.secondary is not None: self.secondary.draw()

