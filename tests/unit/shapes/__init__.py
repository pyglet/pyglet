from pytest import fixture


@fixture(scope="module")
def new_rgb_color():
    return 1, 2, 3


@fixture(scope="module")
def new_rgba_color():
    return 5, 6, 7, 59


@fixture(scope="module", params=[(1, 2, 3), (5, 6, 7, 59)])
def new_rgb_or_rgba_color(request):
    return request.param


__all__ = ['new_rgb_color', 'new_rgba_color', 'new_rgb_or_rgba_color']
