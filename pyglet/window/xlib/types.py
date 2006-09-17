#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from ctypes import *

from pyglet.window.xlib.constants import *

# from X.h
#  XID = c_ulong
#  ... and a whole lot of things are XIDs
#  Time is c_ulong

# Window attrs from Xlib.h


class XSetWindowAttributes(Structure):
    _fields_ = [
    ('background_pixmap', c_ulong),
    ('background_pixel', c_ulong),
    ('border_pixmap', c_ulong),
    ('border_pixel', c_ulong),
    ('bit_gravity', c_int),
    ('win_gravity', c_int),
    ('backing_store', c_int),
    ('backing_planes', c_ulong),
    ('backing_pixel', c_ulong),
    ('save_under', c_int),
    ('event_mask', c_long),
    ('do_not_propagate_mask', c_long),
    ('override_redirect', c_int),
    ('colormap', c_ulong),
    ('cursor', c_ulong),
    ]

# Events (TODO incomplete -- see marker below)

class XAnyEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

# TODO all the type-based TODOs below apply to all events
class XKeyEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_ulong),
        ('root', c_ulong),
        ('subwindow', c_ulong),
        ('time', c_ulong),
        ('x', c_int),
        ('y', c_int),
        ('x_root', c_int),
        ('y_root', c_int),
        ('state', c_uint),
        ('keycode', c_uint),
        ('same_screen', c_int)
    ]

class XButtonEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int),
        ('root', c_ulong),
        ('subwindow', c_ulong),
        ('time', c_ulong),
        ('x', c_int),
        ('y', c_int),
        ('x_root', c_int),
        ('y_root', c_int),
        ('state', c_uint),
        ('button', c_uint),
        ('same_screen', c_int)
    ]

class XMotionEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int),
        ('root', c_ulong),
        ('subwindow', c_ulong),
        ('time', c_ulong),
        ('x', c_int),
        ('y', c_int),
        ('x_root', c_int),
        ('y_root', c_int),
        ('state', c_uint),
        ('is_hint', c_char),
        ('same_screen', c_int)
    ]

# TODO remainder incomplete

class XCrossingEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

class XFocusChangeEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

class XExposeEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

class XGraphicsExposeEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

class XNoExposeEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

class XVisibilityEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

class XCreateWindowEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

class XDestroyWindowEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

class XUnmapEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

class XMapEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

class XMapRequestEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

class XReparentEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

class XConfigureEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

class XGravityEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

class XResizeRequestEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

class XConfigureRequestEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

class XCirculateEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

class XCirculateRequestEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

class XPropertyEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

class XSelectionClearEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

class XSelectionRequestEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

class XSelectionEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

class XColormapEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

class XClientMessageEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

class XMappingEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

class XErrorEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

class XKeymapEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', c_void_p),
        ('window', c_int)
    ]

class XEvent(Union):
    _fields_ = [
        ('type', c_int),
        ('xkey', XKeyEvent),
        ('xbutton', XButtonEvent),
        ('xmotion', XMotionEvent),
        ('xcrossing', XCrossingEvent),
        ('xfocus', XFocusChangeEvent),
        ('xexpose', XExposeEvent),
        ('xgraphicsexpose', XGraphicsExposeEvent),
        ('xnoexpose', XNoExposeEvent),
        ('xvisibility', XVisibilityEvent),
        ('xcreatewindow', XCreateWindowEvent),
        ('xdestroywindow', XDestroyWindowEvent),
        ('xunmap', XUnmapEvent),
        ('xmap', XMapEvent),
        ('xmaprequest', XMapRequestEvent),
        ('xreparent', XReparentEvent),
        ('xconfigure', XConfigureEvent),
        ('xgravity', XGravityEvent),
        ('xresizerequest', XResizeRequestEvent),
        ('xconfigurerequest', XConfigureRequestEvent),
        ('xcirculate', XCirculateEvent),
        ('xcirculaterequest', XCirculateRequestEvent),
        ('xproperty', XPropertyEvent),
        ('xselectionclear', XSelectionClearEvent),
        ('xselectionrequest', XSelectionRequestEvent),
        ('xselection', XSelectionEvent),
        ('xcolormap', XColormapEvent),
        ('xclient', XClientMessageEvent),
        ('xmapping', XMappingEvent),
        ('xerror', XErrorEvent),
        ('xkeymap', XKeymapEvent),
        ('xany', XAnyEvent),
        ('pad', c_long * 24)
    ]

    _event_names = {
        KeyPress: 'KeyPress',
        KeyRelease: 'KeyRelease',
        ButtonPress: 'ButtonPress',
        ButtonRelease: 'ButtonRelease',
        MotionNotify: 'MotionNotify',
        EnterNotify: 'EnterNotify',
        LeaveNotify: 'LeaveNotify',
        FocusIn: 'FocusIn',
        FocusOut: 'FocusOut',
        KeymapNotify: 'KeymapNotify',
        Expose: 'Expose',
        GraphicsExpose: 'GraphicsExpose',
        NoExpose: 'NoExpose',
        VisibilityNotify: 'VisibilityNotify',
        CreateNotify: 'CreateNotify',
        DestroyNotify: 'DestroyNotify',
        UnmapNotify: 'UnmapNotify',
        MapNotify: 'MapNotify',
        MapRequest: 'MapRequest',
        ReparentNotify: 'ReparentNotify',
        ConfigureNotify: 'ConfigureNotify',
        ConfigureRequest: 'ConfigureRequest',
        GravityNotify: 'GravityNotify',
        ResizeRequest: 'ResizeRequest',
        CirculateNotify: 'CirculateNotify',
        CirculateRequest: 'CirculateRequest',
        PropertyNotify: 'PropertyNotify',
        SelectionClear: 'SelectionClear',
        SelectionRequest: 'SelectionRequest',
        SelectionNotify: 'SelectionNotify',
        ColormapNotify: 'ColormapNotify',
        ClientMessage: 'ClientMessage',
        MappingNotify: 'MappingNotify',
    }

    def __repr__(self):
        return self._event_names[self.type]

# from Xutil.h

class XTextProperty(Structure):
    _fields_ = [
        ('value', c_char_p),
        ('encoding', c_ulong),
        ('format', c_int),
        ('nitems', c_ulong)
    ]

XStringStyle = 0
XCompundTextStyle = 1
XTextStyle = 2
XStdICCTextStyle = 3
XUTF8StringStyle = 4

class XVisualInfo(Structure):
    _fields_ = [
        ('visual', c_void_p),
        ('visualid', c_ulong),
        ('screen', c_int),
        ('depth', c_int),
        ('c_class', c_int),
        ('red_mask', c_ulong),
        ('green_mask', c_ulong),
        ('blue_mask', c_ulong),
        ('colormap_size', c_int),
        ('bits_per_rgb', c_int),
    ]

