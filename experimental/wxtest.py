#!/usr/bin/python
# $Id:$

import wx
import pyglet
from pyglet.gl import *

import sys
assert sys.platform == 'win32'

from pyglet.window.win32 import _user32
from pyglet.gl import wgl


class pygletCanvas(wx.Window, pyglet.event.EventDispatcher):
    def __init__(self, parent, id=-1, config=None, context=None):
        wx.Window.__init__(self, parent, id)
        
        # Create context (same as pyglet.window.Window.__init__)
        if not config:
            platform = pyglet.window.get_platform()
            display = platform.get_default_display()
            screen = display.get_screens()[0]
            for template_config in [
                pyglet.gl.Config(double_buffer=True, depth_size=24),
                pyglet.gl.Config(double_buffer=True, depth_size=16)]:
                try:
                    config = screen.get_best_config(template_config)
                    break
                except pyglet.window.NoSuchConfigException:
                    pass
            if not config:
                raise pyglet.window.NoSuchConfigException(
                    'No standard config is available.')

        if not config.is_complete():
            config = screen.get_best_config(config)

        if not context:
            context = config.create_context(pyglet.gl.current_context)

        # Set up context for this window 
        # (same as pyglet.window.win32.Win32Window._create)
        self._hwnd = self.GetHandle()
        self._dc = _user32.GetDC(self._hwnd)
        context._set_window(self)
        self._context = context
        self._wgl_context = context._context
        self.switch_to()

        self.Bind(wx.EVT_PAINT, self._OnPaint)
        self.Bind(wx.EVT_SIZE, self._OnSize)

    def _OnPaint(self, event):
        # wx handler for EVT_PAINT
        self.dispatch_event('on_draw')
        self.flip()

    def _OnSize(self, event):
        # wx handler for EVT_SIZE
        width, height = self.GetClientSize()
        self.dispatch_event('on_resize', width, height)
         
    def switch_to(self):
        wgl.wglMakeCurrent(self._dc, self._wgl_context)
        self._context.set_current()
        pyglet.gl.gl_info.set_active_context()
        pyglet.gl.glu_info.set_active_context()

    def flip(self):
        wgl.wglSwapLayerBuffers(self._dc, wgl.WGL_SWAP_MAIN_PLANE)

    def on_resize(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)
        glMatrixMode(GL_MODELVIEW)

pygletCanvas.register_event_type('on_draw')
pygletCanvas.register_event_type('on_resize')

class TestCanvas(pygletCanvas):
    label = pyglet.text.Label('Hello, world', font_size=48,
                              valign='center', halign='center')

    def on_draw(self):
        width, height = self.GetClientSize()
        
        glClear(GL_COLOR_BUFFER_BIT)
        self.label.text = 'OpenGL %s' % pyglet.gl.gl_info.get_version()
        self.label.x = width//2
        self.label.y = height//2
        self.label.draw()

class TestFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title, size=(640, 480))
        canvas = TestCanvas(self)

class TestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, 'Test wxPython + pyglet')
        self.SetTopWindow(frame)

        frame.Show(True)
        return True

if __name__ == '__main__':
    TestApp(redirect=False).MainLoop()
