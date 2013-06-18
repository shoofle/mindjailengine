#!/usr/bin/env python
import wx, wx.glcanvas, os
from OpenGL.GL import *
from OpenGL.GLUT import *

class MyFrame(wx.Frame):
	""" New frame class! """
	def __init__(self, parent, title):
		wx.Frame.__init__(self, parent, title=title, size=(400,600))
		self.control = wx.TextCtrl(self, style=wx.TE_MULTILINE)
		self.CreateStatusBar()
		
		fileMenu = wx.Menu()
		open_choice = fileMenu.Append(wx.ID_OPEN, "&Open", " Open a file!")
		self.Bind(wx.EVT_MENU, self.on_open, open_choice)
		exit_choice = fileMenu.Append(wx.ID_EXIT, "E&xit", " Quit :(")
		self.Bind(wx.EVT_MENU, self.on_exit, exit_choice)
		
		menuBar = wx.MenuBar()
		menuBar.Append(fileMenu, "&File")
		
		self.SetMenuBar(menuBar)
		self.canvas = wx.glcanvas.GLCanvas(self, id=wx.ID_ANY, size=wx.Size(w=100, h=200))
		self.context = wx.glcanvas.GLContext(self.canvas)
		self.init = False
		self.Bind(wx.EVT_PAINT, self.on_paint)

		self.Show(True)


	def on_open(self, e):
		""" Open a file. """
		self.dirname = ""
		dialog = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.*", wx.OPEN)
		if dialog.ShowModal() == wx.ID_OK:
			self.filename = dialog.GetFilename()
			self.dirname = dialog.GetDirectory()
			f = open(os.path.join(self.dirname, self.filename), "r")
			self.control.SetValue(f.read())
			f.close()
		dialog.destroy()

	def on_exit(self, e):
		self.Close(True)

	def on_paint(self, e):
		dc = wx.PaintDC(self)
		self.canvas.SetCurrent()
		if not self.init:
			init_gl()
			self.init = True
		draw_cube(self.canvas)


def init_gl():
	# set viewing projection
	glMatrixMode(GL_PROJECTION)
	glFrustum(-0.5, 0.5, -0.5, 0.5, 1.0, 3.0)

	# position viewer
	glMatrixMode(GL_MODELVIEW)
	glTranslatef(0.0, 0.0, -2.0)

	glClearColor(0, 0, 1.0, 1.0)
		
	glEnable(GL_DEPTH_TEST)
	glEnable(GL_LIGHTING)
	glEnable(GL_LIGHT0)

def draw_cube(canvas):
	# clear color and depth buffers
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

	# draw six faces of a cube
	glBegin(GL_QUADS)
	glNormal3f( 0.0, 0.0, 1.0)
	glVertex3f( 0.5, 0.5, 0.5)
	glVertex3f(-0.5, 0.5, 0.5)
	glVertex3f(-0.5,-0.5, 0.5)
	glVertex3f( 0.5,-0.5, 0.5)

	glNormal3f( 0.0, 0.0,-1.0)
	glVertex3f(-0.5,-0.5,-0.5)
	glVertex3f(-0.5, 0.5,-0.5)
	glVertex3f( 0.5, 0.5,-0.5)
	glVertex3f( 0.5,-0.5,-0.5)

	glNormal3f( 0.0, 1.0, 0.0)
	glVertex3f( 0.5, 0.5, 0.5)
	glVertex3f( 0.5, 0.5,-0.5)
	glVertex3f(-0.5, 0.5,-0.5)
	glVertex3f(-0.5, 0.5, 0.5)

	glNormal3f( 0.0,-1.0, 0.0)
	glVertex3f(-0.5,-0.5,-0.5)
	glVertex3f( 0.5,-0.5,-0.5)
	glVertex3f( 0.5,-0.5, 0.5)
	glVertex3f(-0.5,-0.5, 0.5)

	glNormal3f( 1.0, 0.0, 0.0)
	glVertex3f( 0.5, 0.5, 0.5)
	glVertex3f( 0.5,-0.5, 0.5)
	glVertex3f( 0.5,-0.5,-0.5)
	glVertex3f( 0.5, 0.5,-0.5)

	glNormal3f(-1.0, 0.0, 0.0)
	glVertex3f(-0.5,-0.5,-0.5)
	glVertex3f(-0.5,-0.5, 0.5)
	glVertex3f(-0.5, 0.5, 0.5)
	glVertex3f(-0.5, 0.5,-0.5)
	glEnd()

	size = canvas.GetClientSize()
	w, h = size
	w = max(w, 1.0)
	h = max(h, 1.0)
	xScale = 180.0 / w
	yScale = 180.0 / h
	
	canvas.SwapBuffers()

app = wx.App(False)
frame = MyFrame(None, "Somethin'")
app.MainLoop()

