# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2021 pyglet contributors
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
import pyglet

from .ninepatch import NinePatch, NinePatchGroup


class Frame:

    def __init__(self, window, cell_size=64, order=0):
        window.push_handlers(self)
        self._cell_size = cell_size
        self._cells = {}
        self._active_widgets = set()
        self._order = order
        self._mouse_pos = 0, 0

    def _hash(self, x, y):
        """Normalize position to cell"""
        return int(x / self._cell_size), int(y / self._cell_size)

    def add_widget(self, widget):
        """Insert Widget into the appropriate cell"""
        min_vec, max_vec = self._hash(*widget.aabb[0:2]), self._hash(*widget.aabb[2:4])
        for i in range(min_vec[0], max_vec[0] + 1):
            for j in range(min_vec[1], max_vec[1] + 1):
                self._cells.setdefault((i, j), set()).add(widget)
                # TODO: return ID and track Widgets for later deletion.
        widget.update_groups(self._order)

    def on_mouse_press(self, x, y, buttons, modifiers):
        """Pass the event to any widgets within range of the mouse"""
        for widget in self._cells.get(self._hash(x, y), set()):
            widget.dispatch_event('on_mouse_press', x, y, buttons, modifiers)
            self._active_widgets.add(widget)

    def on_mouse_release(self, x, y, buttons, modifiers):
        """Pass the event to any widgets that are currently active"""
        for widget in self._active_widgets:
            widget.dispatch_event('on_mouse_release', x, y, buttons, modifiers)
        self._active_widgets.clear()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        """Pass the event to any widgets that are currently active"""
        for widget in self._active_widgets:
            widget.dispatch_event('on_mouse_drag', x, y, dx, dy, buttons, modifiers)
        self._mouse_pos = x, y

    def on_mouse_scroll(self, x, y, index, direction):
        """Pass the event to any widgets within range of the mouse"""
        for widget in self._cells.get(self._hash(x, y), set()):
            widget.dispatch_event('on_mouse_scroll', x, y, index, direction)

    def on_mouse_motion(self, x, y, dx, dy):
        """Pass the event to any widgets within range of the mouse"""
        for widget in self._active_widgets:
            widget.dispatch_event('on_mouse_motion', x, y, dx, dy)
        for widget in self._cells.get(self._hash(x, y), set()):
            widget.dispatch_event('on_mouse_motion', x, y, dx, dy)
            self._active_widgets.add(widget)
        self._mouse_pos = x, y

    def on_text(self, text):
        for widget in self._cells.get(self._hash(*self._mouse_pos), set()):
            widget.dispatch_event('on_text', text)

    def on_text_motion(self, motion):
        for widget in self._cells.get(self._hash(*self._mouse_pos), set()):
            widget.dispatch_event('on_text_motion', motion)

    def on_text_motion_select(self, motion):
        for widget in self._cells.get(self._hash(*self._mouse_pos), set()):
            widget.dispatch_event('on_text_motion_select', motion)


class NinePatchFrame(Frame):

    def __init__(self, x, y, width, height, window, image, group=None, batch=None, cell_size=128, order=0):
        super().__init__(window, cell_size, order)
        self._npatch = NinePatch(image)
        self._npatch.get_vertices(x, y, width, height)
        self._group = NinePatchGroup(image.get_texture(), order, group)
        self._batch = batch or pyglet.graphics.Batch()

        vertices = self._npatch.get_vertices(x, y, width, height)
        indices = self._npatch.indices
        tex_coords = self._npatch.tex_coords

        self._vlist = self._batch.add_indexed(16, pyglet.gl.GL_QUADS, self._group, indices,
                                              ('v2i', vertices), ('t2f', tex_coords))
