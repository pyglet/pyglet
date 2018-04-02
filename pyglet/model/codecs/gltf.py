# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions 
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright 
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------
import os
import json
import array
import struct

import pyglet

from pyglet.gl import GL_BYTE, GL_UNSIGNED_BYTE, GL_SHORT, GL_UNSIGNED_SHORT, GL_FLOAT
from pyglet.gl import GL_UNSIGNED_INT, GL_ELEMENT_ARRAY_BUFFER, GL_ARRAY_BUFFER, GL_TRIANGLES

from .. import Model, Material, Mesh, MaterialGroup, TexturedMaterialGroup
from . import ModelDecodeException, ModelDecoder


_struct_types = {
    GL_BYTE: 'b',
    GL_FLOAT: 'f',
    GL_SHORT: 's',              # ('h')
    GL_UNSIGNED_BYTE: 'B',
    GL_UNSIGNED_SHORT: 'H',     # ('S')
    GL_UNSIGNED_INT: 'I',
}

_accessor_types = {
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


class Buffer(object):
    def __init__(self, length, uri):
        self._length = length
        self._file = pyglet.resource.file(uri, 'rb')

    def read(self, offset, length, stride=1):
        self._file.seek(offset)
        data = self._file.read(length)
        return data[::stride]


def parse_gltf_file(filename, file=None):

    if not file:
        file = open(filename)

    path = os.path.abspath(filename)

    try:
        data = json.load(file)
    except json.JSONDecodeError:
        raise ModelDecodeException('Json error. Does not appear to be a valid glTF file.')
    finally:
        file.close()

    if 'asset' not in data:
        raise ModelDecodeException('Not a valid glTF file. Asset property not found.')
    else:
        if float(data['asset']['version']) < 2.0:
            raise ModelDecodeException('Only glTF 2.0+ models are supported')

    buffers = {i: Buffer(length=item['byteLength'], uri=item['uri'])
               for i, item in enumerate(data.get('buffers', []))}
    buffer_views = data.get('bufferViews', [])
    accessors = data.get('accessors', [])

    for accessor in accessors:
        # "required": ["bufferView", "byteOffset", "componentType", "count", "type"]
        buffer_view = buffer_views[accessor['bufferView']]
        byte_offset = accessor['byteOffset']
        component_type = accessor['componentType']
        count = accessor['count']
        data_type = accessor['type']

        size = _accessor_types[data_type] * count
        target = buffer_view['target']
        buffer = buffers[buffer_view['buffer']]

        offset = buffer_view.get('byteOffset')
        length = buffer_view.get('byteLength')
        stride = buffer_view.get('byteStride', 1)   # Default to 1, if no stride.

        data = buffer.read(offset, length, stride)
        arr = array.array(_struct_types[component_type], data)

    # return mesh_list
    return buffers, buffer_views


###################################################
#   Decoder definitions start here:
###################################################

class GLTFModelDecoder(ModelDecoder):
    def get_file_extensions(self):
        return ['.gltf']

    def decode(self, file, filename, batch):

        if not batch:
            batch = pyglet.graphics.Batch()

        mesh_list = parse_gltf_file(filename=filename)

        textures = {}
        vertex_lists = {}

        # for mesh in mesh_list:
        #     material = mesh.material
        #     if material.texture_name:
        #         texture = pyglet.resource.texture(material.texture_name)
        #         group = TexturedMaterialGroup(material, texture)
        #         textures[texture] = group
        #     else:
        #         group = MaterialGroup(material)
        #
        #     vlist = batch.add(len(mesh.vertices) // 3,
        #                       GL_TRIANGLES,
        #                       group,
        #                       ('v3f/static', mesh.vertices),
        #                       ('n3f/static', mesh.normals),
        #                       ('t2f/static', mesh.tex_coords))
        #
        #     vertex_lists[vlist] = group

        return Model(vertex_lists, textures, batch=batch)


def get_decoders():
    return [GLTFModelDecoder()]


def get_encoders():
    return []
