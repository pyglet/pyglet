import io
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
