#!/usr/bin/env python
# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------
# $Id$

import math

import pyglet
from pyglet.gl import *
from pyglet.math import Mat4, Vec3

from . import reader

pyglet.resource.path.append('res')
pyglet.resource.reindex()

# # Default to OpenAL if available:
# pyglet.options['audio'] = 'openal', 'pulse', 'directsound', 'silent'


# def disc(r, x, y, slices=20, start=0, end=2*math.pi):
#     d = (end - start) / (slices - 1)
#     s = start
#     points = [(x, y)] + [(x + r * math.cos(a*d+s), y + r * math.sin(a*d+s))
#                          for a in range(slices)]
#     points = ((GLfloat * 2) * len(points))(*points)
#     glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
#     glEnableClientState(GL_VERTEX_ARRAY)
#     glVertexPointer(2, GL_FLOAT, 0, points)
#     glDrawArrays(GL_TRIANGLE_FAN, 0, len(points))
#     glPopClientAttrib()


# def circle(r, x, y, slices=20):
#     d = 2 * math.pi / slices
#     points = [(x + r * math.cos(a*d), y + r * math.sin(a*d)) for a in range(slices)]
#     points = ((GLfloat * 2) * len(points))(*points)
#     glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
#     glEnableClientState(GL_VERTEX_ARRAY)
#     glVertexPointer(2, GL_FLOAT, 0, points)
#     glDrawArrays(GL_LINE_LOOP, 0, len(points))
#     glPopClientAttrib()


def orientation_angle(orientation):
    return math.atan2(orientation[2], orientation[0])


class Handle:
    tip = ''

    def __init__(self, window, player):
        self.win = window
        self.player = player

    def hit_test(self, x, y, z):
        dx, dy, dz = [a - b for a, b in zip(self.pos(), (x, y, z))]
        if dx * dx + dy * dy + dz * dz < self.radius * self.radius:
            return -dx, -dy, -dz

    def pos(self):
        raise NotImplementedError()

    def delete(self):
        pass

    def update_shapes(self):
        pass

    def begin_drag(self, offset):
        self.offset = offset
        return self

    def on_mouse_press(self, x, y, button, modifiers):
        self.win.remove_handlers(self)

    def on_mouse_release(self, x, y, button, modifiers):
        self.win.remove_handlers(self)


class LabelHandle(Handle):
    def __init__(self, window, player):
        super().__init__(window, player)
        self.text = pyglet.text.Label('', font_size=10, color=(0, 0, 0, 255),
                                      anchor_y='top', anchor_x='center', batch=window.text_batch)

    def delete(self):
        self.text.delete()

    def hit_test(self, x, y, z):
        return None

    # def draw(self):
    #     if hasattr(self.player, 'label'):
    #         x, _, y = self.player.position

    #         # ech. fudge scale back to 1
    #         mat = (GLfloat * 16)()
    #         glGetFloatv(GL_MODELVIEW_MATRIX, mat)

    #         glPushMatrix()
    #         glTranslatef(x, y, 0)
    #         glScalef(1/mat[0], 1/mat[5], 1/mat[10])
    #         glTranslatef(0, -5, 0)

    #         self.text.text = self.player.label
    #         self.text.draw()

    #         glPopMatrix()



class PositionHandle(Handle):
    tip = 'position'
    radius = .3

    def __init__(self, window, player):
        super().__init__(window, player)
        self._triangle = pyglet.shapes.Triangle(
            0, self.radius,
            -self.radius * math.sqrt(3.0) / 2.0, -self.radius / 2.0,
            self.radius * math.sqrt(3.0) / 2.0, -self.radius / 2.0,
            (255, 0, 0, 255),
            window.handle_batch)

    def update_shapes(self):
        self._triangle.position = self.player.position[0], self.player.position[2]

    def delete(self):
        self._triangle.delete()

    # def draw(self):
    #     glPushMatrix()
    #     glTranslatef(self.player.position[0], self.player.position[2], 0)
    #     glColor3f(1, 0, 0)
    #     glBegin(GL_TRIANGLES)
    #     glVertex2f(0, self.radius)
    #     glVertex2f(-self.radius * math.sqrt(3) / 2, -.5 * self.radius)
    #     glVertex2f(self.radius * math.sqrt(3) / 2, -.5 * self.radius)
    #     glEnd()
    #     glPopMatrix()

    def pos(self):
        return self.player.position

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        pos = self.win.mouse_transform(x, y)
        self.player.position = \
            (pos[0] - self.offset[0],
             pos[1] - self.offset[1],
             pos[2] - self.offset[2])


