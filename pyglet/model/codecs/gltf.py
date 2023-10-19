import json

from urllib.request import urlopen

import pyglet

from pyglet.gl import GL_BYTE, GL_UNSIGNED_BYTE, GL_SHORT, GL_UNSIGNED_SHORT, GL_FLOAT
from pyglet.gl import GL_UNSIGNED_INT, GL_ELEMENT_ARRAY_BUFFER, GL_ARRAY_BUFFER, GL_TRIANGLES

from . import ModelDecodeException, ModelDecoder


# struct module types
_struct_types = {
    GL_BYTE: 'b',
    GL_UNSIGNED_BYTE: 'B',
    GL_SHORT: 'h',
    GL_UNSIGNED_SHORT: 'H',
    GL_UNSIGNED_INT: 'I',
    GL_FLOAT: 'f',
}

# OpenGL type sizes
_component_sizes = {
    GL_BYTE: 1,
    GL_UNSIGNED_BYTE: 1,
    GL_SHORT: 2,
    GL_UNSIGNED_SHORT: 2,
    GL_UNSIGNED_INT: 4,
    GL_FLOAT: 4
}

_accessor_type_sizes = {
    "SCALAR": 1,
    "VEC2": 2,
    "VEC3": 3,
    "VEC4": 4,
    "MAT2": 4,
    "MAT3": 9,
    "MAT4": 16
}

_targets = {
    GL_ELEMENT_ARRAY_BUFFER: "element_array",
    GL_ARRAY_BUFFER: "array",
}


class Buffer:
    def __init__(self, data):
        self._length = data['byteLength']
        self._uri = data['uri']

        if self._uri.startswith('data'):
            self._response = urlopen(self._uri)
            self._file = self._response.file
        else:
            self._file = pyglet.resource.file(self._uri, 'rb')

    def read(self, offset, length):
        self._file.seek(offset)
        return self._file.read(length)

    def __del__(self):
        try:
            self._file.close()
        except AttributeError:
            pass

    def __repr__(self):
        return f"{self.__class__.__name__}(length={self._length})"


class BufferView:
    def __init__(self, data, owner):
        self.buffer_index = data.get('buffer')
        self.offset = data.get('byteOffset', 0)
        self.length = data.get('byteLength')
        self.target = data.get('target')
        self.stride = data.get('byteStride', 1)

        self.buffer = owner.buffers[self.buffer_index]

    def __repr__(self):
        return f"{self.__class__.__name__}(buffer={self.buffer_index})"


class Accessor:
    def __init__(self, data, owner):
        self.buffer_view_index = data.get('bufferView')
        self.byte_offset = data.get('byteOffset')
        self.component_type = data.get('componentType')
        self.count = data.get('count')
        self.type = data.get('type')
        self.max = data.get('max')
        self.min = data.get('min')

        self.buffer_view = owner.buffer_views[self.buffer_view_index]

    def __repr__(self):
        return f"{self.__class__.__name__}(buffer_view={self.buffer_view_index})"


class Attribute:
    def __init__(self, name, index):
        self.name = name
        self.index = index

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name}, index={self.index})"


class Primitive:
    def __init__(self, data, owner):
        self.attributes = {name: Attribute(name, index) for name, index in data.get('attributes').items()}
        self.indices = data.get('indices')

    def __repr__(self):
        return f"{self.__class__.__name__}(attributes={len(self.attributes)}, indices={self.indices})"


class Mesh:
    def __init__(self, data, owner):
        self.primitives = [Primitive(primitive_data, owner) for primitive_data in data.get('primitives')]

    def __repr__(self):
        return f"{self.__class__.__name__}(primitives={len(self.primitives)})"


class Node:
    def __init__(self, data):
        self.mesh = data.get('mesh')

    def __repr__(self):
        return f"{self.__class__.__name__}(mesh={self.mesh})"


class Scene:
    def __init__(self, data, owner):
        self.nodes = [owner.nodes[i] for i in data['nodes']]

    def __repr__(self):
        return f"{self.__class__.__name__}(nodes={self.nodes})"


class GLTF:
    def __init__(self, gltf_data: dict):
        self._gltf_data = gltf_data
        self.version = self._gltf_data['asset']['version']

        self.buffers = [Buffer(data=data) for data in gltf_data['buffers']]
        self.buffer_views = [BufferView(data=data, owner=self) for data in gltf_data['bufferViews']]
        self.accessors = [Accessor(data=data, owner=self) for data in gltf_data['accessors']]
        self.meshes = [Mesh(data=data, owner=self) for data in gltf_data['meshes']]
        self.nodes = [Node(data=data) for data in gltf_data['nodes']]

        self.scenes = [Scene(data=data, owner=self) for data in gltf_data['scenes']]
        self.default_scene = self.scenes[gltf_data['scene']]

    def __repr__(self):
        return f"{self.__class__.__name__}()"


def load_gltf(filename, file=None):

    if file is None:
        file = pyglet.resource.file(filename, 'r')
    elif file.mode != 'r':
        file.close()
        file = pyglet.resource.file(filename, 'r')

    try:
        gltf_data = json.load(file)
    except json.JSONDecodeError as e:
        raise ModelDecodeException(f"Json error. Does not appear to be a valid glTF file. {e}")
    finally:
        file.close()

    if 'asset' not in gltf_data:
        raise ModelDecodeException("Not a valid glTF file. Asset property not found.")
    else:
        if float(gltf_data['asset']['version']) < 2.0:
            raise ModelDecodeException('Only glTF 2.0+ models are supported')


    return GLTF(gltf_data=gltf_data)


###################################################
#   Decoder definitions start here:
###################################################

class GLTFModelDecoder(ModelDecoder):
    def get_file_extensions(self):
        return ['.gltf']

    def decode(self, filename, file, batch, group):
        pass


def get_decoders():
    return [GLTFModelDecoder()]


def get_encoders():
    return []
