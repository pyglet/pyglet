from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pyglet
from pyglet.enums import Stretch, Style, Weight
from pyglet.font import base


@dataclass(frozen=True)
class _RangeEntry:
    start: int
    end: int
    family: str


class FontGroupBase(ABC):
    """Base class for a collection of fonts used as one font.

    Applications normally use :class:`FontGroup` for ordered glyph fallback,
    or :class:`FontRangeGroup` when they need explicit Unicode-range routing.
    """
    _instance_cache: dict[tuple[float, str | Weight, str | Style, str | Stretch, int], FontGroupInstance]

    def __init__(self, name: str) -> None:
        self.name = name
        self._instance_cache = {}

    def get_font(
        self,
        size: float | None,
        weight: Weight | str | None = Weight.NORMAL,
        style: Style | str | None = Style.NORMAL,
        stretch: Stretch | str | None = Stretch.NORMAL,
        dpi: int | None = None,
    ) -> FontGroupInstance:
        size = size or 12
        dpi = dpi or 96
        weight = weight or Weight.NORMAL
        style = style or Style.NORMAL
        stretch = stretch or Stretch.NORMAL

        descriptor = (size, weight, style, stretch, dpi)
        inst = self._instance_cache.get(descriptor)
        if inst is None:
            inst = FontGroupInstance(self, size, weight, style, stretch, dpi)
            self._instance_cache[descriptor] = inst
        return inst

    @abstractmethod
    def _families_for_cluster(self, cluster: str) -> tuple[str, ...]:
        """Return candidate families in selection order for ``cluster``."""


class FontGroup(FontGroupBase):
    """An ordered set of fallback font families.

    Each character is rendered by the first added family that contains it.
    If no family contains a character, the first family supplies its
    normal missing-glyph representation.

    .. versionadded:: 3.0
    """
    _families: list[str]

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._families = []

    def add(self, family: str) -> FontGroup:
        """Add a font family to the fallback chain.

        Families are checked in the order in which they are added.
        """
        self._families.append(family)
        return self

    def _families_for_cluster(self, cluster: str) -> tuple[str, ...]:  # noqa: ARG002
        return tuple(self._families)


class FontRangeGroup(FontGroupBase):
    """A collection of fonts selected by explicit Unicode ranges.

    The first matching range chooses the family. If no range matches, the
    first added family is used. Unlike :class:`FontGroup`, this class does not
    probe subsequent families for missing characters.

    .. versionadded:: 3.0
    """
    _ranges: list[_RangeEntry]

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._ranges = []

    def add(self, family: str, start: int | str, end: int | str) -> FontRangeGroup:
        """Add a font family responsible for a range of characters."""
        if isinstance(start, str):
            start = ord(start)
        if isinstance(end, str):
            end = ord(end)
        self._ranges.append(_RangeEntry(start, end, family))
        return self

    def _families_for_cluster(self, cluster: str) -> tuple[str, ...]:
        if not self._ranges:
            return ()
        codepoint = ord(cluster[0])
        for entry in self._ranges:
            if entry.start <= codepoint <= entry.end:
                return (entry.family,)
        return (self._ranges[0].family,)


class FontGroupInstance(base.Font):
    """A font instance based on a :class:`FontGroupBase`."""
    _child_cache: dict[str, base.Font]

    def __init__(self, group: FontGroupBase, size: float, weight: Weight | str, style: Style | str,
                 stretch: Stretch | str, dpi: int | None) -> None:
        super().__init__("", size, weight, style, stretch, dpi)
        self._group = group
        self._name = self._get_name()
        self._child_cache = {}
        self.glyphs.clear()

    def _get_name(self) -> str:
        italic = "Italic" if self.style != "normal" else "Regular"
        return f"{self._group.name} ({int(self.size)}px {italic} w{self.weight} s{self.stretch} @{self.dpi}dpi)"

    def _resolve_child(self, family: str) -> base.Font:
        font = self._child_cache.get(family)
        if font is None:
            font = pyglet.font.load(family, size=self.size, weight=self.weight, style=self.style,
                                    stretch=self.stretch, dpi=self.dpi)
            self._child_cache[family] = font
            self.ascent = max(self.ascent, getattr(font, "ascent", 0))
            self.descent = min(self.descent, getattr(font, "descent", 0))
        return font

    @staticmethod
    def _supports_cluster(font: base.Font, cluster: str) -> bool:
        # A group chooses a single face for a grapheme cluster.
        ignored = {"\u200c", "\u200d"}
        return all(font.has_character(char) for char in cluster
                   if char not in ignored and not 0xfe00 <= ord(char) <= 0xfe0f)

    def _font_for_cluster(self, cluster: str, allow_missing: bool = True) -> base.Font | None:
        candidates = self._group._families_for_cluster(cluster)
        for family in candidates:
            font = self._resolve_child(family)
            if isinstance(self._group, FontRangeGroup) or self._supports_cluster(font, cluster):
                return font
        return self._resolve_child(candidates[0]) if allow_missing and candidates else None

    def has_character(self, character: str) -> bool:
        super().has_character(character)
        if isinstance(self._group, FontRangeGroup):
            candidates = self._group._families_for_cluster(character)
            return bool(candidates) and self._resolve_child(candidates[0]).has_character(character)
        return self._font_for_cluster(character, allow_missing=False) is not None

    def get_glyphs(self, text: str, shaping: bool = False) -> tuple[list[base.Glyph], list[base.GlyphPosition]]:
        glyphs: list[base.Glyph] = []
        offsets: list[base.GlyphPosition] = []

        for cluster in base.get_grapheme_clusters(str(text)):
            c = " " if cluster == "\t" else cluster
            fnt = self._font_for_cluster(c)
            if fnt is None:
                self._initialize_renderer()
                gs = self._missing_glyph or self._glyph_renderer.render(" ")
                gp = base.GlyphPosition(0, 0, 0, 0)
                glyphs.append(gs)
                offsets.append(gp)
            else:
                gs, gp = fnt.get_glyphs(c, shaping)
                glyphs.extend(gs)
                offsets.extend(gp)

        return glyphs, offsets

    def get_text_size(self, text: str) -> tuple[int, int]:
        if not text:
            return 0, 0

        total_w = 0
        max_height = 0

        run_font: base.Font | None = None
        run_text: list[str] = []

        def flush() -> None:
            nonlocal total_w, max_height, run_font, run_text
            if run_font and run_text:
                w, h = run_font.get_text_size("".join(run_text))
                total_w += w
                max_height = max(max_height, h)
            run_font = None
            run_text = []

        for cluster in base.get_grapheme_clusters(text):
            f = self._font_for_cluster(cluster)
            if f is not run_font:
                flush()
                run_font = f
            run_text.append(" " if cluster == "\t" else cluster)

        flush()
        return total_w, max_height


__all__ = ("FontGroup", "FontGroupBase", "FontGroupInstance", "FontRangeGroup")
