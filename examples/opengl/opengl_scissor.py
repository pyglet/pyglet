"""In some cases, you may want to restrict drawing to a specific part
of the Window. To accomplish this, you can use an OpenGL Scissor
area. In this example we use a Camera view with a Scissor area
attached to a Group to enforce this. Any Sprites/Labels that are
assigned to this Group will not be drawn outside the specified area.
Drag the mouse to move the position.
"""

import pyglet

from pyglet.sprite import Sprite


window = pyglet.window.Window(width=500, height=500)
batch = pyglet.graphics.Batch()

label = pyglet.text.Label("Drag the mouse to move the scissor area.", x=5, y=5, batch=batch)


@window.event
def on_draw():
    window.clear()
    batch.draw()


###################################################
# A Camera view that enforces a Scissor area
###################################################

# Create a child view of the window's default camera. A Scissor area
# on this view clips anything drawn with it. Any Sprites/Labels that
# are drawn through this view will not render outside the area.
scissor_view = window.camera.create_view(inherit=True)
scissor = scissor_view.set_scissor_area(x=50, y=50, width=300, height=300)

# Assign the view to a Group, so anything in the Group is drawn with it.
scissor_group = pyglet.graphics.Group()
scissor_group.set_camera(scissor_view)

###################################################
# Create some Sprites
###################################################

# Create a bunch of Sprites, and assign them to our scissor group. Any parts
# of these Sprites that are outside the specified area will not be drawn.
sprites = []
img = pyglet.resource.texture('pyglet.png')
for x in range(5):
    for y in range(5):
        sprite = Sprite(img, x * img.width, y * img.height, group=scissor_group, batch=batch)
        sprites.append(sprite)


@window.event
def on_mouse_drag(x, y, dx, dy, *etc):
    scissor.x += dx
    scissor.y += dy


pyglet.app.run()
