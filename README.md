(note to self: kivy kivy kivy let's try kivy)

mindjailengine
==============

A relatively simple game engine in python. Thanks, I'm shoofle.
---------------------------------------------------------------

Check out what it looks like in [this (extremely choppy, because of the screen recorder) video!](http://youtu.be/-OvUgrvlsug)

This is a 2D, physics-y game engine in python. At present, it uses the [pyglet](http://www.pyglet.org/) library for windowing and opengl bindings, although this might change sometime soon in favor of something more frequently updated. For the moment, graphics are limited to vectory stuff, because it's all basically hand-crafted opengl loops. That's still in the works, but I like the vector look. Not sure where that's going to go.

In order to use this, you'll need python (2.6, I think? 2.7? Unfortunately, it's not up to python3 yet :( I hope to make that happen!) and pyglet; I installed pyglet using [pip](https://pypi.python.org/pypi/pip) (`pip install pyglet`). When you've got pyglet in place, just do `python mindjailengine.py` and it'll go. Not too much to it.

Unfortunately, pyglet is ailing and unhappy and doesn't play nice with 64-bit machines, so you might need 32-bit python in order to run this. Replacing pyglet is on my list of things to do!

--------

Fast collision detection is a python for any system of interacting dynamic objects, and it's made no easier by python's less-than-urgent nature. This project has given me a better visceral appreciation for data structures and algorithmic speed than anything else I've worked on - including precisely how *magical* hash tables are. Collision detection is facilitated in this engine by a multi-tiered spatial hashing structure, which can be found in `collision_structures.py`. It is occasionally referred to as a tree, because I haven't gotten around to refactoring from when I was using quadtrees.

--------

This engine runs on a component-entity system - if you want an entity to have a physics component, you set `entity.physics\_component` to be a PhysicsComponent. The component classes are defined (at least for the most part) in components.py. This system is fairly new and still in the throes of its birth.

--------

The vector class (`v` in `vectors.py`) is something I've tried pretty hard to keep lightweight. In theory, it should behave as close to a primitive type as possible. There's a number of things I've done towards that goal (mostly implementing all the basic operator functionalities so I can actually _do_ math with them easily) but the most recent and most surprising thing I've done is switch them to use \_\_slots\_\_. This means that the keys for the attributes of each vector object are internally stored using a tuple, rather than a dict. This means it's not run-time changeable, but I don't even want that! In practice, running a quick test with memory_profiler (simply allocating a thousand vectors in a list), the \_\_slots\_\_ vects seem to take 172 bytes each, as compared to 445 bytes each without \_\_slots\_\_. For comparison, storing in a list the same number of tuples of two numbers seems to take 121 bytes each.
To be sure, 172 bytes for storing a pair of floating point numbers is pretty awful, but hey! It's close to tuples!

--------

I'm working on this with the intent of making a game in it, for funsies and for learning experience. I started this in my second year of college, and I wasn't particularly experienced then - and while I'm by no means a guru, I've grown a lot. What I'm saying is that I'm really nervous about people looking at old code I've written. Look with care! I'm also always, *always* happy to hear advice. If you've got something to add or contribute, I'm interested!
