"""In some cases, you may want to restrict drawing to a specific area
of the Window. To accomplish this, you can use an OpenGL Scissor
area. In this example we define a custom Group that enforces this
Scissor area. Any Sprites/Labels that are assigned to this Group
will not be drawn outside of the area.
"""

import pyglet
from pyglet.gl import glEnable, glScissor, glDisable, GL_SCISSOR_TEST


window = pyglet.window.Window(width=500, height=500)
batch = pyglet.graphics.Batch()


@window.event
def on_draw():
    window.clear()
    batch.draw()


###################################################
# A custom Group class that enforces a Scissor area
###################################################

class ScissorGroup(pyglet.graphics.Group):
    """A Custom Group that defines a "Scissor" area.

    If a Sprite/Label is in this Group, any parts of it that
    fall outside of the specified area will not be drawn.
    NOTE: You should use the same exact group instance
    for every object that will use the group, equal groups
    will still be kept seperate.

    :Parameters:
        `x` : int
            The X coordinate of the Scissor area.
        `x` : int
            The X coordinate of the Scissor area.
        `width` : int
            The width of the Scissor area.
        `height` : int
            The height of the Scissor area.

    """

    def __init__(self, x, y, width, height, parent=None):
        super().__init__(parent)
        self.x, self.y = x, y
        self.width, self.height = width, height

    @property
    def area(self):
        return self.x, self.y, self.width, self.height

    @area.setter
    def area(self, area):
        self.x, self.y, self.width, self.height = area

    def set_state(self):
        glEnable(GL_SCISSOR_TEST)
        glScissor(self.x, self.y, self.width, self.height)

    def unset_state(self):
        glDisable(GL_SCISSOR_TEST)


###################################################
# Create an instance of our Group, and some Sprites
###################################################

# Create an instance of the ScissorGroup that defines the center of the window:
scissor_group = ScissorGroup(x=50, y=50, width=400, height=400)

# Create a bunch of Sprites assigned to our custom Group. Any parts of these
# Sprites that is outside of the specified area will not be drawn.
sprites = []
img = pyglet.resource.image('pyglet.png')
for x in range(5):
    for y in range(5):
        sprite = pyglet.sprite.Sprite(
            img, x*img.width, y*img.height, group=scissor_group, batch=batch)
        sprites.append(sprite)


pyglet.app.run()
