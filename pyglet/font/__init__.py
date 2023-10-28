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

import os
import sys
import weakref
from typing import Dict, Union, BinaryIO, Optional, List, Iterable

import pyglet
from pyglet.font.user import UserDefinedFont
from pyglet import gl


def _get_system_font_class():
    """Get the appropriate class for the system being used.
    Pyglet relies on OS dependent font systems for loading fonts and glyph creation.
    """
    if pyglet.compat_platform == 'darwin':
        from pyglet.font.quartz import QuartzFont
        _font_class = QuartzFont

    elif pyglet.compat_platform in ('win32', 'cygwin'):
        from pyglet.libs.win32.constants import WINDOWS_7_OR_GREATER
        if WINDOWS_7_OR_GREATER and not pyglet.options['win32_gdi_font']:
            from pyglet.font.directwrite import Win32DirectWriteFont
            _font_class = Win32DirectWriteFont
        else:
            from pyglet.font.win32 import GDIPlusFont
            _font_class = GDIPlusFont
    else:
        from pyglet.font.freetype import FreeTypeFont
        _font_class = FreeTypeFont

    return _font_class


def create_font(name: str, mappings: Dict[str, pyglet.image.ImageData], default_char: str,
                ascent: Optional[float] = None,
                descent: Optional[float] = None, size: Optional[float] = None, bold: bool = False,
                italic: bool = False, stretch: bool = False, dpi: Optional[float] = None,
                font_class=UserDefinedFont):
    """
        Create a custom font with the mappings provided.

        If a character in a string is not mapped in the font, it will use the default_char as fallback.

        Default size is 12.
        Ascent and descent will use the image dimensions as default, but can be provided.

        The rest of the font parameters are used for font lookups.
    """
    # Arbitrary default size
    if size is None:
        size = 12

    if dpi is None:
        dpi = 96

    # Locate or create font cache
    shared_object_space = gl.current_context.object_space
    if not hasattr(shared_object_space, 'pyglet_font_font_cache'):
        shared_object_space.pyglet_font_font_cache = weakref.WeakValueDictionary()
        shared_object_space.pyglet_font_font_hold = []
        shared_object_space.pyglet_font_font_name_match = {}  # Match a tuple to specific name to reduce lookups.

    font_cache = shared_object_space.pyglet_font_font_cache
    font_hold = shared_object_space.pyglet_font_font_hold

    # Look for font name in font cache
    descriptor = (name, size, bold, italic, stretch, dpi)
    if descriptor in font_cache:
        raise Exception("A font with these parameters has already been created.", descriptor)

    if _system_font_class.have_font(name):
        raise Exception(f"Font name: '{name}' already exists within the system fonts.")

    # Not in cache, create from scratch
    font = font_class(mappings, default_char, name, ascent, descent, size, bold, italic, stretch, dpi)

    # Save parameters for new-style layout classes to recover
    # TODO: add properties to the Font classes, so these can be queried:
    font.size = size
    font.bold = bold
    font.italic = italic
    font.stretch = stretch
    font.dpi = dpi

    if name not in _user_fonts:
        _user_fonts.append(name)

    # Cache font in weak-ref dictionary to avoid reloading while still in use
    font_cache[descriptor] = font

    # Hold onto refs of last three loaded fonts to prevent them being
    # collected if momentarily dropped.
    del font_hold[3:]
    font_hold.insert(0, font)

    return font


def have_font(name: str) -> bool:
    """Check if specified system font name is available."""
    return name in _user_fonts or _system_font_class.have_font(name)


def load(name: Optional[Union[str, Iterable[str]]] = None, size: Optional[float] = None, bold: bool = False,
         italic: bool = False,
         stretch: bool = False, dpi: Optional[float] = None):
    """Load a font for rendering.

    :Parameters:
        `name` : str, or list of str
            Font family, for example, "Times New Roman".  If a list of names
            is provided, the first one matching a known font is used.  If no
            font can be matched to the name(s), a default font is used.  In
            pyglet 1.1, the name may be omitted.
        `size` : float
            Size of the font, in points.  The returned font may be an exact
            match or the closest available.
        `bold` : bool
            If True, a bold variant is returned, if one exists for the given
            family and size.
        `italic` : bool
            If True, an italic variant is returned, if one exists for the given
            family and size.
        `dpi` : float
            The assumed resolution of the display device, for the purposes of
            determining the pixel size of the font.  Defaults to 96.

    :rtype: `Font`
    """
    # Arbitrary default size
    if size is None:
        size = 12

    if dpi is None:
        dpi = 96

    # Locate or create font cache
    shared_object_space = gl.current_context.object_space
    if not hasattr(shared_object_space, 'pyglet_font_font_cache'):
        shared_object_space.pyglet_font_font_cache = weakref.WeakValueDictionary()
        shared_object_space.pyglet_font_font_hold = []
        shared_object_space.pyglet_font_font_name_match = {}  # Match a tuple to specific name to reduce lookups.

    font_cache = shared_object_space.pyglet_font_font_cache
    font_hold = shared_object_space.pyglet_font_font_hold
    font_name_match = shared_object_space.pyglet_font_font_name_match

    name_type = type(name)
    if name_type in (tuple, list):
        if name_type == list:
            name = tuple(name)

        if name in font_name_match:
            name = font_name_match[name]
        else:
            # Find first matching name, cache it.
            found_name = None
            for n in name:
                if n in _user_fonts or _system_font_class.have_font(n):
                    found_name = n
                    break

            font_name_match[name] = found_name
            name = found_name

    # Look for font name in font cache
    descriptor = (name, size, bold, italic, stretch, dpi)
    if descriptor in font_cache:
        return font_cache[descriptor]

    # Not in cache, create from scratch
    font = _system_font_class(name, size, bold=bold, italic=italic, stretch=stretch, dpi=dpi)

    # Save parameters for new-style layout classes to recover
    # TODO: add properties to the Font classes, so these can be queried:
    font.size = size
    font.bold = bold
    font.italic = italic
    font.stretch = stretch
    font.dpi = dpi

    # Cache font in weak-ref dictionary to avoid reloading while still in use
    font_cache[descriptor] = font

    # Hold onto refs of last three loaded fonts to prevent them being
    # collected if momentarily dropped.
    del font_hold[3:]
    font_hold.insert(0, font)

    return font


if not getattr(sys, 'is_pyglet_doc_run', False):
    _system_font_class = _get_system_font_class()
    _user_fonts = []


def add_file(font: Union[str, BinaryIO]):
    """Add a font to pyglet's search path.

    In order to load a font that is not installed on the system, you must
    call this method to tell pyglet that it exists.  You can supply
    either a filename or any file-like object.

    The font format is platform-dependent, but is typically a TrueType font
    file containing a single font face. Note that to use a font added with this method,
    you should pass the face name (not the file name) to :meth::py:func:`pyglet.font.load` or any
    other place where you normally specify a font.

    :Parameters:
        `font` : str or file-like object
            Filename or file-like object to load fonts from.

    """
    if isinstance(font, str):
        font = open(font, 'rb')
    if hasattr(font, 'read'):
        font = font.read()
    _system_font_class.add_font_data(font)


def add_directory(directory):
    """Add a directory of fonts to pyglet's search path.

    This function simply calls :meth:`pyglet.font.add_file` for each file with a ``.ttf``
    extension in the given directory. Subdirectories are not searched.

    :Parameters:
        `dir` : str
            Directory that contains font files.

    """
    for file in os.listdir(directory):
        if file[-4:].lower() == '.ttf':
            add_file(os.path.join(directory, file))


__all__ = ('add_file', 'add_directory', 'load', 'have_font')
