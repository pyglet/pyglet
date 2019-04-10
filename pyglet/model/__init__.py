# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2019 Alex Holkner
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
"""Loading of 3D models.

A :py:class:`~pyglet.model.Model` is an instance of a 3D object.

The following example loads a ``"teapot.obj"`` model::

    import pyglet

    window = pyglet.window.Window()

    teapot = pyglet.model.load('teapot.obj')

    @window.event
    def on_draw():
        teapot.draw()

    pyglet.app.run()


You can also load models with :py:meth:`~pyglet.resource.model`.
See :py:mod:`~pyglet.resource` for more information.


Efficient Drawing
=================

As with Sprites or Text, Models can be added to a
:py:class:`~pyglet.graphics.Batch` for efficient drawing. This is
preferred to calling their ``draw`` methods individually.  To do this,
simply pass in a reference to the :py:class:`~pyglet.graphics.Batch`
instance when loading the Model::


    import pyglet

    window = pyglet.window.Window()
    batch = pyglet.graphics.Batch()

    teapot = pyglet.model.load('teapot.obj', batch=batch)

    @window.event
    def on_draw():
        batch.draw()

    pyglet.app.run()


.. versionadded:: 1.4
"""

from io import BytesIO

from pyglet.graphics.shader import Shader, ShaderProgram
from pyglet.gl import *
from pyglet import graphics

from .codecs import ModelDecodeException
from .codecs import add_encoders, add_decoders, add_default_model_codecs
from .codecs import get_encoders, get_decoders


def load(filename, file=None, decoder=None, batch=None):
    """Load a 3D model from a file.

    :Parameters:
        `filename` : str
            Used to guess the model format, and to load the file if `file` is
            unspecified.
        `file` : file-like object or None
            Source of model data in any supported format.        
        `decoder` : ModelDecoder or None
            If unspecified, all decoders that are registered for the filename
            extension are tried. An exception is raised if no codecs are
            registered for the file extension, or if decoding fails.
        `batch` : Batch or None
            An optional Batch instance to add this model to.

    :rtype: :py:mod:`~pyglet.model.Model`
    """

    if not file:
        file = open(filename, 'rb')

    if not hasattr(file, 'seek'):
        file = BytesIO(file.read())

    try:
        if decoder:
            return decoder.decode(file, filename, batch)
        else:
            first_exception = None
            for decoder in get_decoders(filename):
                try:
                    model = decoder.decode(file, filename, batch)
                    return model
                except ModelDecodeException as e:
                    if (not first_exception or
                            first_exception.exception_priority < e.exception_priority):
                        first_exception = e
                    file.seek(0)

            if not first_exception:
                raise ModelDecodeException('No decoders are available for this model format.')
            raise first_exception
    finally:
        file.close()


class Model(object):
    """Instance of a 3D object.

    See the module documentation for usage.
    """

    def __init__(self, vertex_lists, groups, batch):
        """Create a model.

        :Parameters:
            `vertex_lists` : list
                A list of `~pyglet.graphics.VertexList` or
                `~pyglet.graphics.IndexedVertexList`.
            `groups` : list
                A list of `~pyglet.model.TexturedMaterialGroup`, or
                 `~pyglet.model.MaterialGroup`. Each group corresponds to
                 a vertex list in `vertex_lists` of the same index.
            `batch` : `~pyglet.graphics.Batch`
                Optional batch to add the model to. If no batch is provided,
                the model will maintain it's own internal batch.
        """
        self.vertex_lists = vertex_lists
        self.groups = groups
        self._batch = batch
        self._rotation = 0, 0, 0
        self._translation = 0, 0, 0

    @property
    def batch(self):
        """The graphics Batch that the Model belongs to.

        The Model can be migrated from one batch to another, or removed from
        a batch (for individual drawing). If not part of any batch, the Model
        will keep it's own internal batch. Note that batch migration can be
        an expensive operation.

        :type: :py:class:`pyglet.graphics.Batch`
        """
        return self._batch

    @batch.setter
    def batch(self, batch):
        if self._batch == batch:
            return

        if batch is None:
            batch = graphics.Batch()

        for group, vlist in zip(self.groups, self.vertex_lists):
            self._batch.migrate(vlist, GL_TRIANGLES, group, batch)

        self._batch = batch

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, values):
        self._rotation = values
        for group in self.groups:
            group.rotation = values

    @property
    def translation(self):
        return self._translation

    @translation.setter
    def translation(self, values):
        self._translation = values
        for group in self.groups:
            group.translation = values

    def draw(self):
        """Draw the model.

        This is not recommended. See the module documentation
        for information on efficient drawing of multiple models.
        """
        self._batch.draw_subset(self.vertex_lists)


