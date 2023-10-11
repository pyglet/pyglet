from typing import Tuple
from unittest import mock

from pytest import fixture


@fixture
def get_dummy_shader_program():
    """
    Provide a dummy getter to monkeypatch getters for default shaders.

    By default, batchable objects create or re-use a default shader
    program. This is usually done through a ``get_default_shader``
    function on their implementing module. If no GL context exists,
    calling that function creates one, which risks non-drawing tests
    failing or running slower than optimal.

    Avoid that by passing this fixture to local monkey patching fixtures
    in module-specific single test files or conftest.py instances for
    test modules::

        # Example from ./shapes/conftest.py

        @fixture(autouse=True)  # Force this to be used for every test in the module
        def monkeypatch_default_shape_shader(monkeypatch, get_dummy_shader_program):
            monkeypatch.setattr(
                'pyglet.shapes.get_default_shader',
                 get_dummy_shader_program)

    """
    # A named function instead of a lambda for clarity in debugger views.
    def _get_dummy_shader_program(*args, **kwargs):
        return mock.MagicMock()

    return _get_dummy_shader_program


# Color constants & fixtures for use with Shapes, UI elements, etc.
ORIGINAL_RGB_COLOR = 253, 254, 255
ORIGINAL_RGBA_COLOR = ORIGINAL_RGB_COLOR + (37,)
NEW_RGB_COLOR = 1, 2, 3
NEW_RGBA_COLOR = 5, 6, 7, 59


@fixture(scope="session")
def original_rgb_color():
    return ORIGINAL_RGB_COLOR


@fixture(scope="session")
def original_rgba_color():
    return ORIGINAL_RGBA_COLOR


@fixture(params=[ORIGINAL_RGB_COLOR, ORIGINAL_RGBA_COLOR])
def original_rgb_or_rgba_color(request):
    return request.param


def expected_alpha_for_color(color: Tuple[int, ...]):
    """
    Slow but readable color helper with validation.

    This uses more readable logic than the main library and will raise
    clear ValueErrors as part of validation.

    Args:
        color: An RGB or RGBA color

    Returns:

    """
    num_channels = len(color)

    if num_channels == 4:
        return color[3]
    elif num_channels == 3:
        return 255

    raise ValueError(
        f"Expected color tuple with 3 or 4 elements, but got {color!r}.")


@fixture
def original_rgb_or_rgba_expected_alpha(original_rgb_or_rgba_color):
    return expected_alpha_for_color(original_rgb_or_rgba_color)


@fixture(scope="session")
def new_rgb_color():
    return NEW_RGB_COLOR


@fixture(scope="session")
def new_rgba_color():
    return NEW_RGBA_COLOR


@fixture(params=[NEW_RGB_COLOR, NEW_RGBA_COLOR])
def new_rgb_or_rgba_color(request):
    return request.param


@fixture(params=[180, -180])
def new_nonzero_rotation(request) -> float:
    return request.param


def new_color_expected_alpha(new_rgb_or_rgba_color):
    return expected_alpha_for_color(new_rgb_or_rgba_color)


@fixture(params=[0, 128, 254])
def new_opacity_set_opacity_alone(request):
    return request.param

