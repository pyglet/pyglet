import pytest

import pyglet

from pyglet import resource
from pyglet.gl import GL_NEAREST


# Test image is laid out
#  M R
#  B G
# In this test the image is sampled at four points from top-right clockwise:
#  R G B M (red, green, blue, magenta)

@pytest.mark.parametrize('transforms,result', [
    (dict(), 'rgbm'),
    (dict(flip_x=True), 'mbgr'),
    (dict(flip_y=True), 'grmb'),
    (dict(flip_x=True, flip_y=True), 'bmrg'),
    (dict(rotate=90), 'mrgb'),
    (dict(rotate=-270), 'mrgb'),
    (dict(rotate=180), 'bmrg'),
    (dict(rotate=-180), 'bmrg'),
    (dict(rotate=270), 'gbmr'),
    (dict(rotate=-90), 'gbmr'),
])
def test_resource_image_loading(event_loop, transforms, result):
    """Test loading an image resource with possible transformations."""
    resource.path.append('@' + __name__)
    resource.reindex()

    img = resource.image('rgbm.png', **transforms)

    window = event_loop.create_window()

    # Create a Framebuffer to render into:
    framebuffer = pyglet.image.buffer.Framebuffer()
    texture = pyglet.image.Texture.create(width=10, height=10, min_filter=GL_NEAREST, mag_filter=GL_NEAREST)
    framebuffer.attach_texture(texture)

    # Draw into the Framebuffer:
    framebuffer.bind()
    img.blit(img.anchor_x, img.anchor_y)
    framebuffer.unbind()

    # Check the pixels that were drawn:
    image_data = texture.get_image_data()
    pixels = image_data.get_data('RGBA', image_data.width * 4)

    def sample(x, y):
        i = y * image_data.pitch + x * len(image_data.format)
        r, g, b, _ = pixels[i:i + len(image_data.format)]
        if type(r) is str:
            r, g, b = list(map(ord, (r, g, b)))
        return {(255, 0, 0): 'r',
                (0, 255, 0): 'g',
                (0, 0, 255): 'b',
                (255, 0, 255): 'm'}.get((r, g, b), 'x')

    samples = ''.join([sample(3, 3), sample(3, 0), sample(0, 0), sample(0, 3)])

    if samples == samples[2] * 4:
        # On retina displays the image buffer is twice the size of the coordinate system
        samples = ''.join([sample(6, 6), sample(6, 0), sample(0, 0), sample(0, 6)])

    assert samples == result
