from unittest import mock

import pytest
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


@fixture(scope="module")
def new_rgb_color():
    return 1, 2, 3


@fixture(scope="module")
def new_rgba_color():
    return 5, 6, 7, 59


@fixture(scope="module", params=[(1, 2, 3), (5, 6, 7, 59)])
def new_rgb_or_rgba_color(request):
    return request.param


@pytest.fixture(params=[(0, 0, 0), (0, 255, 0, 37)])
def original_color(request):
    return request.param
