import ctypes

import pyglet

__all__ = ['link_GL', 'link_AGL', 'link_GLX', 'link_WGL',
           'GLException', 'missing_function', 'decorate_function']

_debug_gl = pyglet.options['debug_gl']
_debug_gl_trace = pyglet.options['debug_gl_trace']
_debug_gl_trace_args = pyglet.options['debug_gl_trace_args']


class MissingFunctionException(Exception):
    def __init__(self, name, requires=None, suggestions=None):
        msg = '%s is not exported by the available OpenGL driver.' % name
        if requires:
            msg += '  %s is required for this functionality.' % requires
        if suggestions:
            msg += '  Consider alternative(s) %s.' % ', '.join(suggestions)
        Exception.__init__(self, msg)


def missing_function(name, requires=None, suggestions=None):
    def MissingFunction(*args, **kwargs):
        raise MissingFunctionException(name, requires, suggestions)

    return MissingFunction


_int_types = (ctypes.c_int16, ctypes.c_int32)
if hasattr(ctypes, 'c_int64'):
    # Some builds of ctypes apparently do not have c_int64
    # defined; it's a pretty good bet that these builds do not
    # have 64-bit pointers.
    _int_types += (ctypes.c_int64,)
for t in _int_types:
    if ctypes.sizeof(t) == ctypes.sizeof(ctypes.c_size_t):
        c_ptrdiff_t = t


class c_void(ctypes.Structure):
    # c_void_p is a buggy return type, converting to int, so
    # POINTER(None) == c_void_p is actually written as
    # POINTER(c_void), so it can be treated as a real pointer.
    _fields_ = [('dummy', ctypes.c_int)]


class GLException(Exception):
    pass


def errcheck(result, func, arguments):
    if _debug_gl_trace:
        try:
            name = func.__name__
        except AttributeError:
            name = repr(func)
        if _debug_gl_trace_args:
            trace_args = ', '.join([repr(arg)[:20] for arg in arguments])
            print(f'{name}({trace_args})')
        else:
            print(name)

    from pyglet import gl
    context = gl.current_context
    if not context:
        raise GLException('No GL context; create a Window first')
    error = gl.glGetError()
    if error:
        # These are the 6 possible error codes we can get in opengl core 3.3+
        error_types = {
            gl.GL_INVALID_ENUM: "Invalid enum. An unacceptable value is specified for an enumerated argument.",
            gl.GL_INVALID_VALUE: "Invalid value. A numeric argument is out of range.",
            gl.GL_INVALID_OPERATION: "Invalid operation. The specified operation is not allowed in the current state.",
            gl.GL_INVALID_FRAMEBUFFER_OPERATION: "Invalid framebuffer operation. The framebuffer object is not complete.",
            gl.GL_OUT_OF_MEMORY: "Out of memory. There is not enough memory left to execute the command.",
        }
        msg = error_types.get(error, "Unknown error")
        raise GLException(f'(0x{error}): {msg}')
    return result


def decorate_function(func, name):
    if _debug_gl:
        if name not in ('glGetError',) and name[:3] not in ('glX', 'agl', 'wgl'):
            func.errcheck = errcheck


link_AGL = None
link_GLX = None
link_WGL = None

if pyglet.compat_platform in ('win32', 'cygwin'):
    from pyglet.gl.lib_wgl import link_GL, link_WGL
elif pyglet.compat_platform == 'darwin':
    from pyglet.gl.lib_agl import link_GL, link_AGL
else:
    from pyglet.gl.lib_glx import link_GL, link_GLX
