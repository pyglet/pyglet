import json

from array import array
from urllib.request import urlopen

import pyglet

from pyglet.gl import GL_BYTE, GL_UNSIGNED_BYTE, GL_SHORT, GL_UNSIGNED_SHORT, GL_FLOAT, GL_DOUBLE
from pyglet.gl import GL_INT, GL_UNSIGNED_INT, GL_ELEMENT_ARRAY_BUFFER, GL_ARRAY_BUFFER
from pyglet.gl import GL_REPEAT

from . import ModelDecodeException, ModelDecoder
from .base import Scene


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

    def read(self, offset, nbytes) -> bytes:
        self._file.seek(offset)
        return self._file.read(nbytes)

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
        self.buffer = owner.buffers[self._buffer_index]

        self.offset = data.get('byteOffset', 0)
        self.length = data.get('byteLength')
        self.stride = data.get('byteStride', 0)
        self.target = data.get('target')
        self.target_name = _targets[self.target]

    def read(self, read_offset: int, byte_length: int, count: int) -> bytes:
        offset = self.offset + read_offset
        bytestring = b""

        for _ in range(count):
            bytestring += self.buffer.read(offset, byte_length)
            offset += self.stride or byte_length

        return bytestring

    def __repr__(self):
        return f"{self.__class__.__name__}(buffer={self._buffer_index}, target={self.target_name})"


class Accessor:
    def __init__(self, data, owner):
        self._buffer_view_index = data.get('bufferView')
        self.buffer_view = owner.buffer_views[self._buffer_view_index]

        self.byte_offset = data.get('byteOffset')
        self.component_type = data.get('componentType')     # GL_FLOAT, GL_INT, etc
        self.type = data.get('type')                        # VEC3, MAT4, etc.
        self.count = data.get('count')                      # count of self.type
        self.max = data.get('max')
        self.min = data.get('min')

        # This is a 'sparse' accessor:
        self.sparse = data.get('sparse')
        if self.sparse:
            raise NotImplementedError("Not yet implmented")

        # The Python format type:
        self.fmt = _array_types[self.component_type]

        # The byte size of the `GL type` multiplied by the length of the GLSL `data type`.
        # For example: a GL_FLOAT is 4 bytes and a VEC3 has 3 values, so 4 * 3 = 12 bytes
        self._byte_length = _gl_type_sizes[self.component_type] * _accessor_type_counts[self.type]

    def read(self) -> bytes:
        return self.buffer_view.read(self.byte_offset, self._byte_length, self.count)
        # assert self._byte_length * self.count == len(readbytes), "insufficient bytes read"
        # return readbytes

    def as_array(self):
        return array(self.fmt, self.read())

    def __repr__(self):
        return f"{self.__class__.__name__}(buffer_view={self._buffer_view_index})"


class Attribute:
    def __init__(self, name, index, owner):
        self.name = name
        self._accessor_index = index
        self.accessor = owner.accessors[index]

        # Aliases
        self.fmt = self.accessor.fmt
        self.type = self.accessor.type
        self.count = self.accessor.count
        self.target = self.accessor.buffer_view.target
        self.target_name = self.accessor.buffer_view.target_name

        self.read = self.accessor.read
        self.as_array = self.accessor.as_array

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', type={self.type}, count={self.count})"


class Primitive:
    def __init__(self, data, owner):
        self.attributes = {name: Attribute(name, index, owner) for name, index in data.get('attributes').items()}

        # TODO: Confirm that this is right:
        self.indices_index = data.get('indices')
        self.indices_accessor = owner.accessors[self.indices_index]

    @property
    def indices(self):
        return self.indices_accessor.as_array()

    def __repr__(self):
        return f"{self.__class__.__name__}(attributes={len(self.attributes)}, index_accessor={self.indices_index})"


class Material:
    def __init__(self, data):
        self.name = data.get('name')

        # TODO: parse this:
        self.pbr_metallic_roughness = data.get('pbrMetallicRoughness')

        self.normal_texture = data.get('normalTexture')
        self.occlusion_texture = data.get('occlusionTexture')
        self.emissive_texture = data.get('emissiveTexture')
        self.emissive_factor = data.get('emissiveFactor', (0.0, 0.0, 0.0))
        self.alpha_mode = data.get('alphaMode', 'OPAQUE')
        self.alpha_cutoff = data.get('alphaCutoff', 0.5)
        self.double_sided = data.get('doubleSided', False)
        # self.extensions = data.get('extensions')
        # self.extras = data.get('extras')


