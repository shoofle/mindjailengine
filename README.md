mindjailengine
==============

A relatively simple game engine in python. Thanks, I'm shoofle.
---------------------------------------------------------------

Check out what it looks like in [this (extremely choppy, because of the screen recorder) video!](http://youtu.be/-OvUgrvlsug)

This is a 2D, physics-y game engine in python. At present, it uses the [pyglet](http://www.pyglet.org/) library for windowing and opengl bindings, although I'm interested in eventually moving to some kind of gui kit. It's very undecided. I like pyglet a lot. For the moment, graphics are limited to vectory stuff, because it's drawn through hand-crafted opengl loops. Still in the works. I do like the vector look. Not sure where that's going to go.

In order to use this, you'll need python (python3 preferred!) and pyglet; feel free to use the `requirements.txt` file or to install by `pip install pyglet`. When pyglet's in place, just do `python mindjailengine.py` and it'll go. Not too much to it!

Replacing pyglet was high on my list of priorities, and was a major roadblock to actually going further with this project, but fortunatey pyglet finally released 1.2 and now supports python3 and fixed its OSX support! So I can work on this again!

--------

Fast collision detection is a python for any system of interacting dynamic objects, and it's made no easier by python's less-than-urgent nature. This project has given me a better visceral appreciation for data structures and algorithmic speed than anything else I've worked on - including precisely how *magical* hash tables are. Collision detection is facilitated in this engine by a multi-tiered spatial hashing structure, which can be found in `collision_structures.py`. It is occasionally referred to as a tree, because I haven't gotten around to refactoring from when I was using quadtrees.

--------

This engine runs on a component-entity system - if you want an entity to have a physics component, you set `entity.physics\_component` to be a PhysicsComponent. The component classes are defined (at least for the most part) in components.py. This system is fairly new and still in the throes of its birth.

--------

The vector class (`v` in `vectors.py`) is something I've tried pretty hard to keep lightweight. In theory, it should behave as close to a primitive type as possible. There's a number of things I've done towards that goal (mostly implementing all the basic operator functionalities so I can actually _do_ math with them easily) but the most recent and most surprising thing I've done is switch them to use \_\_slots\_\_. This means that the keys for the attributes of each vector object are internally stored using a tuple, rather than a dict. This means it's not run-time changeable, but I don't even want that! In practice, running a quick test with memory_profiler (simply allocating a thousand vectors in a list), the \_\_slots\_\_ vects seem to take 172 bytes each, as compared to 445 bytes each without \_\_slots\_\_. For comparison, storing in a list the same number of tuples of two numbers seems to take 121 bytes each.
To be sure, 172 bytes for storing a pair of floating point numbers is pretty awful, but hey! It's close to tuples!

--------

I'm working on this with the intent of making a game in it, for funsies and for learning experience. I started this in my second year of college, and I wasn't particularly experienced then - and while I'm by no means a guru, I've grown a lot. What I'm saying is that I'm really nervous about people looking at old code I've written. Look with care! I'm also always, *always* happy to hear advice. If you've got something to add or contribute, I'm interested!

Incidentally, there are some *really* wacky things I've done in here - especially in the `components` library - and I ask you not to judge too harshly. I experiment a lot, but I try to keep the dependencies between different parts of this codebase as sensible as possible - so, yes, I did define something that does a raw `self.__dict__.update(kwargs)` in its constructor... but I do know that that's ridiculous and irresponsible :) I'm trying to use python to do a bunch of different things, including functioning as a game data specification language. That involves some introspection to get the nicest resulting syntax possible! idk. Anyway.
