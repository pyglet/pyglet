import os
import math

from pyglet import image, gl, clock, graphics, sprite

class SpriteBatchGroup(graphics.Group):
    def __init__(self, x, y, parent=None):
        super(SpriteBatchGroup, self).__init__(parent)
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
        self.state = SpriteBatchGroup(x, y)
        self.sprites = []

    def __iter__(self): return iter(self.sprites)

    def __len__(self): return len(self.sprites)

    def hit(self, x, y):
        '''See whether there's a Sprite at the pixel location

        XXX optimise me
        '''
        for sprite in self.sprites:
            if sprite.contains(x, y):
                return sprite
        return None

    def on_mouse_press(self, x, y, buttons, modifiers):
        '''See if the press occurs over a sprite and if it does, invoke the
        on_mouse_press handler on the sprite.

        XXX optimise me
        '''
        sprite = self.hit(x, y)
        if sprite:
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
    def __init__(self, img, x=0, y=0,
            blend_src=gl.GL_SRC_ALPHA, blend_dest=gl.GL_ONE_MINUS_SRC_ALPHA,
            batch=None, parent_state=None, **attributes):
        '''A sprite is an image at some position with some rotation.

        Sprites are blended into the background by default.

        If you're going to have many sprites you should consider creating your
        own SpriteBatch.

        Any additional keyword arguments will be assigned as attributes on the
        sprite. This can be useful if you intend to use `update_kinematics`.
        '''

        # default parent_state to batch state if it has one
        if parent_state is None and hasattr(batch, 'state'):
            parent_state = batch.state

        super(Sprite, self).__init__(img, x, y, blend_src, blend_dest,
            batch, parent_state)

        # if the parent wants us to register then do so
        if self._batch is not None and hasattr(self._batch, 'add_sprite'):
            self._batch.add_sprite(self)

        # arbitrary attributes
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

    def on_mouse_press(self, x, y, buttons, modifiers):
        pass

    def get_top(self):
        t = self._texture
        height = t.height * self._scale
        return self._y + height - t.anchor_y
    def set_top(self, y):
        t = self._texture
        height = t.height * self._scale
        self._y = y - height + t.anchor_y
        self._update_position()
    top = property(get_top, set_top)

    def get_bottom(self):
        return self._y - self._texture.anchor_y
    def set_bottom(self, y):
        self._y = y + self._texture.anchor_y
        self._update_position()
    bottom = property(get_bottom, set_bottom)

    def get_left(self):
        return self._x - self._texture.anchor_x
    def set_left(self, x):
        self._x = x + self._texture.anchor_x
        self._update_position()
    left = property(get_left, set_left)

    def get_right(self):
        t = self._texture
        width = t.width * self._scale
        return self._x + width - t.anchor_x
    def set_right(self, x):
        t = self._texture
        width = t.width * self._scale
        self._x = x - width + t.anchor_x
        self._update_position()
    right = property(get_right, set_right)

    def get_center(self):
        t = self._texture
        left = self._x - t.anchor_x
        bottom = self._y - t.anchor_y
        height = t.height * self._scale
        width = t.width * self._scale
        return (left + width/2, bottom + height/2)
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