class Texture:
    def __init__(self, data, owner):
        self.name = data.get('name')
        self._sampler_index = data.get('sampler')
        if self._sampler_index:
            self.sampler = owner.samplers[self._sampler_index]
        else:
            self.sampler = Sampler({})
        self.source = data.get('source')            # technically NOT required
        self.image = owner.images[self.source]

        # Aliases
        self.min_filter = self.sampler.min_filter
        self.mag_filter = self.sampler.mag_filter
        self.wrap_s = self.sampler.wrap_s
        self.wrap_t = self.sampler.wrap_t

        # self.extensions = data.get('extensions')
        # self.extras = data.get('extras')


class Sampler:
    def __init__(self, data):
        # TODO: make objects for min/mag filter objects
        self.name = data.get('name')
        self.min_filter = data.get('minFilter')
        self.mag_filter = data.get('magFilter')
        self.wrap_s = data.get('wrapS', GL_REPEAT)
        self.wrap_t = data.get('wrapT', GL_REPEAT)
        # self.extensions = data.get('extensions')
        # self.extras = data.get('extras')


class Image:
    def __init__(self, data, owner):
        self.uri = data.get('uri')
        self._buffer_view_index = data.get('bufferView')
        self.buffer_view = owner.buffer_views[self._buffer_view_index] if self._buffer_view_index else None
        self.mime_type = data.get('mimeType')
        self.name = data.get('name')
        self.extensions = data.get('extensions')
        self.extras = data.get('extras')

    def load(self):
        # TODO: load from either URI or bufferview
        # if self.uri:
        #     return
        # else:
        #
        raise NotImplementedError


class Camera:
    def __init__(self, camera_type, data):
        self.type = camera_type

        # Perspective
        self.aspect_ratio = data.get('aspectRatio')     # Not required
        self.yfov = data.get('yfov')

        # Orthographic
        self.xmag = data.get('xmag')
        self.ymag = data.get('ymag')

        # Shared
        self.zfar = data.get('zfar')        # Not required for Perspective
        self.znear = data.get('znear')


class Mesh:
    def __init__(self, data, owner):
        self.data = data
        self.primitives = [Primitive(primitive_data, owner) for primitive_data in data.get('primitives')]

    def __repr__(self):
        return f"{self.__class__.__name__}(primitives={len(self.primitives)})"


class Node:
    def __init__(self, data, owner):
        self.data = data
        self._owner = owner
        self._child_indices = self.data.get('children', [])

        _mesh_index = data.get('mesh')
        self.mesh = owner.meshes[_mesh_index] if _mesh_index is not None else None

        self.matrix = data.get('matrix')            # Mat4
        self.translation = data.get('translation')  # Vec3
        self.rotation = data.get('rotation')        # Quaternion
        self.scale = data.get('scale')              # Vec3

        # TODO: handle global and local transforms:
        # https://github.com/KhronosGroup/glTF-Tutorials/blob/master/gltfTutorial/gltfTutorial_004_ScenesNodes.md

    @property
    def children(self):
        return [self._owner.nodes[i] for i in self._child_indices]

    def __iter__(self):
        yield self
        for child in self.children:
            yield child

    def __repr__(self):
        return f"{self.__class__.__name__}(mesh={self.mesh}, children={self._child_indices})"


class GLTF:
    def __init__(self, gltf_data: dict):
        self._gltf_data = gltf_data
        self.version = self._gltf_data['asset']['version']
        self.generator = self._gltf_data['asset'].get('generator', 'unknown')

        self.buffers = [Buffer(data=data) for data in gltf_data['buffers']]
        self.buffer_views = [BufferView(data=data, owner=self) for data in gltf_data['bufferViews']]
        self.accessors = [Accessor(data=data, owner=self) for data in gltf_data['accessors']]
        self.meshes = [Mesh(data=data, owner=self) for data in gltf_data['meshes']]
        self.nodes = [Node(data=data, owner=self) for data in gltf_data['nodes']]

        self.cameras = [Camera(cam['type'], cam[cam['type']]) for cam in gltf_data.get('cameras', [])]
        self.images = [Image(data=data, owner=self) for data in gltf_data.get('images', [])]

        self.samplers = [Sampler(data=data) for data in gltf_data.get('samplers', [])]
        self.textures = [Texture(data=data, owner=self) for data in gltf_data.get('textures', [])]
        self.materials = [Material(data) for data in gltf_data.get('materials')]

        self.scenes = [Scene(nodes=[self.nodes[i] for i in data['nodes']]) for data in gltf_data['scenes']]
        self.default_scene = self.scenes[gltf_data.get('scene', 0)]

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
        if float(gltf_data['asset'].get('version', 0)) < 2.0:
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
