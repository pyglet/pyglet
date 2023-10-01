from pyglet.font.base import Font


class UserDefinedFontBase(Font):
    def __init__(
            self, name: str, default_char: str, size: int, ascent: int = None,
            descent: int = None, bold: bool = False, italic: bool = False,
            stretch: bool = False, dpi: int = 96,locale: str = None
    ):
        super().__init__()
        self._name = name
        self.default_char = default_char
        self.ascent = ascent
        self.descent = descent
        self.size = size
        self.bold = bold
        self.italic = italic
        self.stretch = stretch
        self.dpi = dpi
        self.locale = locale

    @property
    def name(self) -> str:
        return self._name


class UserDefinedFontException(Exception):
    pass


__all__ = (
    "UserDefinedFontBase",
    "UserDefinedFontException"
)
