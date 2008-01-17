
import os
import weakref
import math

from pyglet import image, gl, clock
import graphics

import rect
#import hashmap

class LayerState(graphics.AbstractState):
    def __init__(self, x, y, blend, parent=None):
        super(LayerState, self).__init__(parent)
        self.x, self.y, self.blend = x, y, blend

    def set(self):
        gl.glPushAttrib(gl.GL_ENABLE_BIT)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glTranslatef(self.x, self.y, 0)

    def unset(self):
        gl.glTranslatef(-self.x, -self.y, 0)
        gl.glPopAttrib(gl.GL_ENABLE_BIT)

class Layer(graphics.Batch):
    def __init__(self, x=0, y=0, blended=False):
        super(Layer, self).__init__()
        self.state = LayerState(x, y, blended)
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


class Sprite(rect.Rect):
    def __init__(self, im, layer, x, y, file=None, blended=True, rotation=0,
            rothandle=(0, 0), dx=0, dy=0, ddx=0, ddy=0, color=(1, )*4,
            **attributes):
        '''

        "im" is either a filename (and may be accompanied by the "file"
        argument file object) *or* a pyglet.image.Texture instance. If it's
        the former then spryte will handle caching of images loaded. If it's
        the latter it's assumed the application developer is handling image
        loading and caching.

        Example usage:

        >>> sprite = Sprite('car.png', layer, 100, 100)

        rotation (in degrees)

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

        vertices = [x, y,     x+w,   y,    x+w,   y+h,    x,    y+h]
        self._color = color
        colors =  color * 4
        tex_coords = texture.tex_coords

        # XXX use point sprites if they're available
        # PointSpriteState
        # GL_POINTS

        self.blended = blended
        self.graphics_state = graphics.TextureState(texture,
            parent=layer.state)
        self.primitive = layer.add(4, gl.GL_QUADS, self.graphics_state,
            ('v2f/stream', vertices),
            ('c4f/stream', colors),
            ('t3f/stream', tex_coords),         # allow animation
        )
        self.layer = layer
        self.layer.add_sprite(self)
        self._x = x
        self._y = y
        self.dx = dx
        self.dy = dy
        self.ddx = ddx
        self.ddy = ddy
        self._rotation = math.radians(rotation)
        self._rothandle = rothandle
        self.__dict__.update(attributes)

    def delete(self):
        self.graphics_state = None
        self.layer.remove_sprite(self)
        self.primitive.delete()

    def set_color(self, color):
        if color != self._color:
            self.primitive.colors[:] = color*4
            self._color = color
    color = property(lambda self: self.primitive[:4], set_color)   

    def set_texture(self, texture):
        tex_coords = texture.tex_coords
        if texture.id != self.graphics_state.texture.id:
            # the texture has changed, acknowledge new state
            new_state = graphics.TextureState(texture, parent=self.layer.state)
            vertices = self.primitive.vertices[:]
            colors = self.primitive.colors[:]
            self.primitive.delete()
            self.graphics_state = new_state
            self.primitive = layer.add(4, gl.GL_QUADS, new_state,
                ('v2f/stream', vertices),
                ('c3f/stream', colors),
                ('t3f/stream', tex_coords),         # allow animation
            )
        else:
            self.primitive.tex_coords[:] = tex_coords
    texture = property(lambda self: self._texture, set_texture)

    def set_x(self, value):
        self._x = value
        #self.layer.update_sprite(self)
        self._set_vertices()
    x = property(lambda self: self._x, set_x)

    def set_y(self, value):
        self._y = value
        #self.layer.update_sprite(self)
        self._set_vertices()
    y = property(lambda self: self._y, set_y)

    def set_pos(self, pos):
        self._x, self._y = pos
        #self.layer.update_sprite(self)
        self._set_vertices()
    pos = property(lambda self: (self._x, self._y), set_pos)

    def set_width(self, value):
        self._width = value
        #self.layer.update_sprite(self)
        self._set_vertices()
    width = property(lambda self: self._width, set_width)

    def set_height(self, value):
        self._height = value
        #self.layer.update_sprite(self)
        self._set_vertices()
    height = property(lambda self: self._height, set_height)

    def set_size(self, value):
        self._width, self._height = value
        #self.layer.update_sprite(self)
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
        self._rotation = math.radians(rotation)
        self._set_vertices()
    rotation = property(lambda self: math.degrees(self._rotation),
        set_rotation)

    def get_rotated_rect(self):
        r = self._rotation
        if not r:
            x = int(self._x)
            y = int(self._y)
            w = int(self._width)
            h = int(self._height)
            return [x, y, x + w, y, x + w, y + h, x, y + h]

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
            return [
                int(x), int(y),
                int(x + crw), int(y + srw),
                int(x + crw - srh), int(y + srw + crh),
                int(x - srh), int(y + crh)
            ]

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
        return vertices

    def _set_vertices(self):
        self.primitive.vertices[:] = self.get_rotated_rect()

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

        "im" is either a filename (and may be accompanied by the "file"
        argument file object) *or* a pyglet.image.UniformTextureSequence
        instance. If it's a filename then spryte will handle caching of
        images loaded. If it's the latter it's assumed the application
        developer is handling image loading and caching.

        Example usage:

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
        # XXX instead of running every tick, perhaps schedule delay
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

