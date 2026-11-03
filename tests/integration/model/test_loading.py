import base64
import io
import json
import struct
import os

import pytest
import pyglet

from pyglet.util import DecodeException

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
