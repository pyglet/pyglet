'''Clipboard implementation for X11 using xlib.
'''
from ctypes import *

from pyglet import window
from pyglet.window.xlib import xlib

XA_PRIMARY = xlib.Atom(1)
XA_STRING = xlib.Atom(31)
CurrentTime = 0
AnyPropertyType = 0

class XlibClipboard(object):
    def get_text(self):
        display = window.get_platform().get_default_display()._display
        owner = xlib.XGetSelectionOwner(display, XA_PRIMARY)
        if not owner: return ''

        # XXX xa_utf8_string
        xlib.XConvertSelection(display, XA_PRIMARY, XA_STRING, 0, owner,
            CurrentTime)
        xlib.XFlush(display)

        # determine what's in the selection buffer
        type = xlib.Atom()
        format = c_int()
        len = c_ulong()
        bytes_left = c_ulong()
        data = POINTER(c_ubyte)()
        xlib.XGetWindowProperty(display, owner, XA_STRING, 0, 0, 0,
            AnyPropertyType, byref(type), byref(format), byref(len),
            byref(bytes_left), byref(data))

        length = int(bytes_left.value)
        if not length:
            return ''

        # get the contents
        dummy = c_ulong()
        xlib.XGetWindowProperty(display, owner, XA_STRING, 0,
             length, 0, AnyPropertyType, byref(type), byref(format),
             byref(len), byref(dummy), byref(data))
        s = ''.join(chr(c) for c in data[:len.value])
        xlib.XFree(data)
        return s

    def set_text(self, text):
        pass

if __name__ == '__main__':
    cb = XlibClipboard()
    print 'GOT', `cb.get_text()`            # display last text clipped
    s = "[Clipboard text replaced]"
    cb.set_text(s)
    assert s ==  cb.get_text()              # replace it

