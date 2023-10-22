import json

from array import array
from urllib.request import urlopen

import pyglet

from pyglet.gl import GL_BYTE, GL_UNSIGNED_BYTE, GL_SHORT, GL_UNSIGNED_SHORT, GL_FLOAT, GL_DOUBLE
from pyglet.gl import GL_INT, GL_UNSIGNED_INT, GL_ELEMENT_ARRAY_BUFFER, GL_ARRAY_BUFFER

from . import ModelDecodeException, ModelDecoder


_array_types = {
    GL_BYTE: 'b',
    GL_UNSIGNED_BYTE: 'B',
    GL_SHORT: 'h',
    GL_UNSIGNED_SHORT: 'H',
    GL_INT: 'l',
    GL_UNSIGNED_INT: 'L',
    GL_FLOAT: 'f',
    GL_DOUBLE: 'd',
}

_gl_type_sizes = {
    GL_BYTE: 1,
    GL_UNSIGNED_BYTE: 1,
    GL_SHORT: 2,
    GL_UNSIGNED_SHORT: 2,
    GL_INT: 4,
    GL_UNSIGNED_INT: 4,
    GL_FLOAT: 4,
    GL_DOUBLE: 8,
}

_accessor_type_counts = {
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
    """Abstraction over unstructured bytes."""
    def __init__(self, data):
        self.length = data['byteLength']
        self._uri = data['uri']

        if self._uri.startswith('data'):
            self._response = urlopen(self._uri)
            self._file = self._response.file
        else:
            self._file = pyglet.resource.file(self._uri, 'rb')

    def read(self, offset, byte_length) -> bytes:
        self._file.seek(offset)
        return self._file.read(byte_length)

    def __del__(self):
        try:
            self._file.close()
        except AttributeError:
            pass

    def __repr__(self):
        return f"{self.__class__.__name__}(length={self.length})"


class BufferView:
    """View over a section of a Buffer, with optional stride."""
    def __init__(self, data, owner):
        self._buffer_index = data.get('buffer')
        self._offset = data.get('byteOffset', 0)
        self.length = data.get('byteLength')
        self.stride = data.get('byteStride', 0)
        self.target = data.get('target')
        self.target_alias = _targets[self.target]

        self.buffer = owner.buffers[self._buffer_index]

    def read(self, offset: int, byte_length: int, count: int) -> bytes:
        offset = self._offset + offset
        bytestring = b""

        for _ in range(count):
            bytestring += self.buffer.read(offset, byte_length)
            offset += byte_length + self.stride

        return bytestring

    def __repr__(self):
        return f"{self.__class__.__name__}(buffer={self._buffer_index}, target={self.target_alias})"


class Accessor:
    def __init__(self, data, owner):
        self._buffer_view_index = data.get('bufferView')
        self.byte_offset = data.get('byteOffset')
        self.component_type = data.get('componentType')     # GL_FLOAT, GL_INT, etc
        self.type = data.get('type')                        # VEC3, MAT4, etc.
        self.count = data.get('count')                      # Number of self.type
        self.max = data.get('max')
        self.min = data.get('min')

        self._fmt = _array_types[self.component_type]

        # The size of the GL type * the size of the data type.
        # For example a GL_FLOAT is 4 bytes and a VEC3 has 3 values, so 4 * 3 = 12 bytes
        self._byte_length = _gl_type_sizes[self.component_type] * _accessor_type_counts[self.type]

        self.buffer_view = owner.buffer_views[self._buffer_view_index]

    def read(self) -> bytes:
        return self.buffer_view.read(self.byte_offset, self._byte_length, self.count)

    def as_array(self):
        return array(self._fmt, self.read())

    def __repr__(self):
        return f"{self.__class__.__name__}(buffer_view={self._buffer_view_index})"


class Attribute:
    def __init__(self, name, index, owner):
        self.name = name
        self._accessor_index = index
        self.accessor = owner.accessors[index]

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name}, accessor={self._accessor_index})"


class Primitive:
    def __init__(self, data, owner):
        self.attributes = {name: Attribute(name, index, owner) for name, index in data.get('attributes').items()}
        # TODO: point towards the right buffer/accessor:
        self.indices = data.get('indices')

    def __repr__(self):
        return f"{self.__class__.__name__}(attributes={len(self.attributes)}, indices={self.indices})"


class Mesh:
    def __init__(self, data, owner):
        self.primitives = [Primitive(primitive_data, owner) for primitive_data in data.get('primitives')]

    def __repr__(self):
        return f"{self.__class__.__name__}(primitives={len(self.primitives)})"


class Node:
    def __init__(self, data, owner):
        self._mesh_index = data.get('mesh')
        self.mesh = owner.meshes[self._mesh_index]

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
        self.nodes = [Node(data=data, owner=self) for data in gltf_data['nodes']]

        self.scenes = [Scene(data=data, owner=self) for data in gltf_data['scenes']]
        self.default_scene = self.scenes[gltf_data['scene']]

    def __repr__(self):
        return f"{self.__class__.__name__}(scenes={len(self.scenes)}, meshes={len(self.meshes)})"


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
