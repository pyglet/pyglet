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
    BGR = 'BGR'
    BGRA = 'BGRA'


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
