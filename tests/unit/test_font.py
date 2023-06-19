"""
Test pyglet font package
"""

import pyglet


def test_load_privatefont(test_data):
    file = test_data.get_file('fonts', 'action_man.ttf')
    pyglet.font.add_file(file)
    myfont = pyglet.font.load("Action Man", size=12, dpi=96)
    assert myfont.name == "Action Man"


def test_load_privatefont_from_list(test_data):
    file = test_data.get_file('fonts', 'action_man.ttf')
    pyglet.font.add_file(file)
    # First font in the list should be returned:
    myfont = pyglet.font.load(["Action Man", "Arial"], size=12, dpi=96)
    assert myfont.name == "Action Man"
