from OpenGL.GL import *

from PyQt4 import QtCore
from PyQt4.QtGui import *
from PyQt4.QtOpenGL import *

from vectors import v
from random import random, uniform, randint
import math

"""
Screen class accesses the PyQt app, and specifically the widget that defines the screen.
Let's think about a handful of screens - the menu screen, gameplay screen, pause screen.

Menu looks like:
	List of files
	Load level button
	Quit button?
	Adjust settings?

Gameplay looks like:
	OpenGL pane

Pause screen loads from Gameplay screen and uses the same OpenGL pane, keeping it present
`	OpenGL pane

when you go from Menu->Gameplay, it un-displays all the menu widgets, and displays all the gameplay widgets.
It then starts running the gameplay screen logic.
When you go from Menu->Pause, it doesn't un-display the menu widgets, but it then displays all the pause widgets.

"""

class OpenGLPane(QGLWidget):
	def paintGL(self):
		""" Override this to write to stuff. The problem was that we were clearing the screen, and then trying to draw a bunch of stuff, but it was happening in the wrong order..."""
#		glClearColor(0, 0, 0, 1.0)
#		glClear(GL_COLOR_BUFFER_BIT)
#		for b in bwonkers:
#			b.update()

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
		if randint(0, self.scatter) == 0:
			angle = random()*2*math.pi
			self.speed = v(math.sin(angle), math.cos(angle))*abs(self.speed)
		if abs(self.position.x) > x_boundary: self.speed.x = -self.speed.x
		if abs(self.position.y) > y_boundary: self.speed.y = -self.speed.y
		self.position = self.position + self.speed


		glPushMatrix()
		
		glColor4f(*self.color)
		glTranslatef(self.position.x, self.position.y, 0)
		glRectf(-self.size, -self.size, self.size, self.size)

		glPopMatrix()


def update():
	widget.current.updateGL()
	glClearColor(0, 0, 0, 1.0)
	glClear(GL_COLOR_BUFFER_BIT)
	for b in bwonkers:
		b.update()

bwonkers = []
for i in range(10):
	b = Bwonker(position=v(uniform(-10, 10), uniform(-10, 10)), scatter=randint(1, 20), speed=uniform(0.1,1))
	bwonkers.append(b)

def switch_pane():
	if widget.current is pane_one:
		widget.current = pane_two
	else:
		widget.current = pane_one
	widget.current.makeCurrent()


app = QApplication(["Shoofle's PyQt application"])
widget = QWidget()
widget.current = None

layout = QVBoxLayout()

button = QPushButton('Switch Rendering Pane', widget)
button.clicked.connect(switch_pane)
layout.addWidget(button)

splitter = QSplitter(QtCore.Qt.Horizontal)
layout.addWidget(splitter)

pane_one = OpenGLPane()
#pane_one.setMinimumSize(300,600)
splitter.addWidget(pane_one)

pane_two = OpenGLPane()
#pane_two.setMinimumSize(300,600)
splitter.addWidget(pane_two)

widget.current = pane_one

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(1000/60)

widget.setLayout(layout)
widget.show()

app.exec_()

