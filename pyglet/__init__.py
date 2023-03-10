"""pyglet is a cross-platform games and multimedia package.

More information is available at http://www.pyglet.org
"""

import os
import sys

from typing import TYPE_CHECKING

#: The release version
version = '2.0.5'
__version__ = version

MIN_PYTHON_VERSION = 3, 8
MIN_PYTHON_VERSION_STR = '.'.join([str(v) for v in MIN_PYTHON_VERSION])

if sys.version_info < MIN_PYTHON_VERSION:
    raise Exception(f"pyglet {version} requires Python {MIN_PYTHON_VERSION_STR} or newer.")

if 'sphinx' in sys.modules:
    setattr(sys, 'is_pyglet_doc_run', True)
_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run

# pyglet platform treats *BSD systems as Linux
compat_platform = sys.platform
if "bsd" in compat_platform:
    compat_platform = "linux-compat"

_enable_optimisations = not __debug__
if getattr(sys, 'frozen', None):
    _enable_optimisations = True

#: Global dict of pyglet options.  To change an option from its default, you
#: must import ``pyglet`` before any sub-packages.  For example::
#:
#:      import pyglet
#:      pyglet.options['debug_gl'] = False
#:
#: The default options can be overridden from the OS environment.  The
#: corresponding environment variable for each option key is prefaced by
#: ``PYGLET_``.  For example, in Bash you can set the ``debug_gl`` option with::
#:
#:      PYGLET_DEBUG_GL=True; export PYGLET_DEBUG_GL
#:
#: For options requiring a tuple of values, separate each value with a comma.
#:
#: The non-development options are:
#:
#: audio
#:     A sequence of the names of audio modules to attempt to load, in
#:     order of preference.  Valid driver names are:
#:
#:     * xaudio2, the Windows Xaudio2 audio module (Windows only)
#:     * directsound, the Windows DirectSound audio module (Windows only)
#:     * pulse, the PulseAudio module (Linux only)
#:     * openal, the OpenAL audio module
#:     * silent, no audio
#: debug_lib
#:     If True, prints the path of each dynamic library loaded.
#: debug_gl
#:     If True, all calls to OpenGL functions are checked afterwards for
#:     errors using ``glGetError``.  This will severely impact performance,
#:     but provides useful exceptions at the point of failure.  By default,
#:     this option is enabled if ``__debug__`` is (i.e., if Python was not run
#:     with the -O option).  It is disabled by default when pyglet is "frozen"
#:     within a py2exe or py2app library archive.
#: shadow_window
#:     By default, pyglet creates a hidden window with a GL context when
#:     pyglet.gl is imported.  This allows resources to be loaded before
#:     the application window is created, and permits GL objects to be
#:     shared between windows even after they've been closed.  You can
#:     disable the creation of the shadow window by setting this option to
#:     False.
#:
#:     Some OpenGL driver implementations may not support shared OpenGL
#:     contexts and may require disabling the shadow window (and all resources
#:     must be loaded after the window using them was created).  Recommended
#:     for advanced developers only.
#:
#:     .. versionadded:: 1.1
#: vsync
#:     If set, the `pyglet.window.Window.vsync` property is ignored, and
#:     this option overrides it (to either force vsync on or off).  If unset,
#:     or set to None, the `pyglet.window.Window.vsync` property behaves
#:     as documented.
#: xsync
#:     If set (the default), pyglet will attempt to synchronise the drawing of
#:     double-buffered windows to the border updates of the X11 window
#:     manager.  This improves the appearance of the window during resize
#:     operations.  This option only affects double-buffered windows on
#:     X11 servers supporting the Xsync extension with a window manager
#:     that implements the _NET_WM_SYNC_REQUEST protocol.
#:
#:     .. versionadded:: 1.1
#: search_local_libs
#:     If False, pyglet won't try to search for libraries in the script
#:     directory and its `lib` subdirectory. This is useful to load a local
#:     library instead of the system installed version. This option is set
#:     to True by default.
#:
#:     .. versionadded:: 1.2
#:
options = {
    'audio': ('xaudio2', 'directsound', 'openal', 'pulse', 'silent'),
    'debug_font': False,
    'debug_gl': not _enable_optimisations,
    'debug_gl_trace': False,
    'debug_gl_trace_args': False,
    'debug_gl_shaders': False,
    'debug_graphics_batch': False,
    'debug_lib': False,
    'debug_media': False,
    'debug_texture': False,
    'debug_trace': False,
    'debug_trace_args': False,
    'debug_trace_depth': 1,
    'debug_trace_flush': True,
    'debug_win32': False,
    'debug_input': False,
    'debug_x11': False,
    'shadow_window': True,
    'vsync': None,
    'xsync': True,
    'xlib_fullscreen_override_redirect': False,
    'search_local_libs': True,
    'win32_gdi_font': False,
    'headless': False,
    'headless_device': 0,
    'win32_disable_shaping': False,
    'dw_legacy_naming': False,
    'win32_disable_xinput': False,
    'com_mta': False,
}

_option_types = {
    'audio': tuple,
    'debug_font': bool,
    'debug_gl': bool,
    'debug_gl_trace': bool,
    'debug_gl_trace_args': bool,
    'debug_gl_shaders': bool,
    'debug_graphics_batch': bool,
    'debug_lib': bool,
    'debug_media': bool,
    'debug_texture': bool,
    'debug_trace': bool,
    'debug_trace_args': bool,
    'debug_trace_depth': int,
    'debug_trace_flush': bool,
    'debug_win32': bool,
    'debug_input': bool,
    'debug_x11': bool,
    'shadow_window': bool,
    'vsync': bool,
    'xsync': bool,
    'xlib_fullscreen_override_redirect': bool,
    'search_local_libs': bool,
    'win32_gdi_font': bool,
    'headless': bool,
    'headless_device': int,
    'win32_disable_shaping': bool,
    'dw_legacy_naming': bool,
    'win32_disable_xinput': bool,
    'com_mta': bool
}


