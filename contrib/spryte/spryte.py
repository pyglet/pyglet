import os
import math

from pyglet import image, gl, clock, graphics, sprite

class SpriteBatchState(graphics.AbstractState):
    def __init__(self, x, y, parent=None):
        super(SpriteBatchState, self).__init__(parent)
        self.x, self.y = x, y

    def set(self):
        if self.x or self.y:
            gl.glTranslatef(self.x, self.y, 0)

    def unset(self):
        if self.x or self.y:
            gl.glTranslatef(-self.x, -self.y, 0)

class SpriteBatch(graphics.Batch):
    def __init__(self, x=0, y=0):
        super(SpriteBatch, self).__init__()
        self.state = SpriteBatchState(x, y)
        self.sprites = []

    def __iter__(self): return iter(self.sprites)

    def __len__(self): return len(self.sprites)

    def on_mouse_press(self, x, y, buttons, modifiers):
        '''See if the press occurs over a sprite and if it does, invoke the
        on_mouse_press handler on the sprite.

        XXX optimise me
        '''
        for sprite in self.sprites:
            if sprite.contains(x, y):
                return sprite.on_mouse_press(x, y, buttons, modifiers)
        return False

    def add_sprite(self, sprite):
        self.sprites.append(sprite)

    def remove_sprite(self, sprite):
        self.sprites.remove(sprite)

    def clear(self):
        for s in self.sprites: s.delete()
        self.sprites = []

class Sprite(sprite.Sprite):
    def __init__(self, 
                 img, x=0, y=0, 
                 dx=0, dy=0, ddx=0, ddy=0,
                 blend_src=gl.GL_SRC_ALPHA,
                 blend_dest=gl.GL_ONE_MINUS_SRC_ALPHA,
                 batch=None,
                 parent_state=None,
                 **attributes
                 ):

        # default parent_state to batch state if it has one
        if parent_state is None and hasattr(batch, 'state'):
            parent_state = batch.state

        super(Sprite, self).__init__(img, x, y, blend_src, blend_dest,
            batch, parent_state)

        # if the parent wants us to register then do so
        if self._batch is not None and hasattr(self._batch, 'add_sprite'):
            self._batch.add_sprite(self)

        self.dx = dx
        self.dy = dy
        self.ddx = ddx
        self.ddy = ddy

        self.__dict__.update(attributes)

    def delete(self):
        if self._batch is not None and hasattr(self._batch, 'remove_sprite'):
            self._batch.remove_sprite(self)

        super(Sprite, self).delete()

    def contains(self, x, y):
        '''Return boolean whether the point defined by x, y is inside the
        rect area.
        '''
        if x < self.left or x > self.right: return False
        if y < self.bottom or y > self.top: return False
        return True

    def intersects(self, other):
        '''Return boolean whether the "other" rect (an object with .x, .y,
        .width and .height attributes) overlaps this Rect in any way.
        '''
        if self.right < other.left: return False
        if other.right < self.left: return False
        if self.top < other.bottom: return False
        if other.top < self.bottom: return False
        return True

    # r/w, in pixels, y extent
    def get_top(self): return self.y + self.height - self._texture.anchor_y
    def set_top(self, y): self.y = y - self.height + self._texture.anchor_y
    top = property(get_top, set_top)

    # r/w, in pixels, y extent
    def get_bottom(self): return self.y - self._texture.anchor_y
    def set_bottom(self, y): self.y = y + self._texture.anchor_y
    bottom = property(get_bottom, set_bottom)

    # r/w, in pixels, x extent
    def get_left(self): return self.x - self._texture.anchor_x
    def set_left(self, x): self.x = x + self._texture.anchor_x
    left = property(get_left, set_left)

    # r/w, in pixels, x extent
    def get_right(self): return self.x + self.width - self._texture.anchor_x
    def set_right(self, x): self.x = x - self.width + self._texture.anchor_x
    right = property(get_right, set_right)

    # r/w, in pixels, (x, y)
    def get_center(self):
        # XXX optimise this
        return (self.left + self.width/2, self.bottom + self.height/2)
    def set_center(self, center):
        x, y = center
        # XXX optimise this
        self.left = x - self.width/2
        self.bottom = y - self.height/2
    center = property(get_center, set_center)


def update_kinematics(sprite, dt):
    '''Update the sprite with simple kinematics for the passage of "dt"
    seconds.

    The sprite's acceleration (.ddx and .ddy) are added to the sprite's
    velocity.

    If there's a .speed attribute it's combined with the .rotation to
    calculate a new .dx and .dy.

    The sprite's veclocity (.dx and .dy) are added to the sprite's
    position.

    Sprite rotation is included in the calculations. That is, positive dy
    is always pointing up from the top of the sprite and positive dx is
    always pointing right from the sprite.
    '''
    if sprite.ddx: sprite.dx += sprite.ddx * dt
    if sprite.ddy: sprite.dy += sprite.ddy * dt

    # use speed if it's set
    if hasattr(sprite, 'speed'):
        r = math.radians(sprite._rotation)
        sprite.dx = math.cos(r) * sprite.speed
        sprite.dy = -math.sin(r) * sprite.speed

    if sprite.dx == sprite.dy == 0: return
    x, y = sprite._x, sprite._y
    sprite.position = sprite._x + sprite.dx, sprite._y + sprite.dy

