import pytest

from pyglet.gl import *
from pyglet import image
from pyglet import resource

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

    w = event_loop.create_window(width=10, height=10)
    @w.event
    def on_draw():
        # XXX For some reason original on_draw is not called
        w.clear()
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        img.blit(img.anchor_x, img.anchor_y)

        event_loop.interrupt_event_loop()

    # Need to force multiple draws for platforms that do not support immediate drawing
    event_loop.run_event_loop()
    w._legacy_invalid = True
    event_loop.run_event_loop()
    w._legacy_invalid = True
    event_loop.run_event_loop()

    image_data = image.get_buffer_manager().get_color_buffer().get_image_data()
    pixels = image_data.get_data('RGBA', image_data.width * 4)
    def sample(x, y):
        i = y * image_data.pitch + x * len(image_data.format)
        r, g, b, _ = pixels[i:i+len(image_data.format)]
        if type(r) is str:
            r, g, b = list(map(ord, (r, g, b)))
        return {
            (255, 0, 0): 'r',
            (0, 255, 0): 'g',
            (0, 0, 255): 'b',
            (255, 0, 255): 'm'}.get((r, g, b), 'x')

    samples = ''.join([
        sample(3, 3), sample(3, 0), sample(0, 0), sample(0, 3)])
    if samples == samples[2]*4:
        # On retina displays the image buffer is twice the size of the coordinate system
        samples = ''.join([
            sample(6, 6), sample(6, 0), sample(0, 0), sample(0, 6)])

    assert samples == result

