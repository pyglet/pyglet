"""Load fonts.

pyglet will automatically load any system-installed fonts.  You can add additional fonts
(for example, from your program resources) using :meth:`add_file` or
:meth:`add_directory`. These fonts are then available in the same way as system-installed fonts::

    from pyglet import font
    font.add_file('action_man.ttf')
    action_man = font.load('Action Man', 16)
    # or
    from pyglet import resource
    resource.add_font('action_man.ttf')
    action_man = font.load('Action Man')

See the :mod:`pyglet.font.base` module for documentation on the base classes used
by this package.
"""

from __future__ import annotations

import collections
import os
import sys
import weakref
from dataclasses import dataclass
from typing import TYPE_CHECKING, BinaryIO, Iterable, Sequence, Any

import pyglet
from pyglet.enums import Weight, Style, Stretch
from pyglet.font.group import FontGroup
from pyglet.font.user import UserDefinedFontBase
from pyglet.graphics.api import core

if TYPE_CHECKING:
    from pyglet.event import EVENT_HANDLE_STATE
    from pyglet.font.base import Font
    from pyglet.graphics.api.base import SurfaceContext


@dataclass
class _FontContext:
    """A container for data specific to a graphics context.

    Glyph textures can only be used in their respective graphics context.
    """
    context: SurfaceContext
    cache: weakref.WeakValueDictionary[tuple, Font]

    # Hold onto refs of last three loaded fonts to prevent them being
    # collected if momentarily dropped.
    hold: collections.deque

    def add(self, descriptor: tuple, font: Font) -> None:
        """Add a font with the descriptor into the cache."""
        self.cache[descriptor] = font
        self.hold.appendleft(font)



class FontManager(pyglet.event.EventDispatcher):
    """A manager to keep track of system fonts, font files, and user loaded fonts.

    This is a global singleton and should not be instantiated by a user.

    .. versionadded: 3.0
    """
    default_win32_font = "Segoe UI"
    default_darwin_font = "System Default"
    default_linux_font = "sans"  # FC will convert to actual font.
    default_emscripten_font = "Times New Roman"

    resolved_names: dict[tuple[str, ...], str]

    _font_groups: dict[str, FontGroup]
    _user_font_names: set[str]
    _font_contexts: weakref.WeakKeyDictionary[SurfaceContext, _FontContext]

    def __init__(self) -> None:
        self._font_contexts = weakref.WeakKeyDictionary()
        self._hold = collections.deque(maxlen=3)
        self._added_families = set()
        self._added_faces = set()
        self._user_font_names = set()
        self._font_groups = {}

        # A mapping of sequence to the resulting font name.
        self.resolved_names = {}

    def _invalidate(self) -> None:
        """Invalidates all caches.

        Used for tests.
        """
        self._font_contexts.clear()
        self._hold.clear()
        self._added_families.clear()
        self._added_faces.clear()
        self._user_font_names.clear()
        self.resolved_names.clear()

    @staticmethod
    def _get_key_name(name: str | Sequence[str]) -> tuple[str, ...]:
        if isinstance(name, list):
            key_names = tuple(name)
        elif isinstance(name, str):
            key_names = (name,)
        else:
            key_names = name

        return key_names

    def get_group(self, name: str) -> FontGroup | None:
        """Check if the specified name is a font group."""
        return self._font_groups.get(name)

    def get_resolved_name(self, name: str | Sequence[str]) -> str | None:
        """Return the name of the first font found for a name or list of names.

        If a font is not found, a default font will be used depending on the platform.

        A sequence of font names can be used with layouts, using the first found. Each name is checked to ensure
        it exists everytime it is used or text changes.

        Platform specific ``have_font`` calls can be slow depending on the platform.
        """
        key_names = self._get_key_name(name)

        if key_names in self.resolved_names:
            return self.resolved_names[key_names]

        for font_name in key_names:
            if font_name in self._user_font_names or font_name in self._font_groups or _system_font_class.have_font(font_name):
                self.resolved_names[key_names] = font_name
                return font_name

        # If nothing found here, then get a default name.
        self.resolved_names[key_names] = manager.get_platform_default_name()
        return self.resolved_names[key_names]

    def get_platform_default_name(self) -> str:
        """Return a font name that should be guaranteed to exist on a particular platform."""
        if pyglet.compat_platform == "win32":
            return self.default_win32_font
        if pyglet.compat_platform == "darwin":
            return self.default_darwin_font
        if pyglet.compat_platform == "linux":
            return self.default_linux_font
        if pyglet.compat_platform == "emscripten":
            return self.default_emscripten_font

        msg = f"Unsupported platform: {pyglet.compat_platform}"
        raise Exception(msg)

    def _get_context_data(self, context: SurfaceContext | None = None) -> _FontContext:
        """Get a font context based on the current graphics context."""
        graphics_ctx = context or core.current_context
        try:
            return self._font_contexts[graphics_ctx]
        except KeyError:
            font_context = _FontContext(graphics_ctx, weakref.WeakValueDictionary(), collections.deque(maxlen=3))
            self._font_contexts[graphics_ctx] = font_context
            return font_context

    def have_font(self, name: str) -> bool:
        """Check if specified font name is available in the system database or user font database."""
        return name in self._font_groups or name in self._user_font_names or self._get_key_name(name) in self.resolved_names or _system_font_class.have_font(name)

    def _add_user_font(self, font: UserDefinedFontBase) -> None:
        self._user_font_names.add(font.name)
        self.dispatch_event("on_font_loaded", font.name, font.weight, font.style, font.stretch)

    def _add_font_group(self, group: FontGroup) -> None:
        self._font_groups[group.name] = group

    def _add_loaded_font(self, fonts: set[tuple[str, str, str, str]]) -> None:
        old = self._added_faces
        new_fonts = fonts - old
        self._added_faces.update(fonts)

        # Clear any resolved names as this affects already loaded fonts.
        self.resolved_names.clear()

        for new_font in new_fonts:
            self._added_families.add(new_font[0])
            self.dispatch_event("on_font_loaded", *new_font)

    def on_font_loaded(self, family_name: str, weight: str, style: str, stretch: str) -> EVENT_HANDLE_STATE:
        """When a font is loaded, this event will be dispatched with the family name and style of the font.

        On some platforms, a custom added font may not be available immediately after adding the data. In these cases,
        you can set a handler on this event to get notified when it's available.

        .. note:: Not currently supported by GDI.
        """