for key in options:
    """Read defaults for options from environment"""
    assert key in _option_types, f"Option '{key}' must have a type set in _option_types."
    env = f'PYGLET_{key.upper()}'
    try:
        value = os.environ[env]
        if _option_types[key] is tuple:
            options[key] = value.split(',')
        elif _option_types[key] is bool:
            options[key] = value in ('true', 'TRUE', 'True', '1')
        elif _option_types[key] is int:
            options[key] = int(value)
    except KeyError:
        pass


if compat_platform == 'cygwin':
    # This hack pretends that the posix-like ctypes provides windows
    # functionality.  COM does not work with this hack, so there is no
    # DirectSound support.
    import ctypes

    ctypes.windll = ctypes.cdll
    ctypes.oledll = ctypes.cdll
    ctypes.WINFUNCTYPE = ctypes.CFUNCTYPE
    ctypes.HRESULT = ctypes.c_long

# Call tracing
# ------------

_trace_filename_abbreviations = {}


def _trace_repr(value, size=40):
    value = repr(value)
    if len(value) > size:
        value = value[:size // 2 - 2] + '...' + value[-size // 2 - 1:]
    return value


def _trace_frame(thread, frame, indent):
    from pyglet import lib
    if frame.f_code is lib._TraceFunction.__call__.__code__:
        is_ctypes = True
        func = frame.f_locals['self']._func
        name = func.__name__
        location = '[ctypes]'
    else:
        is_ctypes = False
        code = frame.f_code
        name = code.co_name
        path = code.co_filename
        line = code.co_firstlineno

        try:
            filename = _trace_filename_abbreviations[path]
        except KeyError:
            # Trim path down
            dir = ''
            path, filename = os.path.split(path)
            while len(dir + filename) < 30:
                filename = os.path.join(dir, filename)
                path, dir = os.path.split(path)
                if not dir:
                    filename = os.path.join('', filename)
                    break
            else:
                filename = os.path.join('...', filename)
            _trace_filename_abbreviations[path] = filename

        location = f'({filename}:{line})'

    if indent:
        name = f'Called from {name}'
    print(f'[{thread}] {indent}{name} {location}')

    if _trace_args:
        if is_ctypes:
            args = [_trace_repr(arg) for arg in frame.f_locals['args']]
            print(f'  {indent}args=({", ".join(args)})')
        else:
            for argname in code.co_varnames[:code.co_argcount]:
                try:
                    argvalue = _trace_repr(frame.f_locals[argname])
                    print(f'  {indent}{argname}={argvalue}')
                except:
                    pass

    if _trace_flush:
        sys.stdout.flush()


def _thread_trace_func(thread):
    def _trace_func(frame, event, arg):
        if event == 'call':
            indent = ''
            for i in range(_trace_depth):
                _trace_frame(thread, frame, indent)
                indent += '  '
                frame = frame.f_back
                if not frame:
                    break

        elif event == 'exception':
            (exception, value, traceback) = arg
            print('First chance exception raised:', repr(exception))

    return _trace_func


def _install_trace():
    global _trace_thread_count
    sys.setprofile(_thread_trace_func(_trace_thread_count))
    _trace_thread_count += 1


_trace_thread_count = 0
_trace_args = options['debug_trace_args']
_trace_depth = options['debug_trace_depth']
_trace_flush = options['debug_trace_flush']
if options['debug_trace']:
    _install_trace()


# Lazy loading
# ------------

class _ModuleProxy:
    _module = None

    def __init__(self, name):
        self.__dict__['_module_name'] = name

    def __getattr__(self, name):
        try:
            return getattr(self._module, name)
        except AttributeError:
            if self._module is not None:
                raise

            import_name = f'pyglet.{self._module_name}'
            __import__(import_name)
            module = sys.modules[import_name]
            object.__setattr__(self, '_module', module)
            globals()[self._module_name] = module
            return getattr(module, name)

    def __setattr__(self, name, value):
        try:
            setattr(self._module, name, value)
        except AttributeError:
            if self._module is not None:
                raise

            import_name = f'pyglet.{self._module_name}'
            __import__(import_name)
            module = sys.modules[import_name]
            object.__setattr__(self, '_module', module)
            globals()[self._module_name] = module
            setattr(module, name, value)


# Lazily load all modules, except if performing
# type checking or code inspection.
if TYPE_CHECKING:
    from . import app
    from . import canvas
    from . import clock
    from . import event
    from . import font
    from . import gl
    from . import graphics
    from . import gui
    from . import input
    from . import image
    from . import lib
    from . import math
    from . import media
    from . import model
    from . import resource
    from . import sprite
    from . import shapes
    from . import text
    from . import window
else:
    app = _ModuleProxy('app')
    canvas = _ModuleProxy('canvas')
    clock = _ModuleProxy('clock')
    event = _ModuleProxy('event')
    font = _ModuleProxy('font')
    gl = _ModuleProxy('gl')
    graphics = _ModuleProxy('graphics')
    gui = _ModuleProxy('gui')
    image = _ModuleProxy('image')
    input = _ModuleProxy('input')
    lib = _ModuleProxy('lib')
    math = _ModuleProxy('math')
    media = _ModuleProxy('media')
    model = _ModuleProxy('model')
    resource = _ModuleProxy('resource')
    sprite = _ModuleProxy('sprite')
    shapes = _ModuleProxy('shapes')
    text = _ModuleProxy('text')
    window = _ModuleProxy('window')
