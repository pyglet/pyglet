#!/usr/bin/env python
'''Test that a window can have multisample.

A window will be opened containing two rotating squares.  Initially,
there will be no multisampling (the edges will look "jaggy").  Press:

    * M to toggle multisampling on/off
    * S to increase samples (2, 4, 6, 8, 10, ...)
    * Shift+S to decrease samples

Each time sample_buffers or samples is modified, the window will be recreated.
Watch the console for success and failure messages.  If the multisample
options are not supported, a "Failure" message will be printed and the window
will be left as-is.

Press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: WINDOW_OPEN.py 750 2007-03-17 01:16:12Z Alex.Holkner $'

import unittest

from pyglet.gl import *
from pyglet import window
from pyglet import clock
from pyglet.window import key

class WINDOW_MULTISAMPLE(unittest.TestCase):
    win = None
    width = 640
    height = 480

    soft_multisample = True
    multisample = False
    samples = 2

    def set_window(self):
        oldwindow = self.win
        try:
            if self.multisample:
                print 'Attempting samples=%d...' % self.samples,
                config = Config(sample_buffers=1, 
                                samples=self.samples,
                                double_buffer=True)
            else:
                print 'Disabling multisample...',
                config = Config(double_buffer=True)
            self.win = window.Window(self.width, self.height, 
                                     vsync=True,
                                     config=config)
            self.win.switch_to()
            self.win.push_handlers(self.on_key_press)

            if self.multisample:
                if self.soft_multisample:
                    glEnable(GL_MULTISAMPLE_ARB)
                else:
                    glDisable(GL_MULTISAMPLE_ARB)
            
            if oldwindow:
                oldwindow.close()

            print 'Success.'
        except window.NoSuchConfigException:
            print 'Failed.'

    def on_key_press(self, symbol, modifiers):
        mod = 1
        if modifiers & key.MOD_SHIFT:
            mod = -1

        if symbol == key.M:
            self.multisample = not self.multisample
            self.set_window()
        if symbol == key.S:
            self.samples += 2 * mod
            self.samples = max(2, self.samples)
            self.set_window()

        # Another test: try enabling/disabling GL_MULTISAMPLE_ARB...
        # seems to have no effect if samples > 4.
        if symbol == key.N:
            self.soft_multisample = not self.soft_multisample
            if self.soft_multisample:
                print 'Enabling GL_MULTISAMPLE_ARB'
                glEnable(GL_MULTISAMPLE_ARB)
            else:
                print 'Disabling GL_MULTISAMPLE_ARB'
                glDisable(GL_MULTISAMPLE_ARB)

    def render(self):
        self.win.switch_to()
        size = self.height / 4
        glClear(GL_COLOR_BUFFER_BIT)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glLoadIdentity()
        glTranslatef(self.width/2, self.height/2, 0)
        glRotatef(self.angle, 0, 0, 1)

        glColor3f(1, 0, 0)
        glBegin(GL_QUADS)
        glVertex2f(-size, -size)
        glVertex2f(size, -size)
        glVertex2f(size, size)
        glVertex2f(-size, size)
        glEnd()

        glRotatef(-self.angle * 2, 0, 0, 1)
        glColor4f(0, 1, 0, 0.5)
        glBegin(GL_QUADS)
        glVertex2f(-size, -size)
        glVertex2f(size, -size)
        glVertex2f(size, size)
        glVertex2f(-size, size)
        glEnd() 

    def test_multisample(self):
        self.set_window()
        self.angle = 0
        clock.set_fps_limit(30)
        while not self.win.has_exit:
            dt = clock.tick()
            self.angle += dt
            
            self.render()
            self.win.flip()
            self.win.dispatch_events()
        self.win.close()

if __name__ == '__main__':
    unittest.main()