manager = FontManager()
manager.register_event_type("on_font_loaded")

def _get_system_font_class() -> type[Font]:
    """Get the appropriate class for the system being used.

    Pyglet relies on OS dependent font systems for loading fonts and glyph creation.
    """
    if pyglet.compat_platform == "darwin":
        from pyglet.font.quartz import QuartzFont

        _font_class = QuartzFont

    elif pyglet.compat_platform in ("win32", "cygwin"):
        from pyglet.libs.win32.constants import WINDOWS_7_OR_GREATER

        if WINDOWS_7_OR_GREATER and not pyglet.options["win32_gdi_font"]:
            from pyglet.font.dwrite import Win32DirectWriteFont

            _font_class = Win32DirectWriteFont
        else:
            from pyglet.font.win32 import GDIPlusFont

            _font_class = GDIPlusFont
    elif pyglet.compat_platform == "linux":
        from pyglet.font.freetype import FreeTypeFont

        _font_class = FreeTypeFont
    elif pyglet.compat_platform == "emscripten":
        from pyglet.font.pyodide_js import JavascriptPyodideFont

        _font_class = JavascriptPyodideFont
    else:
        raise Exception("Font Renderer is not available for this Operating System.")

    return _font_class

def add_group(font_group: FontGroup) -> None:
    """Add a font group to pyglet's list of font groups."""
    assert isinstance(font_group, FontGroup), "Added group must be based on a FontGroup class."

    if _system_font_class.have_font(font_group.name):
        msg = f"Cannot use FontGroup, name '{font_group.name}' already exists within the system or loaded fonts."
        raise Exception(msg)

    manager._add_font_group(font_group)  # noqa: SLF001

def add_user_font(font: UserDefinedFontBase) -> None:
    """Add a custom font created by the user.

    A strong reference needs to be applied to the font object,
    otherwise pyglet may not find the font later.

    Args:
        font:
            A font class instance defined by user.

    Raises:
        Exception: If font provided is not derived from :py:class:`~pyglet.font.user.UserDefinedFontBase`.
    """
    if not isinstance(font, UserDefinedFontBase):
        msg = "Font must be created from the UserDefinedFontBase."
        raise Exception(msg)

    # Locate or create font cache
    font_context = manager._get_context_data(core.current_context)  # noqa: SLF001

    # Look for font name in font cache
    descriptor = (font.name, font.size, font.weight, font.style, font.stretch, font.dpi)
    if descriptor in font_context.cache:
        msg = f"A font with parameters {descriptor} has already been created. Use a more unique name."
        raise Exception(msg)
    if _system_font_class.have_font(font.name):
        msg = f"Font name '{font.name}' already exists within the system or loaded fonts."
        raise Exception(msg)

    font_context.add(descriptor, font)
    manager._add_user_font(font)  # noqa: SLF001


