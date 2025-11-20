from __future__ import annotations
from enum import Enum, auto


class GraphicsAPI(Enum):
    OPENGL = auto()
    OPENGL_2 = auto()
    OPENGL_ES_2 = auto()
    OPENGL_ES_3 = auto()
    WEBGL = auto()


class BlendFactor(Enum):
    ZERO = "ZERO"
    ONE = "ONE"
    SRC_COLOR = "SRC_COLOR"
    ONE_MINUS_SRC_COLOR = "ONE_MINUS_SRC_COLOR"
    DST_COLOR = "DST_COLOR"
    ONE_MINUS_DST_COLOR = "ONE_MINUS_DST_COLOR"
    SRC_ALPHA = "SRC_ALPHA"
    ONE_MINUS_SRC_ALPHA = "ONE_MINUS_SRC_ALPHA"
    DST_ALPHA = "DST_ALPHA"
    ONE_MINUS_DST_ALPHA = "ONE_MINUS_DST_ALPHA"
    CONSTANT_COLOR = "CONSTANT_COLOR"
    ONE_MINUS_CONSTANT_COLOR = "ONE_MINUS_CONSTANT_COLOR"
    CONSTANT_ALPHA = "CONSTANT_ALPHA"
    ONE_MINUS_CONSTANT_ALPHA = "ONE_MINUS_CONSTANT_ALPHA"


class BlendOp(Enum):
    ADD = "ADD"
    SUBTRACT = "SUBTRACT"
    REVERSE_SUBTRACT = "REVERSE_SUBTRACT"
    MIN = "MIN"
    MAX = "MAX"


class TextureFilter(Enum):
    LINEAR = auto()
    NEAREST = auto()


class AddressMode(Enum):
    REPEAT = auto()
    MIRRORED_REPEAT = auto()
    CLAMP_TO_EDGE = auto()
    CLAMP_TO_BORDER = auto()


class TextureWrapping(Enum):
    WRAP_S = auto()
    WRAP_T = auto()
    WRAP_R = auto()


class ComponentFormat(str, Enum):
    R = 'R'
    RG = 'RG'
    RGB = 'RGB'
    RGBA = 'RGBA'
    D = 'D'  # Depth Component
    DS = 'DS'  # Depth Stencil
    BGR = 'BGR'
    BGRA = 'BGRA'
    L = 'L'  # Luminance (R) - Deprecated
    LA = 'LA'  # Luminance Alpha (LA) - Deprecated


class TextureType(Enum):
    TYPE_1D = auto()
    TYPE_2D = auto()
    TYPE_3D = auto()
    TYPE_CUBE_MAP = auto()
    TYPE_1D_ARRAY = auto()
    TYPE_2D_ARRAY = auto()
    TYPE_CUBE_MAP_ARRAY = auto()


class CompareOp(Enum):
    NEVER = auto()
    LESS = auto()
    EQUAL = auto()
    LESS_OR_EQUAL = auto()
    GREATER = auto()
    NOT_EQUAL = auto()
    GREATER_OR_EQUAL = auto()
    ALWAYS = auto()

class FramebufferTarget(Enum):
    FRAMEBUFFER = auto()
    DRAW = auto()
    READ = auto()

class FramebufferAttachment(Enum):
    COLOR0 = auto()
    COLOR1 = auto()
    COLOR2 = auto()
    COLOR3 = auto()
    COLOR4 = auto()
    COLOR5 = auto()
    COLOR6 = auto()
    COLOR7 = auto()
    COLOR8 = auto()
    COLOR9 = auto()
    COLOR10 = auto()
    COLOR11 = auto()
    COLOR12 = auto()
    COLOR13 = auto()
    COLOR14 = auto()
    COLOR15 = auto()

    DEPTH = auto()
    STENCIL = auto()
    DEPTH_STENCIL = auto()



class Weight(str, Enum):
    """An :py:class:`~enum.Enum` of known cross-platform font weight strings.

    Each value is both an :py:class:`~enum.Enum` and a :py:class:`str`.
    This is not a built-in Python :py:class:`~enum.StrEnum` to ensure
    compatibility with Python < 3.11.

    .. important:: Fonts will use the closest match if they lack a weight.

    The values of this enum imitate the string names for font weights
    as used in CSS and the OpenType specification. Numerical font weights
    are not supported because:

    * Integer font weight support and behavior varies by back-end
    * Some font renderers do not support or round :py:class:`float` values
    * Some font renderers lack support for variable-width fonts

    Additional weight strings may be supported by certain font-rendering
    back-ends. To learn more, please see your platform's API documentation
    and the following:

    #. `The MDN article on CSS font weights <https://developer.mozilla.org/en-US/docs/Web/CSS/font-weight>`_
    #. `The OpenType specification <https://learn.microsoft.com/en-us/typography/opentype/spec/os2#usweightclass>`_

    """

    THIN = 'thin'
    EXTRALIGHT = 'extralight'
    LIGHT = 'light'
    NORMAL = 'normal'
    """The default weight for a font."""
    MEDIUM = 'medium'
    SEMIBOLD = 'semibold'
    BOLD = 'bold'
    """The default **bold** style for a font."""
    EXTRABOLD = 'extrabold'
    BLACK = 'black'
    EXTRABLACK = 'extrablack'

    def __str__(self) -> str:
        return self.value


class Stretch(str, Enum):
    """The stretch or width class of the font."""
    ULTRACONDENSED = 'ultracondensed'
    EXTRACONDENSED = 'extracondensed'
    CONDENSED = 'condensed'
    SEMICONDENSED = 'semicondensed'
    NORMAL = 'normal'
    """The default stretch for a font."""
    SEMIEXPANDED = 'semiexpanded'
    EXPANDED = 'expanded'
    EXTRAEXPANDED = 'extraexpanded'
    ULTRAEXPANDED = 'ultraexpanded'

    def __str__(self) -> str:
        return self.value


class Style(str, Enum):
    """The slant style of the font."""
    NORMAL = 'normal'
    """The default style for a font."""
    ITALIC = 'italic'
    OBLIQUE = 'oblique'
