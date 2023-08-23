"""2D shapes.

This module provides classes for a variety of simplistic 2D shapes,
such as Rectangles, Circles, and Lines. These shapes are made
internally from OpenGL primitives, and provide excellent performance
when drawn as part of a :py:class:`~pyglet.graphics.Batch`.
Convenience methods are provided for positioning, changing color
and opacity, and rotation (where applicable). To create more
complex shapes than what is provided here, the lower level
graphics API is more appropriate. See the :ref:`guide_graphics`
for more details.

A simple example of drawing shapes::

    import pyglet
    from pyglet import shapes

    window = pyglet.window.Window(960, 540)
    batch = pyglet.graphics.Batch()

    circle = shapes.Circle(700, 150, 100, color=(50, 225, 30), batch=batch)
    square = shapes.Rectangle(200, 200, 200, 200, color=(55, 55, 255), batch=batch)
    rectangle = shapes.Rectangle(250, 300, 400, 200, color=(255, 22, 20), batch=batch)
    rectangle.opacity = 128
    rectangle.rotation = 33
    line = shapes.Line(100, 100, 100, 200, width=19, batch=batch)
    line2 = shapes.Line(150, 150, 444, 111, width=4, color=(200, 20, 20), batch=batch)
    star = shapes.Star(800, 400, 60, 40, num_spikes=20, color=(255, 255, 0), batch=batch)

    @window.event
    def on_draw():
        window.clear()
        batch.draw()

    pyglet.app.run()


.. note:: Some Shapes, such as Lines and Triangles, have multiple coordinates.
          If you update the x, y coordinate, this will also affect the secondary
          coordinates. This allows you to move the shape without affecting it's
          overall dimensions.

.. versionadded:: 1.5.4
"""

from pyglet.shapes2d.collidable import *
from pyglet.shapes2d.drawable import *
