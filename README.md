mindjailengine
==============

A relatively simple game engine in python. Thanks, I'm shoofle.
---------------------------------------------------------------

This is a 2D, physics-y game engine in python. At present, it uses the [pyglet](http://www.pyglet.org/) library for windowing and opengl bindings, although this might change sometime soon in favor of something more frequently updated. For the moment, graphics are limited to vectory stuff, because it's all basically hand-crafted opengl loops. That's still in the works, but I like the vector look. Not sure where that's going to go.

In order to use this, you'll need python (2.6, I think? 2.7? Unfortunately, it's not up to python3 yet :( I hope to make that happen!) and pyglet; I installed pyglet using [pip](https://pypi.python.org/pypi/pip) (`pip install pyglet`). When you've got pyglet in place, just do `python mindjailengine.py` and it'll go. Not too much to it.

Unfortunately, pyglet is ailing and unhappy and doesn't play nice with 64-bit machines, so you might need 32-bit python in order to run this. Replacing pyglet is on my list of things to do!

--------

Much of my work on this project (certainly unreasonably much of it) is recorded in `collision_structures.py`. There you can see a wide array (hah!) of data structures I've developed for the purpose of speeding up collision detection. Fast collision detection is a challenge for any system of interacting dynamic objects, and it's certainly made no easier by python's less-than-urgent nature. At the moment I am fairly well satisfied with the spatial hashing algorithm I've implemented in the SpatialGrid class, and I hope to move to other things promptly.

--------

In the future, I'm hoping to move to something like a component-entity system, but my one attempt at it made me realize just how rusty I am at the task of weaving a whole system from fibers of thought. Well, I'm going to move towards it at some point - right now `mod_screen.py` is just a little too cluttered. I'm also considering changing the names for a lot of functions, which weren't named very well.

--------

I'm working on this with the intent of making a game in it, for funsies and for learning experience. I started this in my second year of college, and I wasn't particularly experienced then - and while I'm by no means a guru, I've grown a lot. What I'm saying is that I'm really nervous about people looking at old code I've written.


