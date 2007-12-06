
import os
import weakref
import math

from pyglet import image, gl, clock
import graphics

import rect

class Layer(graphics.Batch):
    pass


class TextureCache(object):
    _cache = None
    def _get_cache(self):
        if self._cache is not None:
            return self._cache
        shared_object_space = gl.get_current_context().object_space
        if not hasattr(shared_object_space, 'spryte_texture_cache'):
            shared_object_space.spryte_texture_cache = {}
        self._cache = shared_object_space.spryte_texture_cache
        return self._cache
    cache = property(_get_cache)

    def __contains__(self, id):
        return id in self.cache

    def __setitem__(self, id, texture):
        self.cache[id] = texture

    def __getitem__(self, id):
        return self.cache[id]

    def clear(self):
        self._cache.clear()

texture_cache = TextureCache()


class TextureState(graphics.AbstractState):
    def __init__(self, texture, blended):
        self.texture = texture
        self.blended = blended

    def set(self):
        gl.glPushAttrib(gl.GL_ENABLE_BIT)
        if self.blended:
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glEnable(self.texture.target)
        gl.glBindTexture(self.texture.target, self.texture.id)

    def unset(self):
        gl.glPopAttrib()

    def __hash__(self):
        return hash((self.texture.target, self.texture.id, self.blended))

    def __cmp__(self, other):
        return cmp((self.texture.target, self.texture.id, self.blended),
            (other.texture.target, other.texture.id, self.blended))

    def __eq__(self, other):
        return (self.texture.target == other.texture.target and
            self.texture.id == other.texture.id and
            self.blended == other.blended)


class Sprite(rect.Rect):
    def __init__(self, im, layer, x, y, file=None, blended=True, rotation=0,
            rothandle=(0, 0), dx=0, dy=0, ddx=0, ddy=0, **attributes):
        '''
        >>> sprite = Sprite('car.png', layer, 100, 100)
        '''
        if isinstance(im, image.Texture):
            # assume we've been passed a cached texture
            texture = self._texture = im
        else:
            assert isinstance(im, str)
            if im not in texture_cache:
                texture_cache[im] = image.load(im, file).texture
            texture = self._texture = texture_cache[im]

        super(Sprite, self).__init__(x, y, texture.width, texture.height)
        w, h = self._width, self._height

        vertices = [x, y,   x+w,   y,    x+w,   y+h,    x,    y+h]
        t = texture.tex_coords
        tex_coords = [
             t[0][0], t[0][1],
             t[1][0], t[1][1],
             t[2][0], t[2][1],
             t[3][0], t[3][1],
        ]

        # XXX use point sprites if they're available

        self.blended = blended
        self.graphics_state = TextureState(texture, self.blended)
        self.primitive = layer.add(4, gl.GL_QUADS, self.graphics_state,
            ('v2f/stream', vertices),
            ('t2f/stream', tex_coords),         # allow animation
        )
        self.layer = layer
        self._x = x
        self._y = y
        self.dx = dx
        self.dy = dy
        self.ddx = ddx
        self.ddy = ddy
        self._rotation = rotation
        self._rothandle = rothandle
        self.__dict__.update(attributes)

    def delete(self):
        self.graphics_state = None
        self.primitive.delete()

    def set_texture(self, texture):
        t = texture.tex_coords
        tex_coords = [
             t[0][0], t[0][1],
             t[1][0], t[1][1],
             t[2][0], t[2][1],
             t[3][0], t[3][1],
        ]
        new_state = TextureState(texture, self.blended)
        if new_state != self.graphics_state:
            # the texture has changed, acknowledge new state
            vertices = self.primitive.vertices[:]
            self.primitive.delete()
            self.graphics_state = new_state
            self.primitive = layer.add(4, gl.GL_QUADS, new_state,
                ('v2f/stream', vertices),
                ('t2f/stream', tex_coords),         # allow animation
            )
        else:
            self.primitive.tex_coords[:] = tex_coords
    texture = property(lambda self: self._texture, set_texture)

    def set_x(self, value):
        self._x = value
        self._set_vertices()
    x = property(lambda self: self._x, set_x)

    def set_y(self, value):
        self._y = value
        self._set_vertices()
    y = property(lambda self: self._y, set_y)

    def set_pos(self, pos):
        self._x, self._y = pos
        self._set_vertices()
    pos = property(lambda self: (self._x, self._y), set_pos)

    def set_width(self, value):
        self._width = value
        self._set_vertices()
    width = property(lambda self: self._width, set_width)

    def set_height(self, value):
        self._height = value
        self._set_vertices()
    height = property(lambda self: self._height, set_height)

    def set_size(self, value):
        self._width, self._height = value
        self._set_vertices()
    size = property(lambda self: (self._width, self._height), set_size)

    def set_velocity(self, value):
        self.dx, self.dy = value
    velocity = property(lambda self: (self.dx, self.dy), set_velocity)

    def set_acceleration(self, value):
        self.ddx, self.ddy = value
    acceleration = property(lambda self: (self.ddx, self.ddy),
        set_acceleration)

    # XXX set_scale
    # XXX set_rect

    def set_rotation(self, rotation):
        self._rotation = rotation
        self._set_vertices()
    rotation = property(lambda self: self._rotation, set_rotation)

    def _set_vertices(self):
        r = self._rotation
        if r:
            sr = math.sin(r)
            cr = math.cos(r)
            x = self._x
            y = self._y
            w = self._width
            h = self._height
            if self._rothandle == (0, 0):
                crw = cr * w
                srh = sr * h
                srw = sr * w
                crh = cr * h
                self.primitive.vertices[:] = [
                    int(x), int(y),
                    int(x + crw), int(y + srw),
                    int(x + crw - srh), int(y + srw + crh),
                    int(x - srh), int(y + crh)
                ]
            else:
                vertices = []
                rx, ry = self._rothandle
                x += rx
                y += ry
                px = -rx
                py = -ry
                vertices.append(int(x + cr * px - sr * py))
                vertices.append(int(y + sr * px + cr * py))
                px = w - rx
                vertices.append(int(x + cr * px - sr * py))
                vertices.append(int(y + sr * px + cr * py))
                py = h - ry
                vertices.append(int(x + cr * px - sr * py))
                vertices.append(int(y + sr * px + cr * py))
                px = -rx
                vertices.append(int(x + cr * px - sr * py))
                vertices.append(int(y + sr * px + cr * py))
                self.primitive.vertices[:] = vertices
        else:
            x = int(self._x)
            y = int(self._y)
            w = int(self._width)
            h = int(self._height)
            self.primitive.vertices[:] = [x, y, x + w, y, x + w, y + h, x, y + h]

    def update_kinematics(self, dt):
        '''Update the sprite with simple kinematics for the passage of "dt"
        seconds.

        The sprite's acceleration (.ddx and .ddy) are added to the sprite's
        velocity.
        
        The sprite's veclocity (.dx and .dy) are added to the sprite's
        position.

        Sprite rotation is included in the calculations. That is, positive dy
        is always pointing up from the top of the sprite and positive dx is
        always pointing right from the sprite.
        '''
        if self.ddx: self.dx += self.ddx * dt
        if self.ddy: self.dy += self.ddy * dt
        if self.dx == self.dy == 0: return

        r = self._rotation
        x, y = self._x, self._y
        if not r:
            self.pos = (x + self.dx, y + self.dy)
        else:
            x, y = self.pos
            cr = math.cos(r)
            sr = math.sin(r)
            self.pos = (x + cr * self.dx - sr * self.dy,
                y + sr * self.dx + cr * self.dy)


