import pyglet
import random
import math
from vectors import v

class Background(object):
	def __init__(self, pscreen, num_triangles=5000, x=(-8000,8000), y=(-5000,5000), z=(-100,100), width=200, height=0.2):
		self.pscreen = pscreen
		self.dead = False
		self.vlist = pyglet.graphics.vertex_list(3*num_triangles, 'v3f', 'c3f')

		verts_per_triangle = 3
		for triangle_index in range(num_triangles):
			color = random.random(), random.random(), random.random()
			cx, cy, cz = random.uniform(x[0],x[1]), random.uniform(y[0],y[1]), random.uniform(z[0],z[1])
			while -0.2 < cz < 0.2: cz = random.uniform(z[0],z[1])
			for sub_index in range(3):
				vertex_index = (triangle_index*verts_per_triangle + sub_index)*3
				self.vlist.vertices[vertex_index:vertex_index+3] = (cx + random.uniform(-width/2,width/2)), \
																   (cy + random.uniform(-width/2,width/2)), \
																   (cz + random.uniform(-height/2,height/2))
				self.vlist.colors[vertex_index:vertex_index+3] = color

		x_count, y_count = 200, 200
		x_width, y_width = 5000, 4000
		start_x, start_y = -2500, -2000
		depth, offset_z = 600, -300
		cylinder_height, cylinder_radius = 1000, 200
		z_scale = 1
		coefficients = ((0,0.05),(1,0.15),(2,0.2),(3,0.3),(4,0.5))
		vertexen = list()
		colors = list()
		for j in range(y_count):
			a = list()
			b = list()
			for i in range(x_count):
				x_n, y_n = 1.0*i/x_count, 1.0*j/y_count
				p = sum(map(lambda c: perlin_2d(x_n,y_n, source=rands[c[0]])*c[1],coefficients) )
				#p = (perlin_2d(x_n,y_n, source=r2) + perlin_2d(x_n,y_n, source=r_v1) + perlin_2d(x_n,y_n, source=r_v2) + perlin_2d(x_n,y_n, source=r_v3))*0.25
#				p = perlin_2d(x_n, y_n, source=r_2d)
#				p = perlin_2d(x_n, y_n, source=r_downscaled)
#				p = perlin_2d(x_n, y_n, source=r_doubledown)

				xp, yp, zp = x_width*x_n+start_x, y_width*y_n+start_y, offset_z+depth*p
				r, theta, h = cylinder_radius + depth*p, 2*math.pi*x_n, cylinder_height*y_n
				#a.append((r*math.cos(theta), h, offset_z + r*math.sin(theta)/z_scale))
				a.append((xp, yp, zp))
				b.append((0.3+0.7*p,)*3)
			vertexen.append(a)
			colors.append(b)
#		diff = lambda a, b: (a[0]-b[0],a[1]-b[1],a[2]-b[2])
#		cross_product = lambda a, b: (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
#		normalize = lambda a: (a[0]/math.sqrt(a[0]**2 + a[1]**2 + a[2]**2), a[1]/math.sqrt(a[0]**2 + a[1]**2 + a[2]**2), a[2]/math.sqrt(a[0]**2 + a[1]**2 + a[2]**2))
#		normals = list()
#		for j in range(y_count):
#			a = list()
#			for i in range(x_count):
#				if i+1 < x_count and j+1 < y_count:
#					a.append(normalize(cross_product(diff(vertexen[i+1][j],vertexen[i][j]),diff(vertexen[i][j],vertexen[i][j+1]))))
#				else:
#					a.append(normalize(cross_product(diff(vertexen[i-1][j],vertexen[i][j]),diff(vertexen[i][j-1],vertexen[i][j]))))
#			normals.append(a)

		vlist, clist = [], []
		for y in range(y_count-1):
			for x in range(x_count-1):
				for i in (vertexen[y][x], vertexen[y][x+1], vertexen[y+1][x], vertexen[y][x+1], vertexen[y+1][x+1], vertexen[y+1][x]):
					vlist.extend(x for x in i)
				for i in (colors[y][x], colors[y][x+1], colors[y+1][x], colors[y][x+1], colors[y+1][x+1], colors[y+1][x]):
					clist.extend(x for x in i)
