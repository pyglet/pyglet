from pytest import fixture


@fixture(autouse=True)
def monkeypatch_default_shape_shader(monkeypatch, get_dummy_shader_program):
    """Use a dummy shader when testing non-drawing functionality"""
    monkeypatch.setattr('pyglet.shapes.get_default_shader', get_dummy_shader_program)


@fixture(scope="module")
def new_rgb_color():
    return 1, 2, 3


@fixture(scope="module")
def new_rgba_color():
    return 5, 6, 7, 59


@fixture(scope="module", params=[(1, 2, 3), (5, 6, 7, 59)])
def new_rgb_or_rgba_color(request):
    return request.param
