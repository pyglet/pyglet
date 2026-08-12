import pyglet
import pytest
from pyglet.font.harfbuzz import harfbuzz_available
from tests.annotations import skip_platform, require_platform, Platform


def test_font_create_default(test_window, test_data):
    ft = pyglet.font.load()
    assert ft.name is not None


def test_default_font_get_text_size(test_window):
    font = pyglet.font.load()
    width, height = font.get_text_size("Backend text")
    assert width > 0
    assert height > 0


def test_font_preload_glyphs(test_window):
    font = pyglet.font.load(None, size=12, dpi=96)
    characters = "".join(chr(codepoint) for codepoint in range(0x20, 0x7f))

    assert font.preload_glyphs() is None

    glyphs, _ = font.get_glyphs(characters, shaping=False)
    assert len(glyphs) == len(characters)
    assert all(any(cached is glyph for cached in font.glyphs.values()) for glyph in glyphs)


def test_default_platform_font():
    """Ensure the platform has a default font from the manager."""
    assert pyglet.font.manager.get_platform_default_name() is not None


def test_missing_font():
    assert not pyglet.font.have_font('definitely-doesnt-exist-font')


def test_missing_font_loads_a_usable_fallback(test_window):
    font = pyglet.font.load("definitely-doesnt-exist-font-638593", size=12, dpi=96)

    assert font.name
    glyphs, _ = font.get_glyphs("Fallback", shaping=False)
    assert len(glyphs) == len("Fallback")


@skip_platform(Platform.LINUX)
def test_load_no_custom_from_list(test_data):
    # First found font, should be Arial since Action Man is not loaded.
    myfont = pyglet.font.load(["Action Man", "Arial"], size=12, dpi=96)
    assert myfont.name == "Arial"
    # Make sure name resolves to an actual found font.
    assert pyglet.font.manager.get_resolved_name(["Action Man", "Arial"]) == 'Times New Roman'

@require_platform(Platform.LINUX)  # Same as above, but Linux runner uses DejaVu Sans.
def test_load_no_custom_from_list(test_data):
    myfont = pyglet.font.load(["Action Man", "DejaVu Sans"], size=12, dpi=96)
    assert myfont.name == "DejaVu Sans"
    # Make sure name resolves to an actual found font.
    assert pyglet.font.manager.get_resolved_name(["Action Man", "DejaVu Sans"]) == 'DejaVu Sans'

def test_load_privatefont(test_window, test_data):
    file = test_data.get_file('fonts', 'action_man.ttf')
    pyglet.font.add_file(file)
    assert pyglet.font.have_font("Action Man") == True
    myfont = pyglet.font.load("Action Man", size=12, dpi=96)
    assert myfont.name == "Action Man"


def test_load_privatefont_from_list(test_window, test_data):
    file = test_data.get_file('fonts', 'action_man.ttf')
    pyglet.font.add_file(file)
    assert pyglet.font.have_font("Action Man") == True

    # First font in the list should be returned:
    myfont = pyglet.font.load(["Action Man", "Arial"], size=12, dpi=96)
    assert myfont.name == "Action Man"

    # List should resolve to actual font name, overwriting from test_load_no_custom_from_list
    assert pyglet.font.manager.get_resolved_name(["Action Man", "Arial"]) == "Action Man"


# Not sure how to properly test a dispatched event, but this seems to work.
def test_font_load_callback(test_data):
    @pyglet.font.manager.event
    def on_font_loaded(family_name: str, weight: str, style: str, stretch: str) -> None:
        assert family_name == "Action Man"
        assert weight == "bold"
        assert style == "normal"
        assert stretch == "normal"

        pyglet.font.manager.pop_handlers()

    file = test_data.get_file('fonts', 'action_man_bold.ttf')
    pyglet.font.add_file(file)

def test_font_range_group_routes_ranges_and_measures_text(test_window, test_data):
    pyglet.font.add_file(test_data.get_file("fonts", "action_man.ttf"))
    default_family = pyglet.font.manager.get_platform_default_name()
    group = pyglet.font.FontRangeGroup("font-group-638593")
    group.add("Action Man", "A", "M")
    group.add(default_family, "N", "Z")
    pyglet.font.add_group(group)

    font = pyglet.font.load(group.name, size=12, dpi=96)
    assert pyglet.font.load(group.name, size=12, dpi=96) is font
    assert font.name.startswith(group.name)

    glyphs, _ = font.get_glyphs("AN?", shaping=False)
    action_font = font._child_cache["Action Man"]  # noqa: SLF001
    default_font = font._child_cache[default_family]  # noqa: SLF001
    assert glyphs[0] is action_font.get_glyphs("A", shaping=False)[0][0]
    assert glyphs[1] is default_font.get_glyphs("N", shaping=False)[0][0]
    assert glyphs[2] is action_font.get_glyphs("?", shaping=False)[0][0]

    width, height = font.get_text_size("AN?")
    action_a_width, action_a_height = action_font.get_text_size("A")
    action_fallback_width, action_fallback_height = action_font.get_text_size("?")
    default_width, default_height = default_font.get_text_size("N")
    assert width == action_a_width + default_width + action_fallback_width
    assert height == max(action_a_height, default_height, action_fallback_height)


