from random import uniform
from vectors import v
from components import *
from world_entities import *

def generate(self):
	manifest = []

	player = PlayerBall(self, location = v(0,0))
	manifest.append( player )
	manifest.append( CameraFollower(self, latch=player, spring=50, damping=10) )

	manifest.append( FreeBall(self, location = v(0,-50)) )
	manifest.append( FreeBall(self, location = v(-100,0)) )
	manifest.append( FreeBall(self, location = v(100,0)) )
	manifest.append( FreeBall(self, location = v(0, 1700), rad=80) )

	manifest.append( Spawner(self, location = v(-500, 1500), rad=250) )
	manifest.append( Spawner(self, location = v(500, 1500), rad=250) )
			
	manifest.append( EnemyBall(self, location = v(-200,30), rad=30) )
	manifest.append( EnemyBall(self, location = v(-260,0), rad=30) )
	manifest.append( EnemyBall(self, location = v(-100,60), rad=30) )

	height = 1000
	width = 4000
	quantity = 100
	balls = [ ObstacleBall(self, location=v(uniform(-1,1)*width, uniform(-1,1)*height), rad=40) for i in range(quantity) ]
	manifest.extend(balls)

	wavelength = 600
	depth = 150
	h = -1000

	wave_1 = [ ObstacleLine(self, location=v(i*wavelength, h), endpoint=v((i+0.5)*wavelength, h+depth), thick=20) for i in range(-10,10) ]
	manifest.extend(wave_1)
	wave_2 = [ ObstacleLine(self, location=v((i+0.5)*wavelength, h+depth), endpoint=v((i+1)*wavelength, h), thick=20) for i in range(-10,10) ]
	manifest.extend(wave_2)

	dummy = {'renderable_component': text.Label( 'THIS IS A TEST', 'Arial', 24, color = (0, 0, 0, 200), 
			x = self.window.width/2, y = self.window.height/4, anchor_x="center", anchor_y="center", 
			width=3*self.window.width/4, height=3*self.window.height/4, multiline=1)}
	manifest.append( dummy )

	return manifest