class OrientationHandle(Handle):
    radius = .1
    length = 1.5

    def __init__(self, window, player):
        super().__init__(window, player)
        self._line = pyglet.shapes.Line(0, 0, 0, 0, color=(74, 74, 74), batch=window.handle_batch)

    def pos(self):
        x, _, z = self.player.position
        direction = self.get_orientation()
        sz = math.sqrt(direction[0] ** 2 + direction[1] ** 2 + direction[2] ** 2) or 1
        if sz != 0:
            x += direction[0] / sz * self.length
            z += direction[2] / sz * self.length
        return x, 0, z

    def update_shapes(self):
        px, _, py = self.player.position
        x, _, y = self.pos()

        self._line._x = px
        self._line._y = py
        self._line._x2 = x
        self._line._y2 = y
        self._line._update_vertices()

    def delete(self):
        self._line.delete()

    # def draw(self):
    #     glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT)

    #     px, _, py = self.player.position
    #     x, _, y = self.pos()

    #     # Dashed line
    #     glColor3f(.3, .3, .3)
    #     glEnable(GL_LINE_STIPPLE)
    #     glLineStipple(1, 0x7777)
    #     glBegin(GL_LINES)
    #     glVertex2f(px, py)
    #     glVertex2f(x, y)
    #     glEnd()

    #     # This handle (orientation)
    #     glColor3f(1, 1, 0)
    #     disc(self.radius, x, y)

    #     glPopAttrib()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        px, py, pz = self.player.position
        hx, hy, hz = self.win.mouse_transform(x, y)
        self.set_orientation(
            (hx - self.offset[0] - px,
             hy - self.offset[1] - py,
             hz - self.offset[2] - pz))


class ConeOrientationHandle(OrientationHandle):
    tip = 'cone_orientation'

    def get_orientation(self):
        return self.player.cone_orientation

    def set_orientation(self, orientation):
        self.player.cone_orientation = orientation


class ForwardOrientationHandle(OrientationHandle):
    tip = 'forward_orientation'

    def get_orientation(self):
        return self.player.forward_orientation

    def set_orientation(self, orientation):
        self.player.forward_orientation = orientation


class ConeAngleHandle(Handle):
    length = .1
    radius = .1

    def __init__(self, window, player):
        super().__init__(window, player)
        self._sector = pyglet.shapes.Sector(0, 0, radius=self.length, color=self.fill_color, batch=window.handle_batch)
        self._handle = pyglet.shapes.Circle(0, 0, radius=self.radius, color=self.color, batch=window.handle_batch)

    def pos(self):
        px, py, pz = self.player.position
        angle = orientation_angle(self.player.cone_orientation)
        angle += self.get_angle() * math.pi / 180. / 2
        x = math.cos(angle) * self.length
        z = math.sin(angle) * self.length
        return px + x, py, pz + z

    def get_angle(self):
        raise NotImplementedError()

    def update_shapes(self):
        px, _, py = self.player.position
        angle = orientation_angle(self.player.cone_orientation)
        a = self.get_angle() * math.pi / 180.0

        self._sector.start_angle = a / 2.0
        self._sector.position = px, py

        x, _, y = self.pos()
        self._handle.radius = self.radius
        self._handle.position = x, y

    def delete(self):
        self._sector.delete()
        self._handle.delete()

    # def draw(self):
    #     glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT)

    #     # Fill
    #     glEnable(GL_BLEND)
    #     glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    #     glColor4f(*self.fill_color)
    #     px, _, py = self.player.position
    #     angle = orientation_angle(self.player.cone_orientation)
    #     a = self.get_angle() * math.pi / 180.
    #     disc(self.length, px, py,
    #          start=angle - a/2,
    #          end=angle + a/2)

    #     # Handle
    #     x, _, y = self.pos()
    #     glColor4f(*self.color)
    #     disc(self.radius, x, y)
    #     glPopAttrib()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        px, py, pz = self.player.position
        hx, hy, hz = self.win.mouse_transform(x, y)
        angle = orientation_angle(self.player.cone_orientation)
        hangle = orientation_angle((hx - px, hy - py, hz - pz))
        if hangle < angle:
            hangle += math.pi * 2
        res = min(max((hangle - angle) * 2, 0), math.pi * 2)
        self.set_angle(res * 180. / math.pi)


class ConeInnerAngleHandle(ConeAngleHandle):
    tip = 'cone_inner_angle'
    length = 1.
    color = (51, 204, 51, 255)
    fill_color = (0, 255, 0, 26)

    def get_angle(self):
        return self.player.cone_inner_angle

    def set_angle(self, angle):
        self.player.cone_inner_angle = angle


