"""pyglet is a cross-platform games and multimedia package.

More information is available at http://www.pyglet.org
"""
from __future__ import annotations

import os
import sys
from collections.abc import ItemsView, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from types import FrameType
    from typing import Any, Callable, ItemsView, Sized

#: The release version
version = '2.1.2'
__version__ = version

MIN_PYTHON_VERSION = 3, 8
MIN_PYTHON_VERSION_STR = ".".join([str(v) for v in MIN_PYTHON_VERSION])

if sys.version_info < MIN_PYTHON_VERSION:
    msg = f"pyglet {version} requires Python {MIN_PYTHON_VERSION_STR} or newer."
    raise Exception(msg)

# pyglet platform treats *BSD systems as Linux
compat_platform = sys.platform
if "bsd" in compat_platform:
    compat_platform = "linux-compat"

_enable_optimisations = not __debug__
if getattr(sys, "frozen", None):
    _enable_optimisations = True


_SPECIAL_OPTION_VALIDATORS = {
    "audio": lambda x: isinstance(x, Sequence),
    "vsync": lambda x: x is None or isinstance(x, bool),
}

_OPTION_TYPE_VALIDATORS = {
    "bool": lambda x: isinstance(x, bool),
    "int": lambda x: isinstance(x, int),
}


@dataclass
class Options:
    """Dataclass for global pyglet options."""

    audio: Sequence[str] = ("xaudio2", "directsound", "openal", "pulse", "silent")
    """A :py:class:`~typing.Sequence` of valid audio modules names. They will
     be tried from first to last until either a driver loads or no entries
     remain. See :ref:`guide-audio-driver-order` for more information.

     Valid driver names are:

     * ``'xaudio2'``, the Windows Xaudio2 audio module (Windows only)
     * ``'directsound'``, the Windows DirectSound audio module (Windows only)
     * ``'pulse'``, the :ref:`guide-audio-driver-pulseaudio` module
        (Linux only, otherwise nearly ubiquitous. Limited features; use
        ``'openal'`` for more.)
     * ``'openal'``, the :ref:`guide-audio-driver-openal` audio module
       (A library may need to be installed on Windows and Linux)
     * ``'silent'``, no audio"""

    debug_font: bool = False
    """If ``True``, will print more verbose information when :py:class:`~pyglet.font.base.Font`'s are loaded."""

    debug_gl: bool = True
    """If ``True``, all calls to OpenGL functions are checked afterwards for
     errors using ``glGetError``.  This will severely impact performance,
     but provides useful exceptions at the point of failure.  By default,
     this option is enabled if ``__debug__`` is enabled (i.e., if Python was not run
     with the -O option).  It is disabled by default when pyglet is "frozen", such as
     within pyinstaller or nuitka."""

    debug_gl_trace: bool = False
    """If ``True``, will print the names of OpenGL calls being executed. For example, ``glBlendFunc``"""

    debug_gl_trace_args: bool = False
    """If ``True``, in addition to printing the names of OpenGL calls, it will also print the arguments passed
    into those calls. For example, ``glBlendFunc(770, 771)``

    .. note:: Requires ``debug_gl_trace`` to be enabled."""

    debug_gl_shaders: bool = False
    """If ``True``, prints shader compilation information such as creation and deletion of shader's. Also includes
    information on shader ID's, attributes, and uniforms."""

    debug_graphics_batch: bool = False
    """If ``True``, prints batch information being drawn, including :py:class:`~pyglet.graphics.Group`'s, VertexDomains,
    and :py:class:`~pyglet.image.Texture` information. This can be useful to see how many Group's are being
    consolidated."""

    debug_lib: bool = False
    """If ``True``, prints the path of each dynamic library loaded."""

    debug_media: bool = False
    """If ``True``, prints more detailed media information for audio codecs and drivers. Will be very verbose."""

    debug_texture: bool = False
    """If ``True``, prints information on :py:class:`~pyglet.image.Texture` size (in bytes) when they are allocated and
    deleted."""

    debug_trace: bool = False
    debug_trace_args: bool = False
    debug_trace_depth: int = 1
    debug_trace_flush: bool = True

    debug_win32: bool = False
    """If ``True``, prints error messages related to Windows library calls. Usually get's information from
    ``Kernel32.GetLastError``. This information is output to a file called ``debug_win32.log``."""

    debug_input: bool = False
    """If ``True``, prints information on input devices such as controllers, tablets, and more."""

    debug_x11: bool = False
    """If ``True``, prints information related to Linux X11 calls. This can potentially help narrow down driver or
    operating system issues."""

    shadow_window: bool = True
    """By default, pyglet creates a hidden window with a GL context when
     pyglet.gl is imported.  This allows resources to be loaded before
     the application window is created, and permits GL objects to be
     shared between windows even after they've been closed.  You can
     disable the creation of the shadow window by setting this option to
     False.

     Some OpenGL driver implementations may not support shared OpenGL
     contexts and may require disabling the shadow window (and all resources
     must be loaded after the window using them was created).  Recommended
     for advanced developers only.

     .. versionadded:: 1.1
     """

    vsync: bool | None = None
    """If set, the `pyglet.window.Window.vsync` property is ignored, and
     this option overrides it (to either force vsync on or off).  If unset,
     or set to None, the `pyglet.window.Window.vsync` property behaves
     as documented.
     """

    xsync: bool = True
    """If ``True`` (the default), pyglet will attempt to synchronise the
    drawing of double-buffered windows to the border updates of the X11
    window manager. This improves the appearance of the window during
    resize operations.  This option only affects double-buffered windows on
    X11 servers supporting the Xsync extension with a window manager that
    implements the _NET_WM_SYNC_REQUEST protocol.

     .. versionadded:: 1.1
     """

    xlib_fullscreen_override_redirect: bool = False
    """If ``True``, pass the xlib.CWOverrideRedirect flag when creating a fullscreen window.
    This option is generally not necessary anymore and is considered deprecated.
    """

    search_local_libs: bool = True
    """If ``False``, pyglet won't try to search for libraries in the script
     directory and its ``lib`` subdirectory. This is useful to load a local
     library instead of the system installed version."""

    win32_gdi_font: bool = False
    """If ``True``, pyglet will fallback to the legacy ``GDIPlus`` font renderer for Windows. This may provide
    better font compatibility for older fonts. The legacy renderer does not support shaping, colored fonts,
    substitutions, or other OpenType features. It may also have issues with certain languages.

    Due to those lack of features, it can potentially be more performant.

    .. versionadded:: 2.0
    """

    headless: bool = False
    """If ``True``, visible Windows are not created and a running desktop environment is not required. This option
    is useful when running pyglet on a headless server, or compute cluster. OpenGL drivers with ``EGL`` support are
    required for this mode.
    """

    headless_device: int = 0
    """If using ``headless`` mode (``pyglet.options['headless'] = True``), this option allows you to set which
    GPU to use. This is only useful on multi-GPU systems.
    """

    win32_disable_shaping: bool = False
    """If ``True``, will disable the shaping process for the default Windows font renderer to offer a performance
    speed up. If your font is simple, monospaced, or you require no advanced OpenType features, this option may be
    useful. You can try enabling this to see if there is any impact on clarity for your font. The advance will be
    determined by the glyph width.

    .. note:: Shaping is the process of determining which character glyphs to use and specific placements of those
       glyphs when given a full string of characters.

    .. versionadded:: 2.0
    """

    dw_legacy_naming: bool = False
    """If ``True``, will enable legacy naming support for the default Windows font renderer (``DirectWrite``).
    Attempt to parse fonts by the passed name, to best match legacy RBIZ naming.

    :see: https://learn.microsoft.com/en-us/windows/win32/directwrite/font-selection#rbiz-font-family-model

    For example, this allows specifying ``"Arial Narrow"`` rather than ``"Arial"`` with a ``"condensed"`` stretch or
    ``"Arial Black"`` instead of ``"Arial"`` with a weight of ``black``. This may enhance naming compatibility
    cross-platform for select fonts as older font renderers went by this naming scheme.

    Starts by parsing the string for any known style names, and searches all font collections for a matching RBIZ name.
    If a perfect match is not found, it will choose a second best match.

    .. note:: Due to the high variation of styles and limited capability of some fonts, there is no guarantee the
       second closest match will be exactly what the user wants.

    .. note:: The ``debug_font`` option can provide information on what settings are being selected.

    .. versionadded:: 2.0.3
    """

    win32_disable_xinput: bool = False
    """If ``True``, this will disable the ``XInput`` controller usage in Windows and fallback to ``DirectInput``.  Can
    be useful for debugging or special uses cases. A controller can only be controlled by either ``XInput`` or
    ``DirectInput``, not both.

    .. versionadded:: 2.0
    """

    com_mta: bool = False
    """If ``True``, this will enforce COM Multithreaded Apartment Mode for Windows applications. By default, pyglet
    has opted to go for Single-Threaded Apartment (STA) for compatibility reasons. Many other third party libraries
    used with Python explicitly set STA. However, Windows recommends MTA with a lot of their API's such as Windows
    Media Foundation (WMF).

    :see: https://learn.microsoft.com/en-us/windows/win32/cossdk/com--threading-models

    .. versionadded:: 2.0.5
    """

    osx_alt_loop: bool = False
    """If ``True``, this will enable an alternative loop for Mac OSX. This is enforced for all ARM64 architecture Mac's.

    Due to various issues with the ctypes interface with Objective C, Python, and Mac ARM64 processors, the standard
    event loop eventually starts breaking down to where inputs are either missed or delayed. Even on Intel based Mac's
    other odd behavior can be seen with the standard event loop such as randomly crashing from events.

    .. versionadded:: 2.0.5"""

    dpi_scaling: Literal["real", "scaled", "stretch", "platform"] = "real"
    """For 'HiDPI' displays, Window behavior can differ between operating systems. Defaults to `'real'`.

    The current options are an attempt to create consistent behavior across all of the operating systems.

    `'real'` (default): Provides a 1:1 pixel for Window frame size and framebuffer. Primarily used for game applications
    to ensure you are getting the exact pixels for the resolution. If you provide an 800x600 window, you can ensure it
    will be 800x600 pixels when the user chooses it.

    `'scaled'`: Window size is scaled based on the DPI ratio. Window size and content (projection) size matches the full
    framebuffer. Primarily used for any applications that wish to become DPI aware. You must rescale and reposition your
    content to take advantage of the larger framebuffer. An 800x600 with a 150% DPI scaling would be changed to
    1200x900 for both `window.get_size` and `window.get_framebuffer_size()`.

    Keep in mind that pyglet objects may not be scaled proportionately, so this is left up to the developer.
    The :py:attr:`~pyglet.window.Window.scale` & :py:attr:`~pyglet.window.Window.dpi` attributes can be queried as a
    reference when determining object creation.

    `'stretch'`:  Window is scaled based on the DPI ratio. However, content size matches original requested size of the
    window, and is stretched to fit the full framebuffer. This mimics behavior of having no DPI scaling at all. No
    rescaling and repositioning of content will be necessary, but at the cost of blurry content depending on the extent
    of the stretch. For example, 800x600 at 150% DPI will be 800x600 for `window.get_size()` and 1200x900 for
    `window.get_framebuffer_size()`.
    
    `'platform'`: A DPI aware window is created, however window sizing and framebuffer sizing is not interfered with
    by Pyglet. Final sizes are dictated by the platform the window was created on. It is up to the user to make any
    platform adjustments themselves such as sizing on a platform, mouse coordinate adjustments, or framebuffer size
    handling. On Windows and X11, the framebuffer and the requested window size will always match in pixels 1:1. On
    MacOS, depending on a Hi-DPI display, you may get a different sized framebuffer than the window size. This option
    does allow `window.dpi` and `window.scale` to return their respective values.
    """

    shader_bind_management: bool = True
    """If ``True``, this will enable internal management of Uniform Block bindings for
     :py:class:`~pyglet.graphics.shader.ShaderProgram`'s.

    If ``False``, bindings will not be managed by Pyglet. The user will be responsible for either setting the binding
    points through GLSL layouts (4.2 required) or manually through ``UniformBlock.set_binding``.

    .. versionadded:: 2.0.16
    """

    def get(self, item: str, default: Any = None) -> Any:
        return self.__dict__.get(item, default)

    def items(self) -> ItemsView[str, Any]:
        return self.__dict__.items()

    def __getitem__(self, item: str) -> Any:
        return self.__dict__[item]

    def __setitem__(self, key: str, value: Any) -> None:
        assert key in self.__annotations__, f"Invalid option name: '{key}'"
        assert (_SPECIAL_OPTION_VALIDATORS.get(key) or _OPTION_TYPE_VALIDATORS[self.__annotations__[key]])(value), \
            f"Invalid type: '{type(value)}' for '{key}'"
        self.__dict__[key] = value