def test_font_group_uses_ordered_character_fallback(test_window):
    image = pyglet.image.ImageData(1, 1, "RGBA", b"\xff\xff\xff\xff")
    primary = pyglet.font.user.UserDefinedMappingFont(
        "font-group-primary-638593", default_char="A", size=12, mappings={"A": image},
    )
    fallback = pyglet.font.user.UserDefinedMappingFont(
        "font-group-fallback-638593", default_char="B", size=12, mappings={"B": image},
    )
    pyglet.font.add_user_font(primary)
    pyglet.font.add_user_font(fallback)

    group = pyglet.font.FontGroup("font-group-ordered-638593")
    group.add(primary.name).add(fallback.name)
    pyglet.font.add_group(group)

    font = pyglet.font.load(group.name, size=12, dpi=96)
    glyphs, _ = font.get_glyphs("AB", shaping=False)

    assert font.has_character("A")
    assert font.has_character("B")
    assert not font.has_character("C")
    assert glyphs[0] is font._child_cache[primary.name].get_glyphs("A", shaping=False)[0][0]  # noqa: SLF001
    assert glyphs[1] is font._child_cache[fallback.name].get_glyphs("B", shaping=False)[0][0]  # noqa: SLF001


def test_font_group_measures_consecutive_clusters_as_one_font_run(monkeypatch):
    class FakeFont:
        ascent = 10
        descent = -2

        def __init__(self) -> None:
            self.measured_runs = []

        def has_character(self, character: str) -> bool:
            return True

        def get_text_size(self, text: str) -> tuple[int, int]:
            self.measured_runs.append(text)
            # This deliberately differs from measuring the characters one at
            # a time, as kerning and shaped text often do.
            return (15 if text == "AV" else len(text) * 10, 12)

    child_font = FakeFont()
    monkeypatch.setattr(pyglet.font, "load", lambda *args, **kwargs: child_font)

    group = pyglet.font.FontGroup("font-group-measure-runs-638593")
    group.add("fake-family")
    font = group.get_font(12)

    assert font.get_text_size("AV") == (15, 12)
    assert child_font.measured_runs == ["AV"]

def test_user_font(test_window, test_data):
    bitmap_image = test_data.get_file('fonts', 'action_man_atlas.png')

    atlas_image = pyglet.image.load(bitmap_image)

    # You can use whatever method you want, but you just need to map your ImageData instances to the character
    atlas_characters = """ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789,.: '"/?!@#$%^&*()"""
    rows = 5
    columns = 16

    # Create image grid based on how many glyphs.
    grid = pyglet.image.ImageGrid(atlas_image, rows=rows, columns=columns)

    # Map characters to image data. A -> ImageData
    # The mapping can be a dictionary lookup, or it can be an object that behaves like a dictionary.
    mapping = {}
    char = 0
    for row in range(rows):
        for column in range(columns):
            y_prime = (rows - 1) - row
            new_index = column + y_prime * columns
            # This chooses values based on the top left. Pyglet uses bottom left indexing.
            glyph = grid[new_index]
            mapping[atlas_characters[char]] = glyph
            char += 1

    class ActionManMappedFont(pyglet.font.user.UserDefinedMappingFont):
        glyph_fit = len(atlas_characters)


    action_man_font = ActionManMappedFont("custom_action_man1",  # Custom unique name to not clash with others.
                                          default_char=" ",  # Default character to use if a character is not mapped.
                                          size=13,  # The size you want your font to be considered at base size.
                                          mappings=mapping)  # The mapping object containing your character -> glyphs.

    pyglet.font.add_user_font(action_man_font)

    assert pyglet.font.have_font("custom_action_man1") is True
    assert action_man_font.name == "custom_action_man1"
    assert action_man_font.size == 13
    assert action_man_font.mappings.get("a") is not None
    assert isinstance(action_man_font.mappings.get("a"), pyglet.image.ImageDataRegion)
    result = action_man_font.get_glyphs("ABC", False)
    assert len(result) == 2  # Should be a tuple of Glyph, GlyphPosition
    assert isinstance(result[0][0], pyglet.font.base.Glyph)
    assert isinstance(result[1][0], pyglet.font.base.GlyphPosition)
    width, height = action_man_font.get_text_size("ABC")
    assert width > 0
    assert height > 0

@pytest.mark.skipif(not harfbuzz_available(), reason="HarfBuzz library is unavailable.")
def test_load_privatefont_harfbuzz_integration(test_window, test_data):
    previous_shaping = pyglet.options.text_shaping
    file = test_data.get_file('fonts', 'action_man.ttf')

    try:
        # Ensure the next load path creates a fresh Font with HarfBuzz resources.
        pyglet.font.manager._invalidate()
        pyglet.options.text_shaping = "harfbuzz"

        pyglet.font.add_file(file)
        myfont = pyglet.font.load("Action Man", size=12, dpi=96)

        assert myfont.hb_resource is not None

        glyphs, offsets = myfont.get_glyphs("test", True)
        assert len(glyphs) == len(offsets)
        assert len(glyphs) > 0
    finally:
        pyglet.font.manager._invalidate()
        pyglet.options.text_shaping = previous_shaping
