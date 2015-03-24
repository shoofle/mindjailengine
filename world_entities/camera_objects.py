import pyglet
from pyglet import text
from pyglet import gl as opengl

import math
from vectors import v

from components import *

from .world_objects import Entity

class CameraFollower(Entity):
	""" This object follows the latch and defines the drawing frustrum and basically sets up cameras. """
	def __init__(self, pscreen, latch=None, spring=30, damping=2):
		self.template_text = "FPS: {0:.2f}\n# of Objects: {1}\n# of Non-Static: {2}"
		label_x, label_y = 3*pscreen.width/4.0, 1*pscreen.height/4.0
		label_width, label_height = pscreen.width/4.0, pscreen.height/8.0
		self.hud_label = text.Label(
				self.template_text.format(0, 0, 0), 
				font_name='Arial', font_size=12, color=(0,0,0,255), 
				x=label_x, y=label_y, width=label_width, height=label_height, 
				anchor_x="center", anchor_y="center", multiline = 1 )

		self.hud_background = pyglet.graphics.vertex_list(4, 'v3f', 'c3f') 
		self.hud_background.vertices = (label_x-label_width/2, label_y-label_height/2, -1, label_x+label_width/2, label_y-label_height/2, -1, label_x+label_width/2, label_y+label_height/2, -1, label_x-label_width/2, label_y+label_height/2, -1)
		self.hud_background.colors = (1, 1, 1)*4

		self.target = latch
		self.spring = spring
		self.damping = damping

		self.scale = 0.5
		self.decay = 0.4

		self.lifecycle = Lifecycle(owner=self, screen=pscreen)
		self.lifecycle.update = self.update
		self.position_component = PositionComponent(owner=self, position=latch.position_component.position)
		
		self.physics_component = PhysicsBody(owner=self, tangible=False, world_forces=False)
		self.renderable_component = Renderable(owner=self)
		self.renderable_component.priority=True
		self.renderable_component.draw = self.draw
	def update(self,timestep):
		# The reason this doesn't call update_inertia is that that also deals with the collision tree.
		self.physics_component.acc += self.spring*(self.target.position_component.position-self.position_component.position)
		self.physics_component.acc -= self.damping*self.physics_component.vel

		targvel = abs(self.target.physics_component.vel)/1000
		scalefactor = 1 + 2/(1+math.exp(-targvel))
		self.scale = self.decay*self.scale + (1-self.decay)/scalefactor

		screen = self.lifecycle.parent_screen
		
		self.hud_label.text = self.template_text.format(screen.window.framerate, len(screen.coltree), len(screen.nonstatic_objects))

	def draw(self):
		parent_screen = self.lifecycle.parent_screen # Need this a lot, so we should pull it into the local namespace.
		opengl.glMatrixMode(opengl.GL_PROJECTION)
		opengl.glLoadIdentity()
		camera_position = self.position_component.position
		#z = 1000.0 + 500/self.scale
		z=600
		clipping_plane_z_coordinates = (-400.0,500.0)

		dist_to_near_plane = min(z-clipping_plane_z_coordinates[0], z-clipping_plane_z_coordinates[1])
		dist_to_near_plane = max(dist_to_near_plane, 0.1) # Ensure that it's not negative.
		dist_to_far_plane = max(z-clipping_plane_z_coordinates[0], z-clipping_plane_z_coordinates[1])

		# Aspect ratio!
		width = 1000.0
		height = width * parent_screen.height / parent_screen.width

		# Define clipping planes.
		left_at_near_plane = -(dist_to_near_plane/z)*width/2
		right_at_near_plane = (dist_to_near_plane/z)*width/2
		bottom_at_near_plane = -(dist_to_near_plane/z)*height/2
		top_at_near_plane = (dist_to_near_plane/z)*height/2

		# Set camera position.
		opengl.glFrustum(left_at_near_plane, right_at_near_plane, bottom_at_near_plane, top_at_near_plane, dist_to_near_plane, dist_to_far_plane)
		opengl.glTranslatef( -camera_position.x, -camera_position.y, -z )

		# Define the rect of what objects should be drawn.
		camera_rect = parent_screen.camera_rect
		camera_rect.x_min, camera_rect.x_max = camera_position.x - width/2.0, camera_position.x + width/2.0
		camera_rect.y_min, camera_rect.y_max = camera_position.y - height/2.0, camera_position.y + height/2.0

		# Draw the HUD.
		opengl.glPushMatrix() # Push onto the stack, so that we can recover after.
		opengl.glLoadIdentity() # Load a blank matrix.
		opengl.glOrtho(0, parent_screen.width, 0, parent_screen.height, -1, 200) # Put us in orthogonal projection.
		
		self.hud_background.draw(opengl.GL_QUADS)
		self.hud_label.draw() # Okay, this is REALLY GODDAMN WEIRD: Removing this line makes it so that the screen is just always blank.

		opengl.glPopMatrix() # Recover the old projection matrix.
		opengl.glMatrixMode(opengl.GL_MODELVIEW)
