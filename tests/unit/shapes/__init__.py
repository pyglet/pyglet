import pytest


@pytest.fixture(scope="module")
def new_rgb_color():
    return 1, 2, 3


@pytest.fixture(scope="module")
def new_rgba_color():
    return 5, 6, 7, 59


@pytest.fixture(scope="module", params=[(1, 2, 3), (5, 6, 7, 59)])
def new_rgb_or_rgba_color(request):
    return request.param
