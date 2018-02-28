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

import pyglet

from pyglet.gl import GL_BYTE, GL_UNSIGNED_BYTE, GL_SHORT, GL_UNSIGNED_SHORT, GL_FLOAT
from pyglet.gl import GL_UNSIGNED_INT, GL_ELEMENT_ARRAY_BUFFER, GL_ARRAY_BUFFER

from .. import Model, Material, Mesh
from . import ModelDecodeException, ModelDecoder


_struct_types = {
    GL_BYTE: 'b',
    GL_FLOAT: 'f',
    GL_SHORT: 's',
    GL_UNSIGNED_BYTE: 'B',
    GL_UNSIGNED_SHORT: 'S',
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


def parse_gltf_file(filename, file=None):
    materials = {}
    mesh_list = []

    if not file:
        file = open(filename)

    try:
        data = json.load(file)
    except json.JSONDecodeError:
        raise ModelDecodeException('Json error. Does not appear to be a valid glTF file.')
    finally:
        file.close()

    path = os.path.dirname(filename)

    if 'asset' not in data:
        raise ModelDecodeException('Not a valid glTF file. Asset property not found.')
    else:
        if float(data['asset']['version']) < 2.0:
            raise ModelDecodeException('Only glTF 2.0+ models are supported')

    buffers = data.get('buffers', [])
    buffer_views = data.get('bufferViews', [])
    accessors = data.get('accessors', [])

    for acessor in accessors:
        # "required": ["bufferView", "byteOffset", "componentType", "count", "type"]
        view = buffer_views[acessor['bufferView']]
        offset = acessor['byteOffset']
        component_type = acessor['componentType']
        count = acessor['count']

        size = _accessor_types[acessor['type']] * count
        struct_type = "{0}{1}".format(_struct_types[component_type], size)
        target = view['target']

        print(struct_type, _targets[target])

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

        return Model(mesh_list=mesh_list, batch=batch)


def get_decoders():
    return [GLTFModelDecoder()]


def get_encoders():
    return []
