import pytest

from pyglet import resource
from tests.annotations import skip_graphics_api, GraphicsAPI

# GLES backends are currently failing on glTexSubImage2D
pytestmark = [skip_graphics_api(GraphicsAPI.GLES)]


@pytest.mark.parametrize('transforms,tex_order', [
    (dict(), (0, 1, 2, 3)),
    (dict(flip_x=True), (1, 0, 3, 2)),
    (dict(flip_y=True), (3, 2, 1, 0)),
    (dict(flip_x=True, flip_y=True), (2, 3, 0, 1)),
    (dict(rotate=90), (1, 2, 3, 0)),
    (dict(rotate=-270), (1, 2, 3, 0)),
    (dict(rotate=180), (2, 3, 0, 1)),
    (dict(rotate=-180), (2, 3, 0, 1)),
    (dict(rotate=270), (3, 0, 1, 2)),
    (dict(rotate=-90), (3, 0, 1, 2)),
])
def test_resource_texture_loading(gl3_context, event_loop, transforms, tex_order):
    """Test loading an image resource with possible transformations."""
    resource.path.append('@' + __name__)
    resource.reindex()

    tex = resource.texture('rgbm.png', **transforms)

    assert tex.tex_coords_order == tex_order, f"{transforms}, {tex.tex_coords_order} != {tex_order}"
