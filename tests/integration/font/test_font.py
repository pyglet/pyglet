import pyglet
from tests.annotations import skip_platform, require_platform, Platform


def test_font_create_default(test_data):
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

def test_load_privatefont(test_data):
    file = test_data.get_file('fonts', 'action_man.ttf')
    pyglet.font.add_file(file)
    assert pyglet.font.have_font("Action Man") == True
    myfont = pyglet.font.load("Action Man", size=12, dpi=96)
    assert myfont.name == "Action Man"


def test_load_privatefont_from_list(test_data):
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
    def on_font_loaded(family_name: str, weight: str, italic: str, stretch: str) -> None:
        assert family_name == "Action Man"
        assert weight == "bold"
        assert italic == "normal"
        assert stretch == "normal"

    file = test_data.get_file('fonts', 'action_man_bold.ttf')
    pyglet.font.add_file(file)
