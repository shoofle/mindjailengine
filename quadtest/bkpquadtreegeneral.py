yminfunction = lambda x: x.shape.ybounds[0]
ymaxfunction = lambda x: x.shape.ybounds[1]
xminfunction = lambda x: x.shape.xbounds[0]
xminfunction = lambda x: x.shape.xbounds[1]

class QuadTree:
	def __init__(self,items=[],center=v(0,0),depth=8, yt=ymaxfunction,yb=yminfunction,xt=xmaxfunction,xb=xminfunction):
		self.depth = depth

		#self.Items = items
		self.quadrants = [ None, None, None, None ]
		self.NE = self.quadrants[0] = None
		self.SE = self.quadrants[1] = None
		self.NW = self.quadrants[2] = None
		self.SW = self.quadrants[3] = None

		self.xmin, self.xmax = -1,1
		self.ymin, self.ymax = -1,1
		self.center = center
		self.xc,self.yc = self.center.x, self.center.y

		self.yb=yb
		self.yt=yt
		self.xb=xb
		self.xt=xt

		appendage = [ [], [], [], [] ]
		for thing in items:
			if self.xb(thing) > self.xc:
				if self.yb(thing) > self.yc: appendage[0].append(thing)
				elif self.yt(thing) < self.yc: appendage[1].append(thing)
				else: self.Items.append(thing)
			elif self.xt(thing) < self.xc:
				if self.yb(thing) > self.yc: appendage[2].append(thing)
				elif self.yt(thing) < self.yc: appendage[3].append(thing)
				else: self.Items.append(thing)
			else: self.Items.append(thing)

		for i, quadrantlist in enumerate(appendage):
			if quadrantlist.length == 0: continue
			qcenter = v(0,0)
			for thing in random.sample(quadrantlist,math.floor(quadrantlist.length/3)):
				qcenter = qcenter + thing.pos/math.floor(quadrantlist.length/3)
			self.quadrant[i] = QuadTree(quadrantlist, center=qcenter, depth = self.depth-1, yt=self.yt, yb=self.yb, xt=self.xt, xb=self.xb)
	
	def insert(self, obj):
		""" Insert obj into this quadtree. Should throw it into the appropriate quadrant if necessary, 
		and otherwise throw it into the self.Items bin.
		Still a little iffy on how to determine if it's actually *necessary* to 
		put it into a new quadrant. Also, no clue how to find the good centers for 
		the new quadrants.
		Actually, the problem of where to locate the centers for the new quadrants 
		is quite a bit of a problem. Not really sure how I'm going to do that!
		"""
		if self.yb(obj) < self.ymin: self.ymin = self.yb(obj)
		if self.yt(obj) > self.ymax: self.ymax = self.yt(obj)
		if self.xb(obj) < self.xmin: self.xmin = self.xb(obj)
		if self.xt(obj) > self.xmax: self.xmax = self.xt(obj)

		if obj in self.Items: return self.depth   ### If the object is in this level, go ahead and return the current depth
		if self.xb(obj) > self.xc:
			if self.yb(obj) > self.yc: 
				if self.NE is None: self.NE = QuadTree(items=[], center=obj.pos, depth=self.depth-1, yt=self.yt,yb=self.yb,xt=self.xt,xb=self.xb )
				return self.NE.insert(obj)
			elif self.yt(obj) < self.yc: 
				if self.SE is None: self.SE = QuadTree(items=[], center=obj.pos, depth=self.depth-1, yt=self.yt,yb=self.yb,xt=self.xt,xb=self.xb )
				return self.SE.insert(obj)
			else: self.Items.append(obj)
		elif self.xt(obj) < self.xc:
			if self.yb(obj) > self.yc:
				if self.NW is None: self.NW = QuadTree(items=[], center=obj.pos, depth=self.depth-1, yt=self.yt,yb=self.yb,xt=self.xt,xb=self.xb )
				return self.NW.insert(obj)
			elif self.yt(obj) < self.yc:
				if self.SW is None: self.SW = QuadTree(items=[], center=obj.pos, depth=self.depth-1, yt=self.yt,yb=self.yb,xt=self.xt,xb=self.xb )
				return self.SW.insert(obj)
			else: self.Items.append(obj)
		else: self.Items.append(obj)

	def remove(self, obj):
		""" Remove obj from the tree. If it's already here, return the depth of where it was removed from. Else return none.
		In the future, I suppose that it should throw an exception if it tries to remove an object not in the tree.
		"""
		if obj in self.Items: 
			self.Items.remove(obj)
			return self.depth

		if self.xb(obj) > self.xc:
			if self.yb(obj) > self.yc: self.NE.remove(obj)
			elif self.yt(obj) < self.yc: self.SE.remove(obj)
			elif obj in self.Items:
				self.Items.remove(obj)
				return self.depth
		elif self.xt(obj) < self.yc:
			if self.yb(obj) > self.yc: self.NW.remove(obj)
			elif self.yt(obj) < self.yc: self.SE.remove(obj)
			elif obj in self.Items:
				self.Items.remove(obj)
				return self.depth

	
	def collisions(self, obj):
		if self.yb(obj) > self.ymax: return None
		if self.yt(obj) < self.ymin: return None
		if self.xb(obj) > self.xmax: return None
		if self.xt(obj) < self.xmin: return None

		for other in Items: 
			if COULDBECOLLIDING(obj,other): DOCOLLISIONSXXX(obj,other)

		if self.xb(obj) < self.xc:
			if self.yb(obj) < self.yc: self.SW.collisions(obj)
			if self.yt(obj) > self.yc: self.NW.collisions(obj)
		if self.xt(obj) > self.xc:
			if self.yb(obj) < self.yc: self.SE.collisions(obj)
			if self.yt(obj) > self.yc: self.NE.collisions(obj)

