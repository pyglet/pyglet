"""GLTF decoding must use supplied streams and close only files it opens."""
import base64
import io
import json
import struct

import pytest

import pyglet
from pyglet.model.codecs.gltf import GLTFModelDecoder, load_gltf


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


@pytest.mark.parametrize('extension,text_stream', [('glb', False), ('GLB', False), ('gltf', False), ('gltf', True)])
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
        from pyglet.model.codecs import ModelDecodeException
        with pytest.raises(ModelDecodeException):
            load_gltf('triangle.' + extension)
    else:
        model = load_gltf('triangle.' + extension)
        assert model.nodes[0].name == 'triangle'
    assert calls == [('triangle.' + extension, 'rb' if extension == 'glb' else 'r')]
    assert stream.closed


def test_invalid_borrowed_json_is_left_open():
    from pyglet.model.codecs import ModelDecodeException

    stream = io.StringIO('{')
    with pytest.raises(ModelDecodeException):
        load_gltf('bad.gltf', stream)
    assert not stream.closed