class ConeOuterAngleHandle(ConeAngleHandle):
    tip = 'cone_outer_angle'
    length = 1.2
    color = (51, 51, 204, 255)
    fill_color = (0, 0, 255, 26)

    def get_angle(self):
        return self.player.cone_outer_angle

    def set_angle(self, angle):
        self.player.cone_outer_angle = angle


class _WireframeGroup(pyglet.graphics.Group):
    def set_state(self):
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    def unset_state(self):
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)


class MoreHandle(Handle):
    tip = 'More...'
    radius = .2

    open = False
    open_width = 1.5
    open_height = 1.5

    def __init__(self, window, player):
        super().__init__(window, player)
        _gb0 = pyglet.graphics.Group(0)
        _gb1 = _WireframeGroup(1)
        self._box0 = pyglet.shapes.Rectangle(0, 0, self.open_width, self.open_height, color=(255, 255, 255, 204), group=_gb0, batch=window.handle_batch)
        self._box1 = pyglet.shapes.Rectangle(0, 0, self.open_width, self.open_height, color=(0, 0, 0, 255), group=_gb1, batch=window.handle_batch)
        self._circ0 = pyglet.shapes.Circle(0, 0, radius=self.radius, batch=window.handle_batch)
        self._circ1 = pyglet.shapes.Circle(0, 0, radius=self.radius, color=(0, 0, 0, 255), batch=window.handle_batch)
        self._line0 = pyglet.shapes.Line(0, 0, 0, 0, color=(0, 0, 0, 255), batch=window.handle_batch)
        self._line1 = pyglet.shapes.Line(0, 0, 0, 0, color=(0, 0, 0, 255), batch=window.handle_batch)

    def pos(self):
        x, y, z = self.player.position
        return x + 1, y, z + 1

    def get_angle(self):
        raise NotImplementedError()

    def update_shapes(self):
        self._box0.visible = self.open
        self._box1.visible = self.open
        self._circ0.visible = not self.open
        self._circ1.visible = not self.open
        self._line0.visible = not self.open
        self._line1.visible = not self.open

        x, _, z = self.pos()
        if self.open:
            x -= 0.2
            z += 0.2
            self._box0.position = x, z
            self._box1.position = x, z
        else:
            self._circ0.position = x, z
            self._circ1.position = x, z
            r = self.radius - 0.1
            self._line0._x = x - r
            self._line0._y = z
            self._line0._x2 = x + r
            self._line0._x2 = r
            self._line0._update_vertices()
            self._line1._x = x
            self._line1._y = z - r
            self._line1._x2 = x
            self._line1._x2 = z + r
            self._line1._update_vertices()

    def delete(self):
        self._box0.delete()
        self._box1.delete()
        self._circ0.delete()
        self._circ1.delete()
        self._line.delete()

    # def draw(self):
    #     x, _, z = self.pos()

    #     if self.open:
    #         x -= .2
    #         z += .2
    #         glPushAttrib(GL_ENABLE_BIT)
    #         glEnable(GL_BLEND)

    #         glColor4f(1, 1, 1, .8)
    #         glBegin(GL_QUADS)
    #         glVertex2f(x, z)
    #         glVertex2f(x + self.open_width, z)
    #         glVertex2f(x + self.open_width, z - self.open_height)
    #         glVertex2f(x, z - self.open_height)
    #         glEnd()

    #         glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    #         glColor4f(0, 0, 0, 1)
    #         glBegin(GL_QUADS)
    #         glVertex2f(x, z)
    #         glVertex2f(x + self.open_width, z)
    #         glVertex2f(x + self.open_width, z - self.open_height)
    #         glVertex2f(x, z - self.open_height)
    #         glEnd()
    #         glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    #         glPopAttrib()
    #     else:
    #         glColor3f(1, 1, 1)
    #         disc(self.radius, x, z)

    #         glColor3f(0, 0, 0)
    #         circle(self.radius, x, z)

    #         r = self.radius - 0.1
    #         glBegin(GL_LINES)
    #         glVertex2f(x - r, z)
    #         glVertex2f(x + r, z)
    #         glVertex2f(x, z - r)
    #         glVertex2f(x, z + r)
    #         glEnd()

    def begin_drag(self, offset):
        self.open = True
        self.win.set_more_player_handles(self.player)
        return self

    def on_mouse_press(self, x, y, button, modifiers):
        x, y, z = self.win.mouse_transform(x, y)
        for handle in self.win.more_handles:
            if handle.hit_test(x, y, z):
                return
        self.win.set_more_player_handles(None)
        self.win.remove_handlers(self)
        self.open = False

    def on_mouse_release(self, x, y, button, modifiers):
        pass


