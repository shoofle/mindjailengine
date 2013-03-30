mindjailengine
==============

A relatively simple game engine in python. Thanks, I'm shoofle.

This is a 2D, physics-y game engine in python. At present, it uses the [pyglet](http://www.pyglet.org/) library for windowing and opengl bindings, although this might change sometime soon in favor of something more frequently updated. For the moment, graphics are limited to vectory stuff, because it's all basically hand-crafted opengl loops. That's still in the works, but I like the vector look. Not sure where that's going to go.

--------

Probably the coolest single _part_ of this endeavor is my (hand-crafted!) QuadTree for collision detection. Of course, hand-crafted means it's far from sterling quality, but hey, it's sped up my game. The basic idea of a quadtree is to recursively subdivide the world into quadrants, so that you know that an object in one quadrant can't touch objects in another. There are some issues, and I've implemented some... unusual solutions, but it's all good.

Of mild interest is one of those solutions - before I took the plunge and coded up a quadtree, I made what I've called a sort-search list. It keeps track of two copies of a list of objects, sorted by their extents on the x-axis - ascending by minima and descending by maxima. It makes for a neat trick to massively cut down on time for finding collisions, but only if objects are well-distributed along the x-axis.

And before you ask, yes, I have done some tests, and both of these have noticeably improved my runtimes over a brute-force solution :)

--------

In the future, I'm hoping to move to something like a component-entity system, but my one attempt at it made me realize just how rusty I am at the task of weaving a whole system from fibers of thought. Well, I'm going to move towards it at some point - right now mod\_screen.py is just a little too cluttered. I'm also considering changing the names for a lot of functions, which weren't named very well.

--------

I'm working on this with the intent of making a game in it, for funsies and for learning experience. I started this in my second year of college, and I wasn't particularly experienced then - and while I'm by no means a guru, I've grown a lot. What I'm saying is that I'm really nervous about people looking at old code I've written.