class AnimatedSprite(Sprite):
    def __init__(self, im, rows, frames, layer, x, y, period, file=None,
            blended=True, loop=False, callback=None, **attributes):
        '''

        "im" may be a filename or a pyglet.image.UniformTextureSequence

        >>> explosion = Sprite('explosion.png', 2, 8, layer, 100, 100)
        '''
        if isinstance(im, image.UniformTextureSequence):
            self.texture_sequence = im.self.texture_sequence
        else:
            if im not in texture_cache:
                texture_cache[im] = image.ImageGrid(image.load(im, file),
                    rows, frames).texture_sequence
            self.texture_sequence = texture_cache[im]

        # animation controls
        self.period = period
        self.loop = loop
        self.callback = callback
        self.time = 0
        self.frame = 0
        self.finished = False
        clock.schedule(self.update)

        # complete initialisation with first frame
        im = self.texture_sequence[0].texture
        super(AnimatedSprite, self).__init__(im, layer, x, y, blended=blended,
            **attributes)

    def delete(self):
        clock.unschedule(self.update)
        self.texture_sequence = None
        super(AnimatedSprite, self).delete()

    def update(self, dt):
        self.time += dt
        old_frame = self.frame
        while self.time >= self.period:
            self.time -= self.period
            self.frame += 1
            if self.frame == len(self.texture_sequence):
                self.frame = 0 
                if not self.loop:
                    self.finished = True
                    if self.callback is not None:
                        clock.unschedule(self.update)
                        self.callback(self)
                    else:
                        self.delete()
                    return
        if self.frame != old_frame:
            # update my image
            self.texture = self.texture_sequence[self.frame]