#: Instance of :py:class:`~pyglet.Options` used to set runtime options.
options: Options = Options()

_OPTION_TYPE_REMAPS = {
    "audio": "sequence",
    "vsync": "bool",
}

for _key, _type in options.__annotations__.items():
    """Check Environment Variables for pyglet options"""
    if _value := os.environ.get(f"PYGLET_{_key.upper()}"):
        _type = _OPTION_TYPE_REMAPS.get(_key, _type)
        if _type == 'sequence':
            options[_key] = _value.split(",")
        elif _type == 'bool':
            options[_key] = _value in ("true", "TRUE", "True", "1")
        elif _type == 'int':
            options[_key] = int(_value)


if compat_platform == "cygwin":
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

_trace_filename_abbreviations: dict[str, str] = {}
_trace_thread_count = 0
_trace_args = options["debug_trace_args"]
_trace_depth = options["debug_trace_depth"]
_trace_flush = options["debug_trace_flush"]


def _trace_repr(value: Sized, size: int=40) -> str:
    value = repr(value)
    if len(value) > size:
        value = value[:size // 2 - 2] + "..." + value[-size // 2 - 1:]
    return value


def _trace_frame(thread: int, frame: FrameType, indent: str) -> None:
    if frame.f_code is lib._TraceFunction.__call__.__code__: # noqa: SLF001
        is_ctypes = True
        func = frame.f_locals["self"]._func # noqa: SLF001
        name = func.__name__
        location = "[ctypes]"
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
            directory = ""
            path, filename = os.path.split(path)

            while len(directory + filename) < 30:
                filename = os.path.join(directory, filename)
                path, directory = os.path.split(path)
                if not directory:
                    break
            else:
                filename = os.path.join("...", filename)
            _trace_filename_abbreviations[path] = filename

        location = f"({filename}:{line})"

    if indent:
        name = f"Called from {name}"
    print(f"[{thread}] {indent}{name} {location}")

    if _trace_args:
        if is_ctypes:
            args = [_trace_repr(arg) for arg in frame.f_locals["args"]]
            print(f'  {indent}args=({", ".join(args)})')
        else:
            for argname in code.co_varnames[:code.co_argcount]:
                try:
                    argvalue = _trace_repr(frame.f_locals[argname])
                    print(f"  {indent}{argname}={argvalue}")
                except: # noqa: S110, E722, PERF203
                    pass

    if _trace_flush:
        sys.stdout.flush()


def _thread_trace_func(thread: int) -> Callable[[FrameType, str, Any], object]:
    def _trace_func(frame: FrameType, event: str, arg: Any) -> None:
        if event == "call":
            indent = ""
            for _ in range(_trace_depth):
                _trace_frame(thread, frame, indent)
                indent += "  "
                if frame.f_back is None:
                    break
                frame = frame.f_back

        elif event == "exception":
            (exception, value, traceback) = arg
            print("First chance exception raised:", repr(exception))

    return _trace_func


def _install_trace() -> None:
    global _trace_thread_count # noqa: PLW0603
    sys.setprofile(_thread_trace_func(_trace_thread_count))
    _trace_thread_count += 1


# Lazy loading
# ------------

class _ModuleProxy:
    _module = None

    def __init__(self, name: str) -> None:
        self.__dict__["_module_name"] = name

    def __getattr__(self, name: str): # noqa: ANN204
        try:
            return getattr(self._module, name)
        except AttributeError:
            if self._module is not None:
                raise

            import_name = f"pyglet.{self._module_name}"
            __import__(import_name)
            module = sys.modules[import_name]
            object.__setattr__(self, "_module", module)
            globals()[self._module_name] = module
            return getattr(module, name)

    def __setattr__(self, name: str, value: Any): # noqa: ANN204
        try:
            setattr(self._module, name, value)
        except AttributeError:
            if self._module is not None:
                raise

            import_name = f"pyglet.{self._module_name}"
            __import__(import_name)
            module = sys.modules[import_name]
            object.__setattr__(self, "_module", module)
            globals()[self._module_name] = module
            setattr(module, name, value)


# Lazily load all modules, except if performing type checking or code inspection.
if TYPE_CHECKING:
    from . import (
        app,
        clock,
        customtypes,
        display,
        event,
        font,
        gl,
        graphics,
        gui,
        image,
        input,
        lib,
        math,
        media,
        model,
        resource,
        shapes,
        sprite,
        text,
        window,
    )
else:
    app = _ModuleProxy("app")  # type: ignore
    clock = _ModuleProxy("clock")  # type: ignore
    customtypes = _ModuleProxy("customtypes")  # type: ignore
    display = _ModuleProxy("display")  # type: ignore
    event = _ModuleProxy("event")  # type: ignore
    font = _ModuleProxy("font")  # type: ignore
    gl = _ModuleProxy("gl")  # type: ignore
    graphics = _ModuleProxy("graphics")  # type: ignore
    gui = _ModuleProxy("gui")  # type: ignore
    image = _ModuleProxy("image")  # type: ignore
    input = _ModuleProxy("input")  # type: ignore
    lib = _ModuleProxy("lib")  # type: ignore
    math = _ModuleProxy("math")  # type: ignore
    media = _ModuleProxy("media")  # type: ignore
    model = _ModuleProxy("model")  # type: ignore
    resource = _ModuleProxy("resource")  # type: ignore
    sprite = _ModuleProxy("sprite")  # type: ignore
    shapes = _ModuleProxy("shapes")  # type: ignore
    text = _ModuleProxy("text")  # type: ignore
    window = _ModuleProxy("window")  # type: ignore

# Call after creating proxies:
if options.debug_trace is True:
    _install_trace()
