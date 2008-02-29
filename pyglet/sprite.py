#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import math

from pyglet.gl import *
from pyglet import clock
from pyglet import event
from pyglet import graphics
from pyglet import image

class SpriteGroup(graphics.AbstractGroup):
    def __init__(self, texture, blend_src, blend_dest, parent=None):
        super(SpriteGroup, self).__init__(parent)
        self.texture = texture
        self.blend_src = blend_src
        self.blend_dest = blend_dest

    def set_state(self):
        glEnable(self.texture.target)
        glBindTexture(self.texture.target, self.texture.id)

        glPushAttrib(GL_COLOR_BUFFER_BIT)
        glEnable(GL_BLEND)
        glBlendFunc(self.blend_src, self.blend_dest)

    def unset_state(self):
        glPopAttrib()
        glDisable(self.texture.target)

    def __eq__(self, other):
        return (other.__class__ is self.__class__ and 
                self.parent is other.parent and 
                self.texture.target == other.texture.target and
                self.texture.id == other.texture.id and
                self.blend_src == other.blend_src and
                self.blend_dest == other.blend_dest)

    def __hash__(self):
        return hash((id(self.parent), 
                     self.texture.id, self.texture.target,
                     self.blend_src, self.blend_dest))

class Sprite(event.EventDispatcher):
    _batch = None
    _animation = None
    _rotation = 0
    _opacity = 255
    _scale = 1.0
    _visible = True

    def __init__(self, 
                 img, x=0, y=0, 
                 blend_src=GL_SRC_ALPHA,
                 blend_dest=GL_ONE_MINUS_SRC_ALPHA,
                 batch=None,
                 group=None):

        if batch is not None:
            self._batch = batch

        self._x = x
        self._y = y

        if isinstance(img, image.Animation):
            self._animation = img
            self._frame_index = 0
            self._texture = img.frames[0].image.get_texture()
            self._next_dt = img.frames[0].duration
            clock.schedule_once(self._animate, self._next_dt)
        else:
            self._texture = img.get_texture()

        self._group = SpriteGroup(self._texture, blend_src, blend_dest, group)
        self._create_vertex_list()

    def __del__(self):
        if self._vertex_list is not None:
            self._vertex_list.delete()

    def delete(self):
        '''Force immediate removal from video memory.  
        
        This is often necessary when using batches, as the Python garbage
        collector will not necessarily call the finalizer as soon as the
        sprite is garbage.
        '''
        if self._animation:
            clock.unschedule(self._animate)
        self._vertex_list.delete()
        self._vertex_list = None

    def _animate(self, dt):
        self._frame_index += 1
        if self._frame_index >= len(self._animation.frames):
            self.dispatch_event('on_animation_end')
            self._frame_index = 0

        frame = self._animation.frames[self._frame_index]
        self._set_texture(frame.image.get_texture())

        if frame.duration is not None:
            duration = frame.duration - (self._next_dt - dt)
            duration = min(max(0, duration), frame.duration)
            clock.schedule_once(self._animate, duration)
            self._next_dt = duration
        else:
            self.dispatch_event('on_animation_end')

    def _set_batch(self, batch):
        if self._batch == batch:
            return

        if batch is not None and self._batch is not None:
            self._batch.migrate(self._vertex_list, GL_QUADS, self._group, batch)
            self._batch = batch
        else:
            self._vertex_list.delete()
            self._batch = batch
            self._create_vertex_list()

    def _get_batch(self):
        return self._batch

    batch = property(_get_batch, _set_batch)

    def _set_group(self, group):
        if self._group.parent == group:
            return

        self._group = SpriteGroup(self._texture, 
                                  self._group.blend_src, 
                                  self._group.blend_dest,
                                  group)

        if self._batch is not None:
           self._batch.migrate(self._vertex_list, GL_QUADS, self._group,
                               self._batch)

    def _get_group(self):
        return self._group.parent

    group = property(_get_group, _set_group)

    def _get_image(self):
        if self._animation:
            return self._animation
        return self._texture

    def _set_image(self, img):
        if self._animation is not None:
            clock.unschedule(self._animate)
            self._animation = None

        if isinstance(img, image.Animation):
            self._animation = img
            self._frame_index = 0
            self._set_texture(img.frames[0].image.get_texture())
            self._next_dt = img.frames[0].duration
            clock.schedule_once(self._animate, self._next_dt)
        else:
            self._set_texture(img.get_texture())
        self._update_position()

    image = property(_get_image,
                     _set_image)

    def _set_texture(self, texture):
        if texture.id is not self._texture.id:
            self._group = SpriteGroup(texture, 
                                      self._group.blend_src, 
                                      self._group.blend_dest,
                                      self._group.parent)
            if self._batch is None:
                self._vertex_list.tex_coords[:] = texture.tex_coords
            else:
                self._vertex_list.delete()
                self._texture = texture
                self._create_vertex_list()
        else:
            self._vertex_list.tex_coords[:] = texture.tex_coords
        self._texture = texture

    def _create_vertex_list(self):
        if self._batch is None:
            self._vertex_list = graphics.vertex_list(4, 
                'v2i', 'c4B', ('t3f', self._texture.tex_coords))
        else:
            self._vertex_list = self._batch.add(4, GL_QUADS, self._group,
                'v2i', 'c4B', ('t3f', self._texture.tex_coords))
        self._update_position()
        self._update_color()

    def _update_position(self):
        img = self._texture
        if not self._visible:
            self._vertex_list.vertices[:] = [0, 0, 0, 0, 0, 0, 0, 0]
        elif self._rotation:
            x1 = -img.anchor_x * self._scale
            y1 = -img.anchor_y * self._scale
            x2 = x1 + img.width * self._scale
            y2 = y1 + img.height * self._scale
            x = self._x
            y = self._y

            r = -math.radians(self._rotation)
            cr = math.cos(r)
            sr = math.sin(r)
            ax = int(x1 * cr - y1 * sr + x)
            ay = int(x1 * sr + y1 * cr + y)
            bx = int(x2 * cr - y1 * sr + x)
            by = int(x2 * sr + y1 * cr + y)
            cx = int(x2 * cr - y2 * sr + x)
            cy = int(x2 * sr + y2 * cr + y)
            dx = int(x1 * cr - y2 * sr + x)
            dy = int(x1 * sr + y2 * cr + y)

            self._vertex_list.vertices[:] = [ax, ay, bx, by, cx, cy, dx, dy]
        elif self._scale != 1.0:
            x1 = int(self._x - img.anchor_x * self._scale)
            y1 = int(self._y - img.anchor_y * self._scale)
            x2 = int(x1 + img.width * self._scale)
            y2 = int(y1 + img.height * self._scale)
            self._vertex_list.vertices[:] = [x1, y1, x2, y1, x2, y2, x1, y2]
        else:
            x1 = int(self._x - img.anchor_x)
            y1 = int(self._y - img.anchor_y)
            x2 = x1 + img.width
            y2 = y1 + img.height
            self._vertex_list.vertices[:] = [x1, y1, x2, y1, x2, y2, x1, y2]

    def _update_color(self):
        self._vertex_list.colors[:] = [255, 255, 255, int(self._opacity)] * 4

    def set_position(self, x, y):
        self._x = x
        self._y = y
        self._update_position()

    position = property(lambda self: (self._x, self._y),
                 lambda self, t: self.set_position(*t))

    def _set_x(self, x):
        self._x = x
        self._update_position()

    x = property(lambda self: self._x,
                 _set_x)

    def _set_y(self, y):
        self._y = y
        self._update_position()

    y = property(lambda self: self._y,
                 _set_y)

    def _set_rotation(self, rotation):
        self._rotation = rotation
        self._update_position()

    rotation = property(lambda self: self._rotation,
                        _set_rotation)

    def _set_scale(self, scale):
        self._scale = scale
        self._update_position()

    scale = property(lambda self: self._scale,
                     _set_scale)

    width = property(lambda self: self._texture.width * self._scale)
    height = property(lambda self: self._texture.height * self._scale)

    def _set_opacity(self, opacity):
        self._opacity = opacity
        self._update_color()

    opacity = property(lambda self: self._opacity,
                       _set_opacity)

    def _set_visible(self, visible):
        self._visible = visible
        self._update_position()

    visible = property(lambda self: self._visible,
                       _set_visible)

    def draw(self):
        self._group.set_state_recursive()
        self._vertex_list.draw(GL_QUADS)
        self._group.unset_state_recursive()

Sprite.register_event_type('on_animation_end')
