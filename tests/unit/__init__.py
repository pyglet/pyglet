from unittest import mock


def get_fake_shader_program(*args, **kwargs):
    """
    Return a mock instead of creating a real shader & GL context.

    By default, batchable objects create or re-use a default shader
    program. Creating this also creates a GL context, which risks unit
    tests failing due to requiring an outside resource.

    To keep unit tests pure, this function should be used to monkeypatch
    methods that return a shader program during unit tests.

    This will often be a `get_default_shader` method found at the top of
    a module. When testing a module, you can turn off GL context creation
    near the top of the file as follows::

        # At the end of the imports section. You may need to change the
        # relative import to account for nesting of test folders.
        from . import get_fake_shader_program

        pyglet.shapes.get_default_shader = get_fake_shader_program


    :return: A mock shader that doesn't do anything
    """
    return mock.MagicMock()
