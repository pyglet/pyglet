#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from ctypes import *

from pyglet.window.xlib.constants import *

# from X.h
VisualID = XID = Atom = Time = c_ulong
WindowRef = XID     # Avoid name collision with pyglet.window.Window
Pixmap = XID
Cursor = XID
Bool = c_int
Colormap = c_uint32

# From Xlib.h

class Display(Structure):
    _fields_ = [
        ('dummy', c_int)        # Don't care about real contents.
    ]

class Screen(Structure):
    _fields_ = [
        ('ext_data', c_void_p),
        ('display', POINTER(Display)),
        ('root', WindowRef),
        ('width', c_int),
        ('height', c_int)
        # ... there is more, but we don't need it.
    ]

class XColor(Structure):
    _fields_ = [
        ('pixel', c_ulong),
        ('red', c_ushort),
        ('green', c_ushort),
        ('blue', c_ushort),
        ('flags', c_char),
        ('pad', c_char),
    ]

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

class XWindowAttributes(Structure):
    _fields_ = [
        ('x', c_int),
        ('y', c_int),
        ('width', c_int),
        ('height', c_int),
        ('border_width', c_int),
        ('depth', c_int),
        ('visual', c_void_p),
        ('root', WindowRef),
        ('c_class', c_int),
        ('bit_gravity', c_int),
        ('win_gravity', c_int),
        ('backing_store', c_int),
        ('backing_planes', c_ulong),
        ('backing_pixel', c_ulong),
        ('save_under', Bool),
        ('colormap', Colormap),
        ('map_installed', Bool),
        ('all_event_masks', c_long),
        ('your_event_mask', c_long),
        ('do_not_propogate_mask', c_long),
        ('override_redirect', Bool),
        ('screen', POINTER(Screen))
    ]


# Events (TODO incomplete -- see marker below)

class XAnyEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
    ]

class XKeyEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
        ('root', WindowRef),
        ('subwindow', WindowRef),
        ('time', Time),
        ('x', c_int),
        ('y', c_int),
        ('x_root', c_int),
        ('y_root', c_int),
        ('state', c_uint),
        ('keycode', c_uint),
        ('same_screen', Bool)
    ]

class XButtonEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
        ('root', WindowRef),
        ('subwindow', WindowRef),
        ('time', Time),
        ('x', c_int),
        ('y', c_int),
        ('x_root', c_int),
        ('y_root', c_int),
        ('state', c_uint),
        ('button', c_uint),
        ('same_screen', Bool)
    ]

class XMotionEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
        ('root', WindowRef),
        ('subwindow', WindowRef),
        ('time', Time),
        ('x', c_int),
        ('y', c_int),
        ('x_root', c_int),
        ('y_root', c_int),
        ('state', c_uint),
        ('is_hint', c_char),
        ('same_screen', Bool)
    ]

class XDestroyWindowEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
    ]

class XClientMessageEvent_data(Union):
    _fields_ = [
		('b', c_char * 20),
		('s', c_short * 10),
		('l', c_long * 5),
    ]

class XClientMessageEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
	    ('message_type', Atom),
	    ('format', c_int),
	    ('data', XClientMessageEvent_data),
    ]

class XExposeEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
        ('x', c_int),
        ('y', c_int),
        ('width', c_int),
        ('height', c_int),
        ('count', c_int),
    ]

class XCrossingEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
        ('root', WindowRef),
        ('subwindow', WindowRef),
        ('time', Time),
        ('x', c_int),
        ('y', c_int),
        ('x_root', c_int),
        ('y_root', c_int),
        ('mode', c_int),
        ('detail', c_int),
        ('same_screen', Bool),
        ('focus', Bool),
        ('state', c_uint),
    ]

class XConfigureEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('event', WindowRef),
        ('window', WindowRef),
        ('x', c_int),
        ('y', c_int),
        ('width', c_int),
        ('height', c_int),
        ('border_width', c_int),
        ('window_above', WindowRef),
        ('override_redirect', Bool),
    ]

# TODO remainder incomplete

class XFocusChangeEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
    ]

class XGraphicsExposeEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
    ]

class XNoExposeEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
    ]

class XVisibilityEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
        ('state', c_int)
    ]

class XCreateWindowEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
    ]

class XUnmapEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
    ]

class XMapEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
    ]

class XMapRequestEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
    ]

class XReparentEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
    ]

class XGravityEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
    ]

class XResizeRequestEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
    ]

class XConfigureRequestEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
    ]

class XCirculateEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
    ]

class XCirculateRequestEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
    ]

class XPropertyEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
    ]

class XSelectionClearEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
    ]

class XSelectionRequestEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
    ]

class XSelectionEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
    ]

class XColormapEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
    ]

class XMappingEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
    ]

class XErrorEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
    ]

class XKeymapEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', Bool),
        ('display', POINTER(Display)),
        ('window', WindowRef),
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

# XXX This is workaround for c_void_p
class OpaqueStruct(Structure):
    _fields_ = [
        ('_', c_int)
    ]

    @classmethod
    def __new__(cls):
        raise Error('OpaqueStruct cannot be dereferenced.')

class Visual(Structure):
    _fields_ = [
        ('ext_data', POINTER(OpaqueStruct)),
        ('visualid', VisualID),
        ('c_class', c_int),
        ('red_mask', c_ulong),
        ('green_mask', c_ulong),
        ('blue_mask', c_ulong),
        ('bits_per_rgb', c_int),
        ('map_entries', c_int),
    ]

class XVisualInfo(Structure):
    _fields_ = [
        ('visual', POINTER(Visual)),
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

class _SizeHintsPoint(Structure):
    _fields_ = [
        ('x', c_int),
        ('y', c_int)
    ]

class XSizeHints(Structure):
    _fields_ = [
        ('flags', c_long),
        ('x', c_int),
        ('y', c_int),
        ('width', c_int),
        ('height', c_int),
        ('min_width', c_int),
        ('min_height', c_int),
        ('max_width', c_int),
        ('max_height', c_int),
        ('width_inc', c_int),
        ('height_inc', c_int),
        ('min_aspect', _SizeHintsPoint),
        ('max_aspect', _SizeHintsPoint),
        ('base_width', c_int),
        ('base_height', c_int),
        ('win_gravity', c_int)
    ]

# Xinerama

class XineramaScreenInfo(Structure):
    _fields_ = [
        ('screen_number', c_int),
        ('x_org', c_short),
        ('y_org', c_short),
        ('width', c_short),
        ('height', c_short)
    ]

# Motif window manager hints

class mwmhints_t(Structure):
    _fields_ = [
        ('flags', c_uint32),
        ('functions', c_uint32),
        ('decorations', c_uint32),
        ('input_mode', c_int32),
        ('status', c_uint32)
    ]

