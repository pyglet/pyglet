from __future__ import annotations

import json
import struct

from array import array
from urllib.request import urlopen

import pyglet

from pyglet.gl import GL_BYTE, GL_UNSIGNED_BYTE, GL_SHORT, GL_UNSIGNED_SHORT, GL_FLOAT, GL_DOUBLE
from pyglet.gl import GL_INT, GL_UNSIGNED_INT, GL_ELEMENT_ARRAY_BUFFER, GL_ARRAY_BUFFER
from pyglet.gl import GL_REPEAT

from . import ModelDecodeException, ModelDecoder
from .base import Scene
from .base import PBRMaterial
from .base import Camera as BaseCamera
from .base import Attribute as BaseAttribute
from .base import Primitive as BasePrimitive
from .base import Node as BaseNode
from .base import Mesh as BaseMesh


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
    GL_ELEMENT_ARRAY_BUFFER: "ELEMENT_ARRAY_BUFFER",
    GL_ARRAY_BUFFER: "ARRAY_BUFFER",
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
        self.target_name = _targets.get(self.target)

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

        self.byte_offset = data.get('byteOffset', 0)
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
        # readbytes = self.buffer_view.read(self.byte_offset, self._byte_length, self.count)
        # assert self._byte_length * self.count == len(readbytes), "insufficient bytes read"
        # return readbytes

    def as_array(self):
        return array(self.fmt, self.read())

    def __repr__(self):
        return f"{self.__class__.__name__}(buffer_view={self._buffer_view_index})"


class Attribute(BaseAttribute):
    def __init__(self, name, index, owner):
        accessor = owner.accessors[index]
        self.target = accessor.buffer_view.target
        self.target_name = accessor.buffer_view.target_name
        super().__init__(name, accessor.fmt, accessor.type, accessor.count, accessor.as_array())


class Primitive(BasePrimitive):
    def __init__(self, data, owner):
        attributes = [Attribute(name, index, owner) for name, index in data.get('attributes').items()]

        indices_index = data.get('indices')
        indices_accessor = owner.accessors[indices_index] if indices_index is not None else None
        indices = indices_accessor.as_array() if indices_accessor else None

        mode = data.get('mode', 4)     # defaults to TRIANGLES

        material_index = data.get('material')
        material = owner.materials[material_index] if material_index is not None else None

        super().__init__(attributes, indices, mode, material)


class Material(PBRMaterial):
    def __init__(self, data):
        self.name = data.get('name')
        # self.extensions = data.get('extensions')
        # self.extras = data.get('extras')

        # TODO: parse this:
        self.pbr_metallic_roughness = data.get('pbrMetallicRoughness')

        self.normal_texture = data.get('normalTexture')
        self.occlusion_texture = data.get('occlusionTexture')
        self.emissive_texture = data.get('emissiveTexture')
        self.base_color_texture = data.get('baseColorTexture')

        self.emissive_factor = data.get('emissiveFactor', (0.0, 0.0, 0.0))
        self.alpha_mode = data.get('alphaMode', 'OPAQUE')   # Any of: OPAQUE, MASK, BLEND
        self.alpha_cutoff = data.get('alphaCutoff', 0.5)
        self.double_sided = data.get('doubleSided', False)

        # TODO: finish this
        # super().__init__(name, )


class Texture:
    def __init__(self, data, owner):
        self.name = data.get('name')
        # self.extensions = data.get('extensions')
        # self.extras = data.get('extras')

        # TODO: verify how this works. Default sampler?
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

    def read(self):
        # TODO: load from either URI or bufferview
        # if self.uri:
        #     return
        # else:
        raise NotImplementedError


