"""Image regions must crop logical rows before converting their output pitch."""
import pickle

import pytest

from pyglet.image import ImageData


def source_image(sign, padding):
    rows = [bytes(channel for x in range(4) for channel in (10 * y + x, 50 + x, 100 + y, 255))
            for y in range(5)]
    stored = [row + b'\xee' * padding for row in rows]
    if sign < 0:
        stored.reverse()
    return ImageData(4, 5, 'RGBA', b''.join(stored), sign * (16 + padding)), rows


@pytest.mark.parametrize('sign', [1, -1])
@pytest.mark.parametrize('padding', [0, 4])
@pytest.mark.parametrize('y', [0, 2, 4])
@pytest.mark.parametrize('output_sign', [1, -1])
def test_crop_logical_rows(sign, padding, y, output_sign):
    image, rows = source_image(sign, padding)
    region = image.get_region(1, y, 2, 1)
    expected = rows[y][4:12]
    assert bytes(region.get_bytes('RGBA', output_sign * 8)) == expected
    assert bytes(region.get_bytes('RGBA', 8)) == expected
    assert bytes(image.get_bytes('RGBA', 16)) == b''.join(rows)


@pytest.mark.parametrize('materialize_parent', [False, True])
@pytest.mark.parametrize('output_sign', [1, -1])
def test_nested_regions_and_format_conversion(materialize_parent, output_sign):
    image, rows = source_image(-1, 4)
    parent = image.get_region(1, 1, 3, 4)
    child = parent.get_region(1, 1, 2, 2)
    if materialize_parent:
        parent.get_bytes('RGBA', 12)
    expected = [b''.join(row[i + 2:i + 3] + row[i + 1:i + 2] + row[i:i + 1]
                        for i in (8, 12)) for row in rows[2:4]]
    if output_sign < 0:
        expected.reverse()
    assert bytes(child.get_bytes('BGR', output_sign * 6)) == b''.join(expected)


def test_set_bytes_replaces_source_coordinates_and_height():
    image, _ = source_image(-1, 4)
    region = image.get_region(1, 2, 2, 2)
    region.set_bytes('R', -2, b'\x03\x04\x01\x02')
    assert bytes(region.get_bytes('R', 2)) == b'\x01\x02\x03\x04'
    assert bytes(region.get_region(0, 1, 2, 1).get_bytes('R', 2)) == b'\x03\x04'


def test_pickled_region_uses_cropped_buffer():
    image, rows = source_image(-1, 4)
    region = pickle.loads(pickle.dumps(image.get_region(1, 1, 2, 3)))
    expected = b''.join(row[4:12] for row in rows[1:4])
    assert bytes(region.get_bytes('RGBA', 8)) == expected
    assert bytes(region.get_region(0, 2, 2, 1).get_bytes('RGBA', 8)) == rows[3][4:12]


def test_region_png_round_trip(tmp_path):
    from pyglet import image as image_module
    from pyglet.image.codecs.png import PNGImageEncoder

    image, rows = source_image(-1, 4)
    region = image.get_region(1, 1, 2, 3)
    path = tmp_path / 'crop.png'
    with path.open('wb') as stream:
        region.save(str(path), file=stream, encoder=PNGImageEncoder())
    reloaded = image_module.load(str(path))
    assert (reloaded.width, reloaded.height) == (2, 3)
    assert bytes(reloaded.get_image_data().get_bytes('RGBA', 8)) == b''.join(row[4:12] for row in rows[1:4])
