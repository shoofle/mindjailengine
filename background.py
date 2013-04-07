import pyglet
import random
import math

class Background(object):
	def __init__(self, pscreen, num_triangles=5000, x=(-8000,8000), y=(-5000,5000), z=(-10,5), width=200, height=0.2):
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

		x_count, y_count = 60, 50
		x_width, y_width = 10000, 8000
		start_x, start_y = -5000, -4000
		depth, offset_z = 4, -10
		pixels = list()
		colors = list()
		for y in range(y_count):
			a = list()
			b = list()
			for x in range(x_count):
				xp = x_width*(1.0*x/x_count)+start_x
				yp = y_width*(1.0*y/y_count)+start_y
				vertex = xp, yp, offset_z - depth*perlin(xp, yp)
				a.append(vertex)
				c = 0.3+0.4*perlin(xp, yp, f_r=(0,0.005), v=r1), \
					0.3+0.4*perlin(xp, yp, f_r=(0,0.005), v=r2), \
					0.3+0.4*perlin(xp, yp, f_r=(0,0.005), v=r3)
				b.append(c)
			pixels.append(a)
			colors.append(b)

		vlist = []
		clist = []
		for y in range(y_count-1):
			for x in range(x_count-1):
				for i in (pixels[y][x], pixels[y][x+1], pixels[y+1][x], pixels[y][x+1], pixels[y+1][x+1], pixels[y+1][x]):
					vlist.extend(x for x in i)
				for i in (colors[y][x], colors[y][x+1], colors[y+1][x], colors[y][x+1], colors[y+1][x+1], colors[y+1][x]):
					clist.extend(x for x in i)
		self.vlist2 = pyglet.graphics.vertex_list(len(vlist)/3, 'v3f', 'c3f')
		self.vlist2.vertices = vlist[:]
		self.vlist2.colors = clist[:]
		
	def update(self, timestep): pass
	def draw(self):
		pyglet.gl.glPushMatrix()
		self.vlist.draw(pyglet.gl.GL_TRIANGLES)
		self.vlist2.draw(pyglet.gl.GL_TRIANGLES)
		pyglet.gl.glPopMatrix()

r = [[random.random() for i in range(10)] for i in range(4)]
r1 = [[random.random() for i in range(10)] for i in range(4)]
r2 = [[random.random() for i in range(10)] for i in range(4)]
r3 = [[random.random() for i in range(10)] for i in range(4)]
r4 = [[random.random() for i in range(10)] for i in range(4)]
 

def perlin(x, y, f_r = (0,0.01), v=r):
	output = 0
	for xf, xo, yf, yo in zip(*v):
		xf, yf = xf*(f_r[1]-f_r[0])+f_r[0], yf*(f_r[1]-f_r[0])+f_r[0]
		output += math.sin(xf*(x-xo)) * math.sin(yf*(y-yo))
	return output/len(r1)