class SliderHandle(Handle):
    length = 1.
    width = .05
    radius = .1

    def __init__(self, window, player, x, z):
        super().__init__(window, player)
        self._groove = pyglet.shapes.Rectangle(0, 0, 20, 20, batch=window.handle_batch)
        self._thumb = pyglet.shapes.Circle(0, 0, radius=self.radius, color=(51, 51, 51, 255), batch=window.handle_batch)
        self.x = x
        self.z = z

    def pos(self):
        x, y, z = self.player.position
        x += self.x + self.get_value() * self.length
        z += self.z
        return x, y, z

    def update_shapes(self):
        x = self.x + self.player.position[0]
        z = self.z + self.player.position[2]
        self._groove.position = x, z
        self._thumb.position = x, z

    def delete(self):
        self._groove.delete()
        self._thumb.delete()

    # def draw(self):
    #     x = self.x + self.player.position[0]
    #     z = self.z + self.player.position[2]

    #     # Groove
    #     glColor3f(.5, .5, .5)
    #     glBegin(GL_QUADS)
    #     glVertex2f(x, z - self.width/2)
    #     glVertex2f(x + self.length, z - self.width/2)
    #     glVertex2f(x + self.length, z + self.width/2)
    #     glVertex2f(x, z + self.width/2)
    #     glEnd()

    #     # Thumb
    #     x, _, z = self.pos()
    #     glColor3f(.2, .2, .2)
    #     disc(self.radius, x, z)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        px, py, pz = self.player.position
        hx, hy, hz = self.win.mouse_transform(x, y)
        value = float(hx - px - self.x) / self.length
        value = min(max(value, 0), 1)
        self.set_value(value)


class VolumeHandle(SliderHandle):
    tip = 'volume'

    def __init__(self, window, player):
        super().__init__(window, player, 1, .9)

    def get_value(self):
        return self.player.volume

    def set_value(self, value):
        self.player.volume = value


class ListenerVolumeHandle(SliderHandle):
    tip = 'volume'

    def __init__(self, window, player):
        super().__init__(window, player, -.5, -1)

    def get_value(self):
        return self.player.volume

    def set_value(self, value):
        self.player.volume = value


class MinDistanceHandle(SliderHandle):
    tip = 'min_distance'

    def __init__(self, window, player):
        super().__init__(window, player, 1, .6)

    def get_value(self):
        return self.player.min_distance / 5.

    def set_value(self, value):
        self.player.min_distance = value * 5.


class MaxDistanceHandle(SliderHandle):
    tip = 'max_distance'

    def __init__(self, window, player):
        super().__init__(window, player, 1, .3)

    def get_value(self):
        return min(self.player.max_distance / 5., 1.0)

    def set_value(self, value):
        self.player.max_distance = value * 5.


class ConeOuterGainHandle(SliderHandle):
    tip = 'cone_outer_gain'

    def __init__(self, window, player):
        super().__init__(window, player, 1, 0)

    def get_value(self):
        return self.player.cone_outer_gain

    def set_value(self, value):
        self.player.cone_outer_gain = value


