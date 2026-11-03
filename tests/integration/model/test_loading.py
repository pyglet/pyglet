import base64
import io
import json
import struct
import os

import pytest
import pyglet

from pyglet.util import DecodeException
from pyglet.math import Vec4
from pyglet.model.codecs.gltf import GLTFModelDecoder

test_data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))


def get_test_data_file(path, file_name):
    """Get a file from the test data directory in an OS independent way.

    Supply relative file name as you would in os.path.join().
    """
    return os.path.join(test_data_path, path, file_name)


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
    assert len(scene.nodes) == 1 and scene.nodes[0].name == f'node{expected}'
    vertex = scene.nodes[0].mesh.primitives[0].attributes[0].array[3:6]
    transformed = scene.nodes[0].global_transform @ Vec4(*vertex, 1)
    assert tuple(transformed) == (10 * expected + 1, 0, 0, 1)
