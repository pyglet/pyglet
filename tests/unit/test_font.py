"""
Test pyglet font package
"""

import pytest
import pyglet

def test_load_privatefont(test_data):

    pyglet.font.add_file(test_data.get_file('fonts', 'action_man.ttf'))
    action_man_font = pyglet.font.load("Action Man", size=12, dpi=96)
    assert action_man_font.logfont.lfFaceName.decode("utf-8") == "Action Man"


def test_load_privatefont_from_list(test_data):
    """Test for Issue #100"""

    pyglet.font.add_file(test_data.get_file('fonts', 'action_man.ttf'))
    action_man_font = pyglet.font.load(["Action Man"], size=12, dpi=96)
    assert action_man_font.logfont.lfFaceName.decode("utf-8") == "Action Man"