class Material(object):
    __slots__ = ("name", "diffuse", "ambient", "specular", "emission", "shininess", "texture_name")

    def __init__(self, name, diffuse, ambient, specular, emission, shininess, texture_name=None):
        self.name = name
        self.diffuse = diffuse
        self.ambient = ambient
        self.specular = specular
        self.emission = emission
        self.shininess = shininess
        self.texture_name = texture_name


vertex_source = """#version 330 core
    in vec4 vertices;
    in vec4 normals;
    in vec4 colors;
    in vec2 tex_coords;
    out vec4 vertex_colors;
    out vec4 vertex_normals;
    out vec2 texture_coords;

    uniform vec3 rotation;
    uniform vec3 translation;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;  

    mat4 m_translation = mat4(1.0);
    mat4 m_rotation_x = mat4(1.0);
    mat4 m_rotation_y = mat4(1.0);
    mat4 m_rotation_z = mat4(1.0);

    void main()
    {
        m_rotation_x[1][1] =  cos(-radians(rotation.x)); 
        m_rotation_x[1][2] =  sin(-radians(rotation.x));
        m_rotation_x[2][1] = -sin(-radians(rotation.x));
        m_rotation_x[2][2] =  cos(-radians(rotation.x));
        vec4 vertices_rx = m_rotation_x * vertices;

        m_rotation_y[0][0] =  cos(-radians(rotation.y)); 
        m_rotation_y[0][2] = -sin(-radians(rotation.y));    
        m_rotation_y[2][0] =  sin(-radians(rotation.y)); 
        m_rotation_y[2][2] =  cos(-radians(rotation.y));
        vec4 vertices_rxy = m_rotation_y * vertices_rx;

        m_rotation_z[0][0] =  cos(-radians(rotation.z)); 
        m_rotation_z[0][1] =  sin(-radians(rotation.z));
        m_rotation_z[1][0] = -sin(-radians(rotation.z));
        m_rotation_z[1][1] =  cos(-radians(rotation.z));
        vec4 vertices_rxyz = m_rotation_z * vertices_rxy;

        m_translation[3][0] = translation.x;
        m_translation[3][1] = translation.y;
        m_translation[3][2] = translation.z;
        vec4 vertices_final = m_translation * vertices_rxyz;

        gl_Position = window.projection * window.view * vertices_final;

        vertex_colors = colors;
        vertex_normals = normals;
        texture_coords = tex_coords;
    }
"""

fragment_source = """#version 330 core
    in vec4 vertex_colors;
    in vec4 vertex_normals;
    in vec2 texture_coords;
    out vec4 final_colors;

    uniform sampler2D our_texture;

    void main()
    {
        // TODO: implement lighting, and do something with normals and materials.
        vec4 nothing = vertex_normals - vec4(1.0, 1.0, 1.0, 1.0);
        final_colors = texture(our_texture, texture_coords) + vertex_colors * nothing;
    }
"""

_default_vert_shader = Shader(vertex_source, 'vertex')
_default_frag_shader = Shader(fragment_source, 'fragment')
default_shader_program = ShaderProgram(_default_vert_shader, _default_frag_shader)


class TexturedMaterialGroup(graphics.Group):

    def __init__(self, material, texture):
        super().__init__()
        self.material = material
        self.texture = texture
        self.program = default_shader_program
        self.rotation = 0, 0, 0
        self.translation = 0, 0, 0

    def set_state(self):
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(self.texture.target, self.texture.id)
        self.program.use_program()
        self.program['rotation'] = self.rotation
        self.program['translation'] = self.translation

    def unset_state(self):
        glBindTexture(self.texture.target, 0)
        self.program.stop_program()

    def __eq__(self, other):
        return False

    def __hash__(self):
        return hash((id(self.parent), self.texture.id, self.texture.target))


class MaterialGroup(graphics.Group):

    def __init__(self, material):
        super(MaterialGroup, self).__init__()
        self.material = material
        self.program = default_shader_program
        self.rotation = 0, 0, 0
        self.translation = 0, 0, 0

    def set_state(self):
        self.program.use_program()
        self.program['rotation'] = self.rotation
        self.program['translation'] = self.translation

    def unset_state(self):
        self.program.stop_program()

    def __eq__(self, other):
        return False

    def __hash__(self):
        return hash((id(self.parent)))


add_default_model_codecs()
