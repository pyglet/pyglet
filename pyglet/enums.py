from __future__ import annotations
from enum import Enum, auto
from typing import NamedTuple


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


class TextureInternalFormat(NamedTuple):
    component: ComponentFormat | str
    depth: int | None = None
    data_type: type[float, int] | None = None


class TextureDescriptor:
    __slots__ = (
        "address_mode",
        "anisotropic_level",
        "depth",
        "internal_format",
        "mag_filter",
        "min_filter",
        "mipmap_levels",
        "pixel_format",
        "tex_type",
    )

    def __init__(self,
                 tex_type: TextureType = TextureType.TYPE_2D,
                 min_filter: TextureFilter = TextureFilter.LINEAR,
                 mag_filter: TextureFilter = TextureFilter.LINEAR,
                 address_mode: AddressMode = AddressMode.REPEAT,
                 internal_format: TextureInternalFormat | None = None,
                 pixel_format: ComponentFormat = ComponentFormat.RGBA,
                 anisotropic_level: int = 0,
                 depth: int = 1,
                 mipmap_levels: int = 1):
        """Create a description of the texture.

        Args:
            tex_type:
                The default texture type. Defaults to TYPE_2D.
            min_filter:
                The default minification filter. Defaults to LINEAR.
            mag_filter:
                The default magnification filter. Defaults to LINEAR.
            address_mode:
                The border repeat mode for textures once values fall outside 0-1.
            internal_format:
                The internal pixel format of the intended texture. Defaults to RGBA 8bits per channel.
            pixel_format:
                The pixel format order of the data that will be written. Defaults to RGBA.
            anisotropic_level:
                The anisotropic filtering level, 0 is disabled. Not always supported.
        """
        self.tex_type = tex_type
        self.min_filter = min_filter
        self.mag_filter = mag_filter
        self.address_mode = address_mode
        self.internal_format = internal_format or TextureInternalFormat(ComponentFormat.RGBA, 8)
        self.pixel_format = pixel_format
        self.anisotropic_level = anisotropic_level
