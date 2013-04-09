import math

class v(object):
	""" Two-dimensional vector. """
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
		return self.x*other.x + self.y*other.y
	def unit(self):
		if abs(self) == 0: return self
		else: return v(self.x/abs(self), self.y/abs(self))
	def proj(self,other):
		return (self*other.unit()) * other.unit()
	def projs(self,other):
		return self*other.unit()
	def rperp(self):
		return v(self.x, -self.y)
	def lperp(self):
		return v(-self.x, self.y)
	def __repr__(self):
		return "v({},{})".format(self.x, self.y)