class SoundSpaceWindow(pyglet.window.Window):
    def __init__(self, **kwargs):
        kwargs.setdefault("caption", "Sound Space")
        kwargs.setdefault("resizable", True)
        super().__init__(**kwargs)

        # pixels per unit
        self.zoom = 40
        self.tx = self.width/2
        self.ty = self.height/2

        self._grid_batch = pyglet.graphics.Batch()
        self._grid = []
        self._refresh_grid()

        self.handle_batch = pyglet.graphics.Batch()
        self.text_batch = pyglet.graphics.Batch()

        self.players = []
        self.handles = []
        self.more_handles = []

        listener = pyglet.media.get_audio_driver().get_listener()
        self.handles.append(PositionHandle(self, listener))
        self.handles.append(ForwardOrientationHandle(self, listener))
        self.handles.append(ListenerVolumeHandle(self, listener))
        self.handles.append(LabelHandle(self, listener))

        self.tip = pyglet.text.Label('', font_size=10, color=(0, 0, 0, 255),
                                     anchor_y='top', anchor_x='center')
        self.tip_player = None

    def add_player(self, player):
        self.players.append(player)
        self.handles.append(PositionHandle(self, player))
        self.handles.append(ConeOrientationHandle(self, player))
        self.handles.append(ConeInnerAngleHandle(self, player))
        self.handles.append(ConeOuterAngleHandle(self, player))
        self.handles.append(LabelHandle(self, player))
        self.handles.append(MoreHandle(self, player))

    def set_more_player_handles(self, player):
        if player:
            self.more_handles = [
                VolumeHandle(self, player),
                MinDistanceHandle(self, player),
                MaxDistanceHandle(self, player),
                ConeOuterGainHandle(self, player),
            ]
        else:
            for h in self.more_handles:
                h.delete()
            self.more_handles = []

    def _refresh_grid(self):
        for line in self._grid:
            line.delete()
        self._grid.clear()

        for x in range(0, self.width, self.zoom):
            self._grid.append(pyglet.shapes.Line(x, 0, x, self.height, batch=self._grid_batch))
        for y in range(0, self.height, self.zoom):
            self._grid.append(pyglet.shapes.Line(0, y, self.width, y, batch=self._grid_batch))

    def mouse_transform(self, x, y):
        return (float(x - self.tx) / self.zoom,
                0,
                float(y - self.ty) / self.zoom)

    def player_transform(self, player):
        return (player.position[0] * self.zoom + self.tx,
                player.position[2] * self.zoom + self.ty)

    def hit_test(self, mouse_x, mouse_y):
        x, y, z = self.mouse_transform(mouse_x, mouse_y)
        for handle in self.more_handles[::-1] + self.handles[::-1]:
            offset = handle.hit_test(x, y, z)
            if offset:
                return handle, offset
        return None, None

    def on_draw(self):
        glClearColor(.8, .8, .8, 1)
        self.clear()

        for handle in self.handles + self.more_handles:
            handle.update_shapes()

        # glLoadIdentity()
        self.view = Mat4()
        # glPushAttrib(GL_CURRENT_BIT)
        # glColor3f(1, 1, 1)
        # glBegin(GL_LINES)
        # for i in range(0, self.width, self.zoom):
        #     glVertex2f(i, 0)
        #     glVertex2f(i, self.height)
        # for i in range(0, self.height, self.zoom):
        #     glVertex2f(0, i)
        #     glVertex2f(self.width, i)
        self._grid_batch.draw()
        # glEnd()
        # glPopAttrib()

        # glPushMatrix()
        # glLoadIdentity()
        # glTranslatef(self.tx, self.ty, 0)
        # glScalef(self.zoom, self.zoom, 1)
        self.view = Mat4().translate(Vec3(self.tx, self.ty, 0)).scale(Vec3(self.zoom, self.zoom, 0))
        # glPopMatrix()
        self.handle_batch.draw()

        self.view = Mat4()
        self.text_batch.draw()

        if self.tip_player:
            player_pos = self.player_transform(self.tip_player)
            self.tip.x = player_pos[0]
            self.tip.y = player_pos[1] - 15
            self.tip.draw()

    def on_mouse_scroll(self, x, y, dx, dy):
        self.zoom += dy * 10
        self.zoom = min(max(self.zoom, 10), 100)
        self._refresh_grid()

    def on_mouse_press(self, x, y, button, modifiers):
        handle, offset = self.hit_test(x, y)
        if handle:
            self.push_handlers(handle.begin_drag(offset))
        else:
            self.push_handlers(PanView(self))

    def on_mouse_motion(self, x, y, dx, dy):
        handle, offset = self.hit_test(x, y)
        if handle:
            self.tip.text = handle.tip
            pos = self.player_transform(handle.player)
            self.tip_player = handle.player
        else:
            self.tip.text = ''


class PanView:
    def __init__(self, window):
        self.win = window

    def on_mouse_release(self, x, y, button, modifiers):
        self.win.remove_handlers(self)

    def on_mouse_press(self, x, y, button, modifiers):
        self.win.remove_handlers(self)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.win.tx += dx
        self.win.ty += dy


if __name__ == '__main__':
    # We swap Y and Z, moving to left-handed system
    listener = pyglet.media.get_audio_driver().get_listener()
    listener.up_orientation = (0, -1, 0)

    # Start facing up (er, forwards)
    listener.forward_orientation = (0, 0, 1)

    listener.label = 'Listener'

    w = SoundSpaceWindow()
    r = reader.SpaceReader(w)
    r.read(pyglet.resource.file('space.txt'))
    player_group = pyglet.media.PlayerGroup(w.players)
    player_group.play()

    pyglet.app.run()
