#!/usr/bin/python
# $Id:$

from pyglet.gl import *
from pyglet import window

class MoveWindow(object):
    def __init__(self, window, x, y):
        self.offset = x, y
        self.window = window

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        sx, sy = self.window.get_location()
        ox, oy = self.offset
        self.window.set_location(int(x + sx - ox), int(sy - y + oy))

    def on_mouse_release(self, x, y, button, modifiers):
        self.window.pop_handlers()

class ResizeWindow(object):
    def __init__(self, window, x, y):
        self.offset = window.width - x, y
        self.window = window

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        print x, y
        ox, oy = self.offset
        width = x + ox
        height = self.window.height - y + oy
        self.window.set_size(int(width), int(height))

    def on_mouse_release(self, x, y, button, modifiers):
        self.window.pop_handlers()

class Win(window.Window):
    def __init__(self, *args, **kwargs):
        kwargs.update(dict(
            style=self.WINDOW_STYLE_BORDERLESS))
        super(Win, self).__init__(*args, **kwargs)

    def draw(self):
        w, h = self.width, self.height

        glColor3f(.6, .6, .6)
        glRectf(0, 0, w, h)

        glColor3f(.2, .2, .2)
        glRectf(3, 3, w - 3, h - 3)
        
        glColor3f(.8, .8, .8)
        glRectf(w - 16, 3, w - 3, 16)

    def on_mouse_press(self, x, y, button, modifiers):
        self.activate()
        if y < 16 and self.width - x < 16:
            self.push_handlers(ResizeWindow(self, x, y))
        else:
            self.push_handlers(MoveWindow(self, x, y))
        


if __name__ == '__main__':
    win = Win()
    while not win.has_exit:
        win.dispatch_events()
        win.clear()
        win.draw()
        win.flip()