#				for i in (normals[y][x], normals[y][x+1], normals[y+1][x], normals[y][x+1], normals[y+1][x+1], normals[y+1][x]):
#					nlist.extend(x for x in i)
		self.vlist2 = pyglet.graphics.vertex_list(len(vlist)/3, 'v3f', 'c3f') #, 'n3f')
		self.vlist2.vertices = vlist
		self.vlist2.colors = clist
#		self.vlist2.normals = nlist
		
	def update(self, timestep): pass
	def draw(self):
		pyglet.gl.glPushMatrix()
		self.vlist.draw(pyglet.gl.GL_TRIANGLES)
		#pyglet.gl.glRotatef(self.pscreen.total_time*20, 0.0, 1.0, 0.0)
		pyglet.gl.glMaterialfv(pyglet.gl.GL_FRONT_AND_BACK, pyglet.gl.GL_DIFFUSE, (pyglet.gl.GLfloat * 4)(*(1, 1, 1, 1.0)))
		pyglet.gl.glMaterialfv(pyglet.gl.GL_FRONT_AND_BACK, pyglet.gl.GL_SPECULAR, (pyglet.gl.GLfloat * 4)(*(0.9, 0.9, 0.8, 1.0)))
		pyglet.gl.glMaterialf(pyglet.gl.GL_FRONT_AND_BACK, pyglet.gl.GL_SHININESS, 89)
		self.vlist2.draw(pyglet.gl.GL_TRIANGLES)
		pyglet.gl.glPopMatrix()


def perlin_2d(x, y, source=None, x_w=None, y_w=None, interpolate=None):
	""" Takes x and y coordinates and produces perlin noise, seeded by the 2d array `source` and using the 2d interpolation function interpolate. """
	if source is None: source=r_2d
	if x_w is None: x_w = len(source)-1
	if y_w is None: y_w = len(source[0])-1
	if interpolate is None: interpolate=interpolate_2d
	p = v(x*x_w,y*y_w)
	i,j = int(p.x),int(p.y) # Don't need to use floor because these are assumed to be positive.
	c=[(i,j),(i,j+1),(i+1,j+1),(i+1,j)]
	corners = [source[u][w]*(p-v(u,w)) for (u,w) in c]
	output = interpolate(p-v(i,j), corners)
	return output

def rescale_2d(source, m):
	x_old_w, y_old_w = len(source), len(source[0])
	x_new_w, y_new_w = int(x_old_w*m), int(y_old_w*m)
	output = list()
	for inew in range(x_new_w):
		a = list()
		for jnew in range(y_new_w):
			x, y = 1.0*inew/x_new_w, 1.0*jnew/y_new_w
			iold, jold = int(x*x_old_w), int(y*y_old_w)
			c=[(iold,jold),(iold,jold+1),(iold+1,jold+1),(iold+1,jold)]
			a.append(interpolate_2d(v(x-1.0*iold/x_old_w, y-1.0*jold/y_old_w), [source[u][w] for (u,w) in c]))
		output.append(a)
	return output


def interpolate_2d(p, c, interpolate=None):
	""" Takes a point normalized to 0,1 and four corner values (0,0, 0,1, 1,1, 1,0) and interpolates between them. """
	if interpolate is None: interpolate = hermite
	bottom_int = hermite(p.x, (c[0],c[3]))
	top_int = hermite(p.x, (c[1],c[2]))
	return hermite(p.y, (bottom_int, top_int))

def hermite(p, c):
	""" Hermite interpolation between two points, with starting and ending tangents zero. """
	return c[0]*(2*(p**3) - 3*(p**2) + 1) + c[1]*(-2*(p**3) + 3*(p**2))

#def spectral_noise(x, y, f_r = (0,0.01), v=r):
#	output = 0
#	for xf, xo, yf, yo in zip(*v):
#		xf, yf = xf*(f_r[1]-f_r[0])+f_r[0], yf*(f_r[1]-f_r[0])+f_r[0]
#		output += math.sin(xf*(x-xo)) * math.sin(yf*(y-yo))
#	return output/len(r1)


#r = [[random.random() for i in range(100)] for j in range(5)]

#r2 = [[v(random.uniform(-1,1),random.uniform(-1,1)) for i in range(80)] for j in range(80)]
rands = list()
rands.append( [[v(random.uniform(-1,1),random.uniform(-1,1)) for i in range(100)] for j in range(100)] )
for i in range(10):
	if len(rands[i]) < 10: break
	rands.append(rescale_2d(rands[i], 0.5))
