.. _migration:

Migrating from pyglet 2.0
=========================
pyglet 2.1 contains several small, but breaking changes. Some of these are
usibility improvements, and some are in the interest of improving the quality
of the code base. If you are upgrading from pyglet 2.0 and your game or project
has suddenly stopped working, this is the place for you. The following sections
should hopefully get you up and running again without too much effort. If you
are having an issue that is not covered here, please open up an issue ticket on
`Github <https://github.com/pyglet/pyglet/issues>`_ so that we can add it.

Labels & Text Layouts
---------------------
TBD

Controllers
-----------
The Controller interface has been changed slightly. Analog sticks and dpad
events now dispatch :py:class:`~pyglet.math.Vec2`, instead of individual float
or boolean values. This can potentially save a few lines of code, and gives
easy access to several helper methods found on the Vec classes. For instance,
where you had to do this in the past::

    @controller.event
    def on_dpad_motion(controller, dpleft, dpright, dpup, dpdown):
        if dpleft:
            # move left
        if dpright:
            # move right
        if dpright and dpdown:
            # move diagonal, but have to normalize the values by yourself

You now get a Vec2 instead of booleans that can be used directly::

    @controller.event
    def on_dpad_motion(controller, vector):
        player_position += vector * PLAYER_SPEED
        # Easily normalize for diagonal values:
        player_position += vector.normalize() * PLAYER_SPEED

Vectors can also be useful for analog sticks, because it gives an easy way to
calculate dead-zones using `abs`. For example::

    @controller.event
    def on_stick_motion(controller, name, vector):
        if abs(vector) <= DEADZONE:
            return
        elif name == "leftstick":
            # Do something with the 2D vector
        elif name == "rightstick":
            # Do something with the 2D vector

Normalization of vectors can also be useful for analog sticks. When dealing
with Controllers that have non-circular gates, the The absolute values of their
combined x and y axis can sometimes exceed 1.0. Vector normalization can ensure
that the maximum value stays within range. For example::

            vector = min(vector, vector.normalize())

You can also of course directly access the individual `Vec2.x` & `Vec2.y`
attributes. See :py:class:`~pyglet.math.Vec2` for more details on vector types.
