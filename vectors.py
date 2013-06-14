import math

class v(object):
	""" Full-featured two-dimensional vector.
	
	I'm not sure if there are speed concerns here or not. This class has two members, x and y, which are the coordinates.
	There are a lot of arithmetic functions defined here. Notably, multiplication checks to see if the other has a dot product, and if so does that.
	There's also a rescale function, which sets the length, and for the most part functions do what their mathematical counterparts do.
	Potentially confusing things: vect.proj(other) will return the component of vect in the direction of other, as a vector.
	vect.projs(other) will return the length of that vector. vect.rperp() and vect.lperp() rotate the vector by 90 degrees, respectively."""
	def __init__(self, x, y):
		self.x = x
		self.y = y
	def __add__(self,other):
		return v(self.x+other.x, self.y+other.y)
	def __radd__(self,other):
		return v(other.x+self.x, other.y+self.y)
	def __sub__(self,other):
		return v(self.x-other.x, self.y-other.y)
	def __rsub__(self,other):
		return v(other.x-self.x, other.y-self.y)
	def __mul__(self,other):
		if hasattr(other,"dot"):
			return self.dot(other)
		return v(other*self.x, other*self.y)
	def __rmul__(self,scalar):
		return v(scalar*self.x, scalar*self.y)
	def __div__(self,scalar):
		return v(self.x/scalar, self.y/scalar)
	def __neg__(self):
		return v(-self.x, -self.y)
	def __pos__(self):
		return self
	def __abs__(self):
		return math.sqrt(self.dot(self))
	def __eq__(self,other):
		if not (hasattr(other,"x") or hasattr(other,"y")): return False
		return not (self.x != other.x or self.y != other.y)
	def __ne__(self,other):
		return not self.__eq__(other)
	def dot(self,other): # Quack!
		""" Dot product of two vectors, which need x and y coordinates. """
		return self.x*other.x + self.y*other.y
	def cross_product(self, other): 
		""" Magnitude of the cross product of self and other. """
		return self.x*other.y - self.y*other.x
	def rescale(self, length):
		mag = abs(self)
		if mag == 0: return self
		else: return v(self.x*length/mag, self.y*length/mag)
	def unit(self):
		return self.rescale(1)
	def proj(self,other):
		""" The component of this vector which is parallel with other."""
		return (self*other.unit()) * other.unit()
	def projs(self,other):
		""" The length of the parallel-with-other component of this vector."""
		return self*other.rescale(1)
	def rperp(self):
		""" Return a copy of the vector, rotated by 90 degrees clockwise."""
		return v(self.y, -self.x)
	def lperp(self):
		""" Return a copy of the vector, rotated 90 degrees anticlockwise."""
		return v(-self.y, self.x)
	def __repr__(self):
		return "v({},{})".format(self.x, self.y)