class Camera(BaseCamera):
    def __init__(self, camera_type, data):
        aspect_ratio = data.get('aspectRatio')  # Not required
        yfov = data.get('yfov')
        # Orthographic
        xmag = data.get('xmag')
        ymag = data.get('ymag')
        # Shared
        zfar = data.get('zfar')                 # Not required for Perspective
        znear = data.get('znear')
        super().__init__(camera_type, aspect_ratio, yfov, xmag, ymag, zfar, znear)


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
    def __init__(self, gltf_data: dict, binary_buffer: bytes | None = None):
        self._gltf_data = gltf_data
        self.version = self._gltf_data['asset']['version']
        self.generator = self._gltf_data['asset'].get('generator', 'unknown')

        self.buffers = [Buffer(data=data) for data in gltf_data['buffers']]
        self.buffer_views = [BufferView(data=data, owner=self) for data in gltf_data['bufferViews']]
        self.accessors = [Accessor(data=data, owner=self) for data in gltf_data['accessors']]

        if binary_buffer:
            # TODO: test this, and think of a better way to do it
            self.buffers[0]._file = binary_buffer

        self.images = [Image(data=data, owner=self) for data in gltf_data.get('images', [])]
        self.samplers = [Sampler(data=data) for data in gltf_data.get('samplers', [])]
        self.textures = [Texture(data=data, owner=self) for data in gltf_data.get('textures', [])]
        self.materials = [Material(data) for data in gltf_data.get('materials', [])]

        print(self.images)
        print(self.samplers)
        print(self.textures)

        self.meshes = [Mesh(data=data, owner=self) for data in gltf_data['meshes']]
        self.nodes = [Node(data=data, owner=self) for data in gltf_data['nodes']]

        self.cameras = [Camera(cam['type'], cam[cam['type']]) for cam in gltf_data.get('cameras', [])]

        self.scenes = [Scene(nodes=[self.nodes[i] for i in data['nodes']]) for data in gltf_data['scenes']]
        self.default_scene = self.scenes[gltf_data.get('scene', 0)]

    def __repr__(self):
        return f"{self.__class__.__name__}(scenes={len(self.scenes)}, meshes={len(self.meshes)})"


def load_gltf(filename, file=None) -> GLTF:

    try:
        if file is None:
            file = pyglet.resource.file(filename, 'r')
        elif file.mode != 'r':
            file.close()
            file = pyglet.resource.file(filename, 'r')
    except pyglet.resource.ResourceNotFoundException:
        raise ModelDecodeException

    if filename.endswith('glb'):
        # Check header
        magic = file.read(4)
        if magic != b"glTF":
            raise ModelDecodeException(f"Invalid header for .glb file: {magic}")

        version = struct.unpack("<I", file.read(4))[0]
        if version != 2:
            raise ModelDecodeException(f"Unsupported glTF version: {version}")

        # Total file size including headers
        _ = struct.unpack("<I", file.read(4))[0]  # noqa

        # Chunk 0 - json
        chunk_0_length = struct.unpack("<I", file.read(4))[0]
        chunk_0_type = file.read(4)
        if chunk_0_type != b"JSON":
            raise ModelDecodeException(f"glTF 'chunk 0 type' is not 'JSON': {chunk_0_type}")

        json_meta = file.read(chunk_0_length).decode()

        # chunk 1 - binary buffer
        chunk_1_length = struct.unpack("<I", file.read(4))[0]
        chunk_1_type = file.read(4)
        if chunk_1_type != b"BIN\x00":
            raise ModelDecodeException(f"glTF 'chunk 1 type' is not 'BIN': {chunk_0_type}")

        binary_buffer = file.read(chunk_1_length)

    else:
        json_meta = file.read()
        binary_buffer = None

    try:
        gltf_data = json.loads(json_meta)
    except json.JSONDecodeError as e:
        raise ModelDecodeException(f"Json error. Does not appear to be a valid glTF file. {e}")
    finally:
        file.close()

    if 'asset' not in gltf_data:
        raise ModelDecodeException("Not a valid glTF file: 'asset' property not found.")
    else:
        if float(gltf_data['asset'].get('version', 0)) < 2.0:
            raise ModelDecodeException('Only glTF 2.0+ models are supported')

    return GLTF(gltf_data=gltf_data, binary_buffer=binary_buffer)


###################################################
#   Decoder definitions start here:
###################################################

class GLTFModelDecoder(ModelDecoder):
    def get_file_extensions(self):
        return ['.gltf', '.glb']

    def decode(self, filename, file):
        gltf = load_gltf(filename, file)
        return gltf.scenes[0]


def get_decoders():
    return [GLTFModelDecoder()]


def get_encoders():
    return []
