from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pyglet
from pyglet.font import base

if TYPE_CHECKING:
    from pyglet.enums import Weight, Style, Stretch


@dataclass(frozen=True)
class _RangeEntry:
    start: int
    end:   int
    family: str


class FontGroup:
    """A collection of fonts that can be used like a single font.

    Each font can be assigned a range of Unicode values that it is set to handle.

    .. versionadded:: 3.0
    """
    _instance_cache: dict[tuple[float,  str | Weight, str | Style, str | Stretch, int], FontGroupInstance]
    _ranges: list[_RangeEntry]

    def __init__(self, name: str) -> None:
        """Create a new font group.

        Args:
            name:
                A unique name describing the grouping; must be unique enough to not collide with an existing font.
        """
        self.name = name
        self._ranges = []
        self._instance_cache = {}

    def add(self, family: str, start: int | str, end: int | str) -> FontGroup:
        """Add a font family responsible for a range of characters.

        The first match will be used by layouts.

        Args:
            family:
                The name of the font family for this range.
            start:
                The start of the range. This may be a single-character string or an integer corresponding to a Unicode
                code point.
            end:
                The end of the range. This may be a single-character string or an integer corresponding to a Unicode
                code point.

        Returns:
            This existing font group instance.
        """
        self._ranges.append(_RangeEntry(start, end, family))
        return self

    def get_font(self,
                 size: float | None,
                 weight: str | None = "normal",
                 style: str | None = "normal",
                 stretch: str | None = "normal",
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

    def _family_for_char(self, ch: str) -> str | None:
        cp = ord(ch)
        for r in self._ranges:
            if r.start <= cp <= r.end:
                return r.family
        return None

class FontGroupInstance(base.Font):
    """A font instance based off the FontGroup."""
    _child_cache: dict[str, base.Font]

    def __init__(self, group: FontGroup, size: float, weight: str | Weight, style: str | Style,  # noqa: D107
                 stretch: str | Stretch,  dpi: int | None) -> None:
        super().__init__("", size, weight, style, stretch, dpi)
        self._name = self._get_name()
        self._group = group

        self._child_cache = {}
        self.glyphs.clear()  # This itself doesn't own glyphs

    def _get_name(self) -> str:
        """Generates a unique descriptor name for this instance."""
        ital = "Italic" if self.style else "Regular"
        return f"{self.name} ({int(self.size)}px {ital} w{self.weight} s{self.stretch} @{self.dpi}dpi)"

    def _resolve_child(self, family: str) -> base.Font:
        f = self._child_cache.get(family)
        if f is None:
            f = pyglet.font.load(family,
                                 size=self.size,
                                 weight=self.weight,
                                 style=self.style,
                                 stretch=self.stretch,
                                 dpi=self.dpi)
            self._child_cache[family] = f

            self.ascent = max(self.ascent, getattr(f, "ascent", 0))
            self.descent = max(self.descent, getattr(f, "descent", 0))
        return f

    def _font_for_cluster(self, cluster: str) -> base.Font | None:
        if not cluster:
            return None
        ft_fam = self._group._family_for_char(cluster[0])  # noqa: SLF001
        if ft_fam is None and self._group._ranges:  # noqa: SLF001
            # Default to first font in the group if nothing matches
            fam = self._group._ranges[0].family  # noqa: SLF001
        return self._resolve_child(ft_fam) if ft_fam else None

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
        max_ascent = self.ascent
        max_descent = self.descent

        run_font: base.Font | None = None
        run_text: list[str] = []

        def flush() -> None:
            nonlocal total_w, max_ascent, max_descent, run_font, run_text
            if run_font and run_text:
                w, _ = run_font.get_text_size("".join(run_text))
                total_w += w
                max_ascent = max(max_ascent, getattr(run_font, "ascent", 0))
                max_descent = max(max_descent, getattr(run_font, "descent", 0))
            run_font = None
            run_text = []

        for cluster in base.get_grapheme_clusters(text):
            f = self._font_for_cluster(cluster)
            if f is not run_font:
                flush()
                run_font = f
            run_text.append(" " if cluster == "\t" else cluster)

        flush()
        return (total_w, max_ascent + max_descent)
