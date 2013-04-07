import pyglet
import random

class Background(object):
	def __init__(self, pscreen, num_triangles=1000, x=(-8000,8000), y=(-5000,5000), z=(-10.0,10.0), width=200, height=0.2):
		self.pscreen = pscreen
		self.dead = False
		self.vlist = pyglet.graphics.vertex_list(3*num_triangles, 'v3f', 'c3f')

		verts_per_triangle = 3
		for triangle_index in range(num_triangles):
			color = random.random(), random.random(), random.random()
			cx, cy, cz = random.uniform(x[0],x[1]), random.uniform(y[0],y[1]), random.uniform(z[0],z[1])
			for sub_index in range(3):
				vertex_index = (triangle_index*verts_per_triangle + sub_index)*3
				self.vlist.vertices[vertex_index:vertex_index+3] = (cx + random.uniform(-width/2,width/2)), \
																   (cy + random.uniform(-width/2,width/2)), \
																   (cz + random.uniform(-height/2,height/2))
				self.vlist.colors[vertex_index:vertex_index+3] = color
	def update(self, timestep): pass
	def draw(self):
		pyglet.gl.glPushMatrix()
		self.vlist.draw(pyglet.gl.GL_TRIANGLES)
		pyglet.gl.glPopMatrix()
