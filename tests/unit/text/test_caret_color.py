from collections import UserList
from unittest.mock import Mock, NonCallableMock

import pytest

from pyglet.graphics.shader import ShaderProgram
from pyglet.graphics.vertexdomain import IndexedVertexList
from pyglet.text import layout, caret


class ListSlicesAsTuple(UserList):
    """
    Mutable sequence which returns tuples when sliced like ctypes objects

    It makes tests cleaner by allowing direct comparison to color tuples and
    slices of them.
    """

    def __getitem__(self, item):
        if isinstance(item, slice):
            return tuple(super().__getitem__(item))
        return super().__getitem__(item)


@pytest.fixture(autouse=True)
def disable_automatic_caret_blinking(monkeypatch):
    monkeypatch.setattr(caret, 'clock', Mock(spec=caret.clock))


# Brittle tangle of mocks due to tightly coupled Caret/Layout design
@pytest.fixture
def mock_layout():

    # Create layout mock
    _layout = NonCallableMock(spec=layout.TextLayout)
    _layout.foreground_decoration_group = NonCallableMock()
    _layout.attach_mock(Mock(), 'push_handlers')

    # Create mock shader program for it
    program = NonCallableMock(spec=ShaderProgram)
    _layout.foreground_decoration_group.attach_mock(program, 'program')

    # Allow the shader program to create a mock vertex list on demand
    def _fake_vertex_list_method(count, mode, batch=None, group=None, colors=None):
        vertex_list = NonCallableMock(spec=IndexedVertexList)
        vertex_list.colors = ListSlicesAsTuple(colors[1])
        return vertex_list

    program.vertex_list = _fake_vertex_list_method

    return _layout


# Color fixtures are defined in pyglet's tests/unit/conftest.py
@pytest.fixture
def rgba_caret(mock_layout, original_rgba_color):
    return caret.Caret(layout=mock_layout, color=original_rgba_color)


@pytest.fixture
def rgb_caret(mock_layout, original_rgb_color):
    return caret.Caret(layout=mock_layout, color=original_rgb_color)


@pytest.fixture
def rgb_or_rgba_caret(mock_layout, original_rgb_or_rgba_color):
    return caret.Caret(layout=mock_layout, color=original_rgb_or_rgba_color)


def test_init_sets_opacity_to_255_when_rgb_color_argument(rgb_caret):
    assert rgb_caret.color[3] == 255


def test_init_sets_opacity_from_rgba_value_as_color_argument(rgba_caret):
    assert rgba_caret.color[3] == 37


def test_init_sets_rgb_channels_correctly(rgb_or_rgba_caret, original_rgb_or_rgba_color):
    assert rgb_or_rgba_caret.color[:3] == original_rgb_or_rgba_color[:3]
