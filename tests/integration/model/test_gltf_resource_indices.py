"""Zero is a valid reference to the first glTF image buffer view or sampler."""
import io
import json
import struct

import pytest

import pyglet
from pyglet.enums import AddressMode
from pyglet.image import ImageData
from pyglet.image.codecs.png import PNGImageEncoder
from pyglet.model.codecs.gltf import Image, load_gltf


PIXELS = bytes((255, 0, 0, 255, 0, 255, 0, 255))


def make_glb(tmp_path, monkeypatch, view_index, sampler_index=1, prefix_size=0):
    stream = io.BytesIO()
    ImageData(2, 1, 'RGBA', PIXELS).save('texture.png', file=stream, encoder=PNGImageEncoder())
    png = stream.getvalue()
    image_bytes = b'\0' * prefix_size + png
    image_bytes += b'\0' * (-len(image_bytes) % 4)
    positions = struct.pack('<9f', 0, 0, 0, 1, 0, 0, 0, 1, 0)
    binary = image_bytes + positions
    image_view = {'buffer': 0, 'byteOffset': prefix_size, 'byteLength': len(png)}
    vertex_view = {'buffer': 0, 'byteOffset': len(image_bytes), 'byteLength': len(positions), 'target': 34962}
    views = [image_view, vertex_view] if view_index == 0 else [vertex_view, image_view]
    texture = {'source': 0}
    if sampler_index is not None:
        texture['sampler'] = sampler_index
    data = {
        'asset': {'version': '2.0'},
        'buffers': [{'byteLength': len(binary)}],
        'bufferViews': views,
        'accessors': [{'bufferView': 1 - view_index, 'componentType': 5126, 'count': 3,
                       'type': 'VEC3', 'min': [0, 0, 0], 'max': [1, 1, 0]}],
        'images': [{'bufferView': view_index, 'mimeType': 'image/png'}],
        'samplers': [{'minFilter': 9728, 'magFilter': 9728, 'wrapS': 33071, 'wrapT': 33648},
                     {'minFilter': 9729, 'magFilter': 9729, 'wrapS': 10497, 'wrapT': 33071}],
        'textures': [texture],
        'materials': [{'pbrMetallicRoughness': {'baseColorTexture': {'index': 0}}}],
        'meshes': [{'primitives': [{'attributes': {'POSITION': 0}, 'material': 0}]}],
        'nodes': [{'mesh': 0}], 'scenes': [{'nodes': [0]}], 'scene': 0,
    }
    metadata = json.dumps(data).encode()
    metadata += b' ' * (-len(metadata) % 4)
    chunks = struct.pack('<I4s', len(metadata), b'JSON') + metadata + struct.pack('<I4s', len(binary), b'BIN\0') + binary
    (tmp_path / 'triangle.glb').write_bytes(struct.pack('<4sII', b'glTF', 2, 12 + len(chunks)) + chunks)
    loader = pyglet.resource.Loader([str(tmp_path)])
    monkeypatch.setattr(pyglet.resource, 'file', loader.file)
    return load_gltf('triangle.glb')


@pytest.mark.parametrize('view_index', [0, 1])
@pytest.mark.parametrize('prefix_size', [0, 8])
def test_embedded_png_from_first_or_later_buffer_view(tmp_path, monkeypatch, view_index, prefix_size):
    model = make_glb(tmp_path, monkeypatch, view_index, prefix_size=prefix_size)
    image = model.images[0].read()
    assert (image.width, image.height) == (2, 1)
    assert bytes(image.get_image_data().get_bytes('RGBA', 8)) == PIXELS
    assert model.images[0].buffer_view is model.buffer_views[view_index]
    assert model.scenes[0].nodes[0].mesh is model.meshes[0]


@pytest.mark.parametrize('sampler_index', [0, 1, None])
def test_texture_selects_declared_sampler_or_default(tmp_path, monkeypatch, sampler_index):
    model = make_glb(tmp_path, monkeypatch, 1, sampler_index)
    texture = model.textures[0]
    if sampler_index is None:
        assert (texture.min_filter, texture.mag_filter) == (None, None)
        assert (texture.wrap_s, texture.wrap_t) == (AddressMode.REPEAT, AddressMode.REPEAT)
    else:
        assert texture.sampler is model.samplers[sampler_index]
        expected = (9728, 9728, 33071, 33648) if sampler_index == 0 else (9729, 9729, 10497, 33071)
        assert (texture.min_filter, texture.mag_filter, texture.wrap_s, texture.wrap_t) == expected


def test_uri_image_has_no_buffer_view():
    from types import SimpleNamespace

    image = Image({'uri': 'texture.png'}, SimpleNamespace(buffer_views=[]))
    assert image.buffer_view is None
    assert image.uri == 'texture.png'
