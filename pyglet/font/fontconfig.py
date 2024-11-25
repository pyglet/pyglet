"""Wrapper around the Linux FontConfig library. Used to find available fonts."""
from __future__ import annotations

from collections import OrderedDict
from ctypes import CDLL, Structure, Union, byref, c_char_p, c_double, c_int, c_uint, c_void_p
from typing import TYPE_CHECKING

from pyglet.font.base import FontException
from pyglet.lib import load_library
from pyglet.util import asbytes, asstr

if TYPE_CHECKING:
    from pyglet.font.freetype_lib import FT_Face

# fontconfig library definitions

(FcResultMatch,
 FcResultNoMatch,
 FcResultTypeMismatch,
 FcResultNoId,
 FcResultOutOfMemory) = range(5)

FcResult = c_int

FC_FAMILY = asbytes("family")
FC_SIZE = asbytes("size")
FC_SLANT = asbytes("slant")
FC_WEIGHT = asbytes("weight")
FC_FT_FACE = asbytes("ftface")
FC_FILE = asbytes("file")

FC_WEIGHT_THIN = 10
FC_WEIGHT_EXTRALIGHT = 40
FC_WEIGHT_ULTRALIGHT = FC_WEIGHT_EXTRALIGHT
FC_WEIGHT_LIGHT = 50
FC_WEIGHT_DEMILIGHT = 55
FC_WEIGHT_SEMILIGHT = FC_WEIGHT_DEMILIGHT
FC_WEIGHT_BOOK = 75
FC_WEIGHT_REGULAR = 80
FC_WEIGHT_NORMAL = FC_WEIGHT_REGULAR
FC_WEIGHT_MEDIUM = 100
FC_WEIGHT_DEMIBOLD = 180
FC_WEIGHT_SEMIBOLD = FC_WEIGHT_DEMIBOLD
FC_WEIGHT_BOLD = 200
FC_WEIGHT_EXTRABOLD = 205
FC_WEIGHT_ULTRABOLD = FC_WEIGHT_EXTRABOLD
FC_WEIGHT_BLACK = 210
FC_WEIGHT_HEAVY = FC_WEIGHT_BLACK
FC_WEIGHT_EXTRABLACK = 215
FC_WEIGHT_ULTRABLACK = FC_WEIGHT_EXTRABLACK


name_to_weight = {
    True: FC_WEIGHT_BOLD,       # Temporary alias for attributed text
    False: FC_WEIGHT_NORMAL,    # Temporary alias for attributed text
    None: FC_WEIGHT_NORMAL,     # Temporary alias for attributed text
    "thin": FC_WEIGHT_THIN,
    "extralight": FC_WEIGHT_EXTRALIGHT,
    "ultralight": FC_WEIGHT_ULTRALIGHT,
    "light": FC_WEIGHT_LIGHT,
    "semilight": FC_WEIGHT_SEMILIGHT,
    "normal": FC_WEIGHT_NORMAL,
    "regular": FC_WEIGHT_REGULAR,
    "medium": FC_WEIGHT_MEDIUM,
    "demibold": FC_WEIGHT_DEMIBOLD,
    "semibold": FC_WEIGHT_SEMIBOLD,
    "bold": FC_WEIGHT_BOLD,
    "extrabold": FC_WEIGHT_EXTRABOLD,
    "ultrabold": FC_WEIGHT_ULTRABOLD,
    "black": FC_WEIGHT_BLACK,
    "heavy": FC_WEIGHT_HEAVY,
    "extrablack": FC_WEIGHT_EXTRABLACK,
}

weight_to_name = {
    0: 'thin',
    40: 'extralight',
    50: 'light',
    55: 'semilight',
    80: 'normal',
    100: 'medium',
    180: 'semibold',
    200: 'bold',
    205: 'extrabold',
    210: 'black',
    215: 'ultrabold',
}


FC_SLANT_ROMAN = 0
FC_SLANT_ITALIC = 100

(FcTypeVoid,
 FcTypeInteger,
 FcTypeDouble,
 FcTypeString,
 FcTypeBool,
 FcTypeMatrix,
 FcTypeCharSet,
 FcTypeFTFace,
 FcTypeLangSet) = range(9)
FcType = c_int

(FcMatchPattern,
 FcMatchFont) = range(2)
FcMatchKind = c_int


class _FcValueUnion(Union):
    _fields_ = [
        ("s", c_char_p),
        ("i", c_int),
        ("b", c_int),
        ("d", c_double),
        ("m", c_void_p),
        ("c", c_void_p),
        ("f", c_void_p),
        ("p", c_void_p),
        ("l", c_void_p),
    ]


