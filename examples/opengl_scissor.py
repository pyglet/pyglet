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
        self._area = x, y, width, height

    @property
    def x(self):
        return self._area[0]

    @x.setter
    def x(self, x):
        self._area = x, self.y, self.width, self.height

    @property
    def y(self):
        return self._area[1]

    @y.setter
    def y(self, y):
        self._area = self.x, y, self.width, self.height

    @property
    def width(self):
        return self._area[2]

    @width.setter
    def width(self, width):
        self._area = self.x, self.y, width, self.height

    @property
    def height(self):
        return self._area[3]

    @height.setter
    def height(self, height):
        self._area = self.x, self.y, self.width, height

    def set_state(self):
        glEnable(GL_SCISSOR_TEST)
        glScissor(*self._area)

    def unset_state(self):
        glDisable(GL_SCISSOR_TEST)

    # For efficient drawing, pyglet will internally consolidate equivalent
    # Groups into the same draw call when you add objects to a Batch. For
    # this to work, __eq__ and __hash__ methods must be defined so that the
    # Groups can be checked for equality.
    def __eq__(self, other):
        return (self.__class__ is other.__class__ and
                self.parent is other.parent and
                self._area == other._area)

    def __hash__(self):
        return hash((id(self.parent), self._area))


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
