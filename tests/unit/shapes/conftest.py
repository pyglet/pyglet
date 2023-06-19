from pytest import fixture


@fixture(autouse=True)
def monkeypatch_default_shape_shader(monkeypatch, get_dummy_shader_program):
    """Use a dummy shader when testing non-drawing functionality"""
    monkeypatch.setattr('pyglet.shapes.get_default_shader', get_dummy_shader_program)
