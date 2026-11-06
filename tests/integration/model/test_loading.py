import base64
import io
import json
import struct
import os
from types import SimpleNamespace

import pytest
import pyglet

from pyglet.util import DecodeException
from pyglet.math import Vec4
from pyglet.enums import AddressMode
from pyglet.image import ImageData
from pyglet.image.codecs.png import PNGImageEncoder
from pyglet.model.codecs import ModelDecodeException
from pyglet.model.codecs.gltf import GLTFModelDecoder, Image, load_gltf

test_data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))


def get_test_data_file(path, file_name):
    """Get a file from the test data directory in an OS independent way.

    Supply relative file name as you would in os.path.join().
    """
    return os.path.join(test_data_path, path, file_name)


@pytest.mark.parametrize('uri', ['data.bin', 'database.bin', 'data', 'data-geometry.bin', 'data+mesh.bin',
                                 'mesh.bin', 'data:', 'DATA:'])
def test_buffer_filenames_are_not_data_uris(tmp_path, monkeypatch, uri):
    binary = struct.pack('<9f', 0, 0, 0, 1, 0, 0, 0, 1, 0)
    if uri in ('data:', 'DATA:'):
        uri += 'application/octet-stream;base64,' + base64.b64encode(binary).decode()
    else:
        (tmp_path / uri).write_bytes(binary)
    loader = pyglet.resource.Loader([str(tmp_path)])
    monkeypatch.setattr(pyglet.resource, 'file', loader.file)
    data = {
        'asset': {'version': '2.0'},
        'buffers': [{'byteLength': len(binary), 'uri': uri}],
        'bufferViews': [{'buffer': 0, 'byteLength': len(binary)}],
        'accessors': [{'bufferView': 0, 'componentType': 5126, 'count': 3, 'type': 'VEC3', 'min': [0, 0, 0], 'max': [1, 1, 0]}],
        'meshes': [{'primitives': [{'attributes': {'POSITION': 0}}]}],
        'nodes': [{'mesh': 0}], 'scenes': [{'nodes': [0]}], 'scene': 0,
    }
    scene = pyglet.model.load('triangle.gltf', io.StringIO(json.dumps(data)))
    primitive = scene.nodes[0].mesh.primitives[0]
    assert list(primitive.attributes[0].array) == [0, 0, 0, 1, 0, 0, 0, 1, 0]
    assert primitive.count == 3


def test_load_from_disk():
    file_path = get_test_data_file('models', 'logo3d.obj')
    scene = pyglet.model.load(file_path)
    assert isinstance(scene, pyglet.model.Scene)


def test_load_from_object_str():
    file_path = get_test_data_file('models', 'logo3d.obj')
    with open(file_path, 'r') as f:
        file_obj = io.StringIO(f.read())
    scene = pyglet.model.load(file_path, file=file_obj)
    assert isinstance(scene, pyglet.model.Scene)


def test_load_from_object_bytes():
    file_path = get_test_data_file('models', 'logo3d.obj')
    with open(file_path, 'rb') as f:
        file_obj = io.BytesIO(f.read())
    scene = pyglet.model.load(file_path, file=file_obj)
    assert isinstance(scene, pyglet.model.Scene)


def test_no_decoders_available():
    # This is NOT a valid model file:
    file_path = get_test_data_file('media', 'alert.wav')

    with pytest.raises(DecodeException) as e:
        scene = pyglet.model.load(file_path)


def test_resource_module():
    folder_path = os.path.join(test_data_path, 'models')
    pyglet.resource.path.append(folder_path)
    pyglet.resource.reindex()

    scene = pyglet.resource.scene('logo3d.obj')
    assert isinstance(scene, pyglet.model.Scene)


