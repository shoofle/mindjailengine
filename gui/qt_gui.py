from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.arrays import vbo

from PyQt4 import QtCore
from PyQt4.QtGui import *
from PyQt4.QtOpenGL import *

from vectors import v
from random import random, uniform, randint
import math

class OpenGLPane(QGLWidget):
	def paintGL(self):
		glClearColor(0, 0, 0, 1.0)
		glClear(GL_COLOR_BUFFER_BIT)

		for b in bwonkers: b.update()

	def resizeGL(self, width, height):
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		glOrtho(-50, 50, -50, 50, -50.0, 50.0)
		glViewport(0, 0, width, height)

	def initializeGL(self):
		glClearColor(0, 0, 0, 1.0)
		glClear(GL_COLOR_BUFFER_BIT)

x_boundary = 50
y_boundary = 50
class Bwonker(object):
	def __init__(self, position, scatter=5, speed=2, size=2):
		self.color = (random(), random(), random(), 1.0)
		self.scatter = scatter
		angle = random()*2*math.pi
		self.speed = v(math.sin(angle), math.cos(angle))*speed
		self.position = position
		self.size = size
	def update(self):
		pane.makeCurrent()
		if randint(0, self.scatter) == 0:
			angle = random()*2*math.pi
			self.speed = v(math.sin(angle), math.cos(angle))*abs(self.speed)
		if abs(self.position.x) > x_boundary: self.speed.x = -self.speed.x
		if abs(self.position.y) > y_boundary: self.speed.y = -self.speed.y
		self.position = self.position + self.speed


		glPushMatrix()
		
		glTranslatef(self.position.x, self.position.y, 0)
		shaders.glUseProgram(shader)
		try:
			square_vbo.bind()
			try:
				glEnableClientState(GL_VERTEX_ARRAY)
				glVertexPointerf(square_vbo)
				glDrawArrays(GL_TRIANGLES,0,6)
			finally:
				square_vbo.unbind()
				glDisableClientState(GL_VERTEX_ARRAY)
		finally:
			shaders.glUseProgram(0)

		#glRectf(-self.size, -self.size, self.size, self.size)
		glPopMatrix()


def update():
	pane.updateGL()
#	print bwonkers[len(bwonkers)-1].position

print(glGetString(GL_VERSION))

# OpenGL Shader type stuff
vertex_shader = shaders.compileShader("""
#version 330
void main() {
  gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
}""", GL_VERTEX_SHADER)
fragment_shader = shaders.compileShader("""
#version 330
void main() {
  gl_FragColor = vec4(0,1,0,0);
}""", GL_FRAGMENT_SHADER)
shader = shaders.compileProgram(vertex_shader, fragment_shader)

data = array([
	[-1,-1, 0],
	[ 1,-1, 0],
	[ 1, 1, 0],
	[-1,-1, 0],
	[ 1, 1, 0],
	[-1, 1, 0]
	],'f')
square_vbo = vbo.VBO(data)




app = QApplication(["Shoofle's PyQt application"])
widget = QWidget()

layout = QHBoxLayout()

scroller = QScrollArea()
layout.addWidget(scroller)

pane = OpenGLPane()
pane.setMinimumSize(700,700)
bwonkers = []
for i in range(10):
	b = Bwonker(position=v(uniform(-10, 10), uniform(-10, 10)), scatter=randint(1, 20), speed=uniform(0.1,1))
	bwonkers.append(b)


layout.addWidget(pane)

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(1000/60)

widget.setLayout(layout)
widget.show()

app.exec_()