class FcValue(Structure):
    _fields_ = [
        ("type", FcType),
        ("u", _FcValueUnion),
    ]


# End of library definitions


class FontConfig:
    _search_cache: OrderedDict[tuple[str, float, str, bool], FontConfigSearchResult]
    _fontconfig: CDLL | None

    def __init__(self) -> None:
        self._fontconfig = self._load_fontconfig_library()
        assert self._fontconfig is not None
        self._search_cache = OrderedDict()
        self._cache_size = 20

    def dispose(self) -> None:
        while len(self._search_cache) > 0:
            k, v = self._search_cache.popitem()
            v.dispose()

        self._fontconfig.FcFini()
        self._fontconfig = None

    def create_search_pattern(self) -> FontConfigSearchPattern:
        return FontConfigSearchPattern(self._fontconfig)

    def find_font(self, name: str, size: float = 12, weight: str = "normal", italic: bool = False) -> FontConfigSearchResult:
        if result := self._get_from_search_cache(name, size, weight, italic):
            return result

        search_pattern = self.create_search_pattern()
        search_pattern.name = name
        search_pattern.size = size
        search_pattern.weight = weight
        search_pattern.italic = italic

        result = search_pattern.match()
        self._add_to_search_cache(search_pattern, result)
        search_pattern.dispose()
        return result

    def have_font(self, name: str) -> bool:
        if result := self.find_font(name):
            # Check the name matches, fontconfig can return a default
            if name and result.name and result.name.lower() != name.lower():
                return False
            return True

        return False

    def char_index(self, ft_face: FT_Face, character: str) -> int:
        return self._fontconfig.FcFreeTypeCharIndex(ft_face, ord(character))

    def _add_to_search_cache(self, search_pattern: FontConfigSearchPattern,
                             result_pattern: FontConfigSearchResult) -> None:
        self._search_cache[(search_pattern.name,
                            search_pattern.size,
                            search_pattern.weight,
                            search_pattern.italic)] = result_pattern
        if len(self._search_cache) > self._cache_size:
            self._search_cache.popitem(last=False)[1].dispose()

    def _get_from_search_cache(self, name: str, size: float, weight: str, italic: bool) -> FontConfigSearchResult | None:
        result = self._search_cache.get((name, size, weight, italic), None)

        if result and result.is_valid:
            return result

        return None

    @staticmethod
    def _load_fontconfig_library() -> CDLL:
        fontconfig = load_library("fontconfig")
        fontconfig.FcInit()

        fontconfig.FcPatternBuild.restype = c_void_p
        fontconfig.FcPatternCreate.restype = c_void_p
        fontconfig.FcFontMatch.restype = c_void_p
        fontconfig.FcFreeTypeCharIndex.restype = c_uint

        fontconfig.FcPatternAddDouble.argtypes = [c_void_p, c_char_p, c_double]
        fontconfig.FcPatternAddInteger.argtypes = [c_void_p, c_char_p, c_int]
        fontconfig.FcPatternAddString.argtypes = [c_void_p, c_char_p, c_char_p]
        fontconfig.FcConfigSubstitute.argtypes = [c_void_p, c_void_p, c_int]
        fontconfig.FcDefaultSubstitute.argtypes = [c_void_p]
        fontconfig.FcFontMatch.argtypes = [c_void_p, c_void_p, c_void_p]
        fontconfig.FcPatternDestroy.argtypes = [c_void_p]

        fontconfig.FcPatternGetFTFace.argtypes = [c_void_p, c_char_p, c_int, c_void_p]
        fontconfig.FcPatternGet.argtypes = [c_void_p, c_char_p, c_int, c_void_p]

        return fontconfig