@pytest.mark.parametrize('selected', [None, 0, 1, 2])
@pytest.mark.parametrize('explicit_decoder', [False, True])
def test_loads_declared_scene(selected, explicit_decoder):
    binary = struct.pack('<9f', 0, 0, 0, 1, 0, 0, 0, 1, 0)
    data = {
        'asset': {'version': '2.0'},
        'buffers': [{'byteLength': len(binary), 'uri': 'data:application/octet-stream;base64,' + base64.b64encode(binary).decode()}],
        'bufferViews': [{'buffer': 0, 'byteLength': len(binary)}],
        'accessors': [{'bufferView': 0, 'componentType': 5126, 'count': 3, 'type': 'VEC3', 'min': [0, 0, 0], 'max': [1, 1, 0]}],
        'meshes': [{'primitives': [{'attributes': {'POSITION': 0}}]}],
        'nodes': [{'name': f'node{i}', 'mesh': 0, 'translation': [10 * i, 0, 0]} for i in range(3)],
        'scenes': [{'name': f'scene{i}', 'nodes': [i]} for i in range(3)],
    }
    if selected is not None:
        data['scene'] = selected
    expected = selected or 0
    decoder = GLTFModelDecoder() if explicit_decoder else None
    scene = pyglet.model.load('scenes.gltf', io.StringIO(json.dumps(data)), decoder=decoder)
    assert scene.name == f'scene{expected}'
    assert len(scene.nodes) == 1
    assert scene.nodes[0].name == f'node{expected}'
    vertex = scene.nodes[0].mesh.primitives[0].attributes[0].array[3:6]
    transformed = scene.nodes[0].global_transform @ Vec4(*vertex, 1)
    assert tuple(transformed) == (10 * expected + 1, 0, 0, 1)


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
    image = Image({'uri': 'texture.png'}, SimpleNamespace(buffer_views=[]))
    assert image.buffer_view is None
    assert image.uri == 'texture.png'


def load_triangle(material):
    binary = struct.pack('<9f', 0, 0, 0, 1, 0, 0, 0, 1, 0)
    data = {
        'asset': {'version': '2.0'},
        'buffers': [{'byteLength': len(binary), 'uri': 'data:application/octet-stream;base64,' + base64.b64encode(binary).decode()}],
        'bufferViews': [{'buffer': 0, 'byteLength': len(binary)}],
        'accessors': [{'bufferView': 0, 'componentType': 5126, 'count': 3, 'type': 'VEC3', 'min': [0, 0, 0], 'max': [1, 1, 0]}],
        'materials': [material],
        'meshes': [{'primitives': [{'attributes': {'POSITION': 0}, 'material': 0}]}],
        'nodes': [{'mesh': 0}], 'scenes': [{'nodes': [0]}], 'scene': 0,
    }
    return load_gltf('triangle.gltf', io.StringIO(json.dumps(data)))


@pytest.mark.parametrize('properties', [
    {}, {'name': 'Default material'}, {'doubleSided': True},
    {'alphaMode': 'BLEND', 'emissiveFactor': [0.1, 0.2, 0.3]},
    {'extensions': {'VENDOR_material': {'value': 1}}, 'extras': {'note': 'kept'}},
    {'pbrMetallicRoughness': {}},
])
def test_optional_metallic_roughness_defaults(properties):
    model = load_triangle(properties)
    material = model.materials[0]
    assert tuple(material.base_color_factor) == (1, 1, 1, 1)
    assert material.metalic_factor == 1
    assert material.roughness_factor == 1
    assert material.base_color_texture is None
    assert material.metallic_roughness_texture is None
    assert model.meshes[0].primitives[0].material is material
    assert list(model.meshes[0].primitives[0].attributes[0].array) == [0, 0, 0, 1, 0, 0, 0, 1, 0]
    assert material.double_sided is properties.get('doubleSided', False)
    assert material.extensions == properties.get('extensions')
    assert material.extras == properties.get('extras')


def test_explicit_metallic_roughness_values_are_preserved():
    material = load_triangle({'pbrMetallicRoughness': {
        'baseColorFactor': [0.1, 0.2, 0.3, 0.4], 'metallicFactor': 0.25, 'roughnessFactor': 0.75,
    }}).materials[0]
    assert material.base_color_factor == [0.1, 0.2, 0.3, 0.4]
    assert material.metalic_factor == 0.25
    assert material.roughness_factor == 0.75


