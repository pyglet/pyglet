from unittest import mock

import pytest


@pytest.fixture
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
