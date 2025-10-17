import pyglet
from tests.annotations import skip_platform, require_platform, Platform


def test_font_create_default(gl3_context, test_data):
    ft = pyglet.font.load()
    assert ft.name is not None


def test_default_platform_font():
    """Ensure the platform has a default font from the manager."""
    assert pyglet.font.manager.get_platform_default_name() is not None


def test_missing_font():
    assert not pyglet.font.have_font('definitely-doesnt-exist-font')


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

def test_load_privatefont(gl3_context, test_data):
    file = test_data.get_file('fonts', 'action_man.ttf')
    pyglet.font.add_file(file)
    assert pyglet.font.have_font("Action Man") == True
    myfont = pyglet.font.load("Action Man", size=12, dpi=96)
    assert myfont.name == "Action Man"


def test_load_privatefont_from_list(gl3_context, test_data):
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

@require_platform(Platform.WINDOWS)  # Same as above, but Linux runner uses DejaVu Sans.
def test_load_gdi(gl3_context, test_data):
    # Invalidate all font caches.
    pyglet.font.manager._invalidate()

    # Switch to GDI Font.
    pyglet.options.win32_gdi_font = True
    pyglet.font._system_font_class = pyglet.font._get_system_font_class()

    myfont = pyglet.font.load(["Action Man", "Segoe UI"], size=12, dpi=96)

    from pyglet.font.win32 import GDIPlusFont
    assert isinstance(myfont, GDIPlusFont)

    assert myfont.name == "Segoe UI"
    # Make sure name resolves to an actual found font.
    assert pyglet.font.manager.get_resolved_name(["Action Man", "Segoe UI"]) == 'Segoe UI'

    # Reset and cleanup again.
    pyglet.font.manager._invalidate()
    pyglet.options.win32_gdi_font = False
    pyglet.font._system_font_class = pyglet.font._get_system_font_class()

@require_platform(Platform.WINDOWS)  # Same as above, but Linux runner uses DejaVu Sans.
def test_load_no_custom_from_list_gdi(gl3_context, test_data):
    # Invalidate all font caches.
    pyglet.font.manager._invalidate()

    # Switch to GDI Font.
    pyglet.options.win32_gdi_font = True
    pyglet.font._system_font_class = pyglet.font._get_system_font_class()

    myfont = pyglet.font.load(["Action Man", "Segoe UI"], size=12, dpi=96)

    from pyglet.font.win32 import GDIPlusFont
    assert isinstance(myfont, GDIPlusFont)

    assert myfont.name == "Segoe UI"
    # Make sure name resolves to an actual found font.
    assert pyglet.font.manager.get_resolved_name(["Action Man", "Segoe UI"]) == 'Segoe UI'

    file = test_data.get_file('fonts', 'action_man.ttf')
    pyglet.font.add_file(file)
    assert pyglet.font.have_font("Action Man") == True

    # Reset and cleanup again.
    pyglet.font.manager._invalidate()
    pyglet.options.win32_gdi_font = False
    pyglet.font._system_font_class = pyglet.font._get_system_font_class()

def test_user_font(gl3_context, test_data):
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