def triangle_data(binary_buffer):
    binary = struct.pack('<9f', 0, 0, 0, 1, 0, 0, 0, 1, 0)
    buffer = {'byteLength': len(binary)}
    if not binary_buffer:
        buffer['uri'] = 'data:application/octet-stream;base64,' + base64.b64encode(binary).decode()
    data = {
        'asset': {'version': '2.0'}, 'buffers': [buffer],
        'bufferViews': [{'buffer': 0, 'byteLength': len(binary)}],
        'accessors': [{'bufferView': 0, 'componentType': 5126, 'count': 3, 'type': 'VEC3', 'min': [0, 0, 0], 'max': [1, 1, 0]}],
        'meshes': [{'primitives': [{'attributes': {'POSITION': 0}}]}],
        'nodes': [{'name': 'triangle', 'mesh': 0}], 'scenes': [{'nodes': [0]}], 'scene': 0,
    }
    metadata = json.dumps(data).encode()
    if not binary_buffer:
        return metadata
    metadata += b' ' * (-len(metadata) % 4)
    chunks = struct.pack('<I4s', len(metadata), b'JSON') + metadata + struct.pack('<I4s', len(binary), b'BIN\0') + binary
    return struct.pack('<4sII', b'glTF', 2, 12 + len(chunks)) + chunks


@pytest.mark.parametrize(('extension', 'text_stream'), [('glb', False), ('GLB', False), ('gltf', False), ('gltf', True)])
def test_public_model_load_uses_borrowed_stream(extension, text_stream):
    payload = triangle_data(extension.lower() == 'glb')
    stream = io.StringIO(payload.decode()) if text_stream else io.BytesIO(payload)
    scene = pyglet.model.load('not-a-file.' + extension, stream, decoder=GLTFModelDecoder())
    assert not stream.closed
    assert scene.nodes[0].name == 'triangle'
    assert list(scene.nodes[0].mesh.primitives[0].attributes[0].array) == [0, 0, 0, 1, 0, 0, 0, 1, 0]


@pytest.mark.parametrize('extension', ['glb', 'gltf'])
@pytest.mark.parametrize('invalid', [False, True])
def test_owned_resource_is_opened_once_and_closed(monkeypatch, extension, invalid):
    payload = b'BAD!' if invalid and extension == 'glb' else b'{' if invalid else triangle_data(extension == 'glb')
    stream = io.BytesIO(payload) if extension == 'glb' else io.StringIO(payload.decode())
    calls = []

    def open_resource(name, mode):
        calls.append((name, mode))
        return stream

    monkeypatch.setattr(pyglet.resource, 'file', open_resource)
    if invalid:
        with pytest.raises(ModelDecodeException):
            load_gltf('triangle.' + extension)
    else:
        model = load_gltf('triangle.' + extension)
        assert model.nodes[0].name == 'triangle'
    assert calls == [('triangle.' + extension, 'rb' if extension == 'glb' else 'r')]
    assert stream.closed


def test_invalid_borrowed_json_is_left_open():
    stream = io.StringIO('{')
    with pytest.raises(ModelDecodeException):
        load_gltf('bad.gltf', stream)
    assert not stream.closed


@pytest.mark.parametrize('with_nodes', [False, True])
@pytest.mark.parametrize('from_stream', [False, True])
def test_loads_scenes_without_geometry(tmp_path, monkeypatch, with_nodes, from_stream):
    data = {'asset': {'version': '2.0'}, 'scenes': [{'name': 'layout'}]}
    if with_nodes:
        data['nodes'] = [
            {'name': 'root', 'translation': [1, 2, 3], 'children': [1]},
            {'name': 'child', 'translation': [4, 5, 6]},
        ]
        data['scenes'][0]['nodes'] = [0]
    text = json.dumps(data)
    (tmp_path / 'layout.gltf').write_text(text)
    loader = pyglet.resource.Loader([str(tmp_path)])
    monkeypatch.setattr(pyglet.resource, 'file', loader.file)
    stream = io.StringIO(text) if from_stream else None
    scene = pyglet.model.load('layout.gltf', stream)
    assert scene.name == 'layout'
    if with_nodes:
        root, = scene.nodes
        child, = root.children
        assert root.name == 'root'
        assert child.name == 'child'
        assert root.mesh is None
        assert child.mesh is None
        assert tuple(child.global_transform @ Vec4(0, 0, 0, 1)) == (5, 7, 9, 1)
    else:
        assert scene.nodes == []
    if stream is not None:
        assert not stream.closed