class FontConfigPattern:
    def __init__(self, fontconfig: CDLL, pattern: c_void_p | None = None) -> None:
        self._fontconfig = fontconfig
        self._pattern = pattern

    @property
    def is_valid(self) -> bool:
        return bool(self._fontconfig and self._pattern)

    def _create(self) -> None:
        assert not self._pattern
        assert self._fontconfig
        self._pattern = self._fontconfig.FcPatternCreate()

    def _destroy(self) -> None:
        assert self._pattern
        assert self._fontconfig
        self._fontconfig.FcPatternDestroy(self._pattern)
        self._pattern = None

    @staticmethod
    def _italic_to_slant(italic: bool) -> int:
        return FC_SLANT_ITALIC if italic else FC_SLANT_ROMAN

    def _set_string(self, name: bytes, value: str) -> None:
        assert self._pattern
        assert name
        assert self._fontconfig

        if not value:
            return

        value = value.encode("utf8")

        self._fontconfig.FcPatternAddString(self._pattern, name, asbytes(value))

    def _set_double(self, name: bytes, value: int) -> None:
        assert self._pattern
        assert name
        assert self._fontconfig

        if not value:
            return

        self._fontconfig.FcPatternAddDouble(self._pattern, name, c_double(value))

    def _set_integer(self, name: bytes, value: int) -> None:
        assert self._pattern
        assert name
        assert self._fontconfig

        if not value:
            return

        self._fontconfig.FcPatternAddInteger(self._pattern, name, c_int(value))

    def _get_value(self, name: bytes) -> FcValue | None:
        assert self._pattern
        assert name
        assert self._fontconfig

        value = FcValue()
        result: FcResult = self._fontconfig.FcPatternGet(self._pattern, name, 0, byref(value))
        if _handle_fcresult(result):
            return value

        return None

    def _get_string(self, name: bytes) -> str | None:
        value = self._get_value(name)

        if value and value.type == FcTypeString:
            return asstr(value.u.s)

        return None

    def _get_face(self, name: bytes) -> FT_Face | None:
        value = self._get_value(name)

        if value and value.type == FcTypeFTFace:
            return value.u.f

        return None

    def _get_integer(self, name: bytes) -> int | None:
        value = self._get_value(name)

        if value and value.type == FcTypeInteger:
            return value.u.i

        return None

    def _get_double(self, name: bytes) -> int | None:
        value = self._get_value(name)

        if value and value.type == FcTypeDouble:
            return value.u.d

        return None


class FontConfigSearchPattern(FontConfigPattern):
    size: int | None
    italic: bool
    weight: str
    name: str | None

    def __init__(self, fontconfig: CDLL) -> None:
        super().__init__(fontconfig)

        self.name = None
        self.weight = "normal"
        self.italic = False
        self.size = None

    def match(self) -> FontConfigSearchResult | None:
        self._prepare_search_pattern()
        result_pattern = self._get_match()

        if result_pattern:
            return FontConfigSearchResult(self._fontconfig, result_pattern)

        return None

    def _prepare_search_pattern(self) -> None:
        self._create()
        self._set_string(FC_FAMILY, self.name)
        self._set_double(FC_SIZE, self.size)
        self._set_double(FC_WEIGHT, name_to_weight[self.weight])
        self._set_integer(FC_SLANT, self._italic_to_slant(self.italic))

        self._substitute_defaults()

    def _substitute_defaults(self) -> None:
        assert self._pattern
        assert self._fontconfig

        self._fontconfig.FcConfigSubstitute(None, self._pattern, FcMatchPattern)
        self._fontconfig.FcDefaultSubstitute(self._pattern)

    def _get_match(self) -> c_void_p | None:
        assert self._pattern
        assert self._fontconfig

        match_result = FcResult()
        match_pattern = self._fontconfig.FcFontMatch(0, self._pattern, byref(match_result))

        if _handle_fcresult(match_result.value):
            return match_pattern

        return None

    def dispose(self) -> None:
        self._destroy()


class FontConfigSearchResult(FontConfigPattern):
    def __init__(self, fontconfig: CDLL, result_pattern: c_void_p | None) -> None:
        super().__init__(fontconfig, result_pattern)

    @property
    def name(self) -> str:
        return self._get_string(FC_FAMILY)

    @property
    def size(self) -> int:
        return self._get_double(FC_SIZE)

    @property
    def weight(self) -> str:
        return weight_to_name[self._get_double(FC_WEIGHT)]

    @property
    def italic(self) -> bool:
        return self._get_integer(FC_SLANT) == FC_SLANT_ITALIC

    @property
    def face(self) -> FT_Face:
        return self._get_face(FC_FT_FACE)

    @property
    def file(self) -> str:
        return self._get_string(FC_FILE)

    def dispose(self) -> None:
        self._destroy()


def _handle_fcresult(result: int) -> bool | None:
    if result == FcResultMatch:
        return True
    if result in (FcResultNoMatch, FcResultTypeMismatch, FcResultNoId):
        return False
    if result == FcResultOutOfMemory:
        msg = "FontConfig ran out of memory."
        raise FontException(msg)
    return None


_fontconfig_instance = None


def get_fontconfig() -> FontConfig:
    global _fontconfig_instance  # noqa: PLW0603
    if not _fontconfig_instance:
        _fontconfig_instance = FontConfig()
    return _fontconfig_instance
