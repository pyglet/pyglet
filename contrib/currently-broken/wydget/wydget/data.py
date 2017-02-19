import os

from pyglet import image

_data = {}

filename = os.path.join
dirname = os.path.dirname(__file__)

def load_gui_image(filename):
    if not os.path.isabs(filename):
        filename = os.path.join(dirname, 'data', filename)
    return load_image(filename)

def load_image(*filename):
    filename = os.path.join(*filename)
    if filename not in _data:
        _data[filename] = image.load(filename)
    return _data[filename]