def have_font(name: str) -> bool:
    """Check if specified font name is available in the system database or user font database."""
    return manager.have_font(name)


def load(
    name: str | Iterable[str] | None = None,
    size: float | None = None,
    weight: str | None = "normal",
    style: str | None = "normal",
    stretch: str | None = "normal",
    dpi: int | None = None,
) -> Font:
    """Load a font for rendering.

    Args:
        name:
            Font family, for example, "Times New Roman".  If a list of names
            is provided, the first one matching a known font is used.  If no
            font can be matched to the name(s), a default font is used.
            The default font will be platform dependent.
        size:
            Size of the font, in points.  The returned font may be an exact
            match or the closest available.
        weight:
            If set, a specific weight variant is returned if one exists for the given font
            family and size. For example, "bold" can be specified. Refer to :py:class:`~pyglet.enums.Weight`
            for valid options.
        style:
            If specified, an italic variant can be returned if one exists for the given family and size. If a font is
            oblique, or italic, either will fallback to choose that variation. Refer to :py:class:`~pyglet.enums.Style`
            for valid options.
        stretch:
            If specified a stretch variant is returned, if one exists for the given family and size. Refer to
            :py:class:`~pyglet.enums.Stretch` for valid options.
        dpi: int
            The assumed resolution of the display device, for the purposes of
            determining the pixel size of the font.  Defaults to 96.
    """
    # TextLayouts pass `None` for unused style keys from run _FontStyleRunsRangeIterator.
    size = size or 12  # Arbitrary default size
    dpi = dpi or 96
    weight = weight or Weight.NORMAL
    style = style or Style.NORMAL
    stretch = stretch or Stretch.NORMAL

    if name is None:
        name = manager.get_platform_default_name()

    font_context = manager._get_context_data(core.current_context)  # noqa: SLF001
    name = manager.get_resolved_name(name)

    # Look for font name in font cache
    descriptor = (name, size, weight, style, stretch, dpi)
    if descriptor in font_context.cache:
        return font_context.cache[descriptor]

    assert weight is not None
    assert style is not None
    assert stretch is not None
    if font_group := manager.get_group(name):
        font = font_group.get_font(size, weight=weight, style=style, stretch=stretch, dpi=dpi)
    else:
        font = _system_font_class(name, size, weight=weight, style=style, stretch=stretch, dpi=dpi)

    # Font system changed the name. Create two descriptors for it, so both can be used.
    if font.name != name:
        fs_descriptor = (font.name, size, weight, style, stretch, dpi)
        font_context.add(fs_descriptor, font)

    # Cache font in weak-ref dictionary to avoid reloading while still in use
    font_context.add(descriptor, font)
    return font


if not getattr(sys, "is_pyglet_doc_run", False):
    _system_font_class = _get_system_font_class()


def add_file(font: str | BinaryIO | bytes) -> None:
    """Add a font to pyglet's search path.

    In order to load a font that is not installed on the system, you must
    call this method to tell pyglet that it exists.  You can supply
    either a filename or any file-like object.

    The font format is platform-dependent, but is typically a TrueType font
    file containing a single font face. Note that to use a font added with this method,
    you should pass the face name (not the file name) to :meth::py:func:`pyglet.font.load` or any
    other place where you normally specify a font.

    Args:
        font:
            Filename, file-like object, or bytes to load fonts from.

    """
    if isinstance(font, str):
        font = open(font, "rb")  # noqa: SIM115
    if hasattr(font, "read"):
        font = font.read()
    _system_font_class.add_font_data(font, manager)


def add_directory(directory: str) -> None:
    """Add a directory of fonts to pyglet's search path.

    This function simply calls :meth:`pyglet.font.add_file` for each file with a ``.ttf``
    extension in the given directory. Subdirectories are not searched.

    Args:
        directory:
            Directory that contains font files.

    """
    for file in os.listdir(directory):
        if file[-4:].lower() == ".ttf":
            add_file(os.path.join(directory, file))

def get_custom_font_names() -> tuple[str, ...]:
    """The names of font families added to pyglet via :py:func:`~pyglet.font.add_file`.

    .. versionadded:: 3.0
    """
    return tuple(manager._added_families)  # noqa: SLF001


__all__ = ("add_directory", "add_file", "add_user_font", "get_custom_font_names", "have_font", "load", "manager")
