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

import pyglet

from pyglet import gl
from pyglet import graphics
from pyglet.gl import current_context
from pyglet.math import Mat4, Vec3
from pyglet.graphics import shader

from .codecs import registry as _codec_registry
from .codecs import add_default_codecs as _add_default_codecs


def load(filename, file=None, decoder=None, batch=None, group=None):
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
        `group` : Group or None
            An optional top level Group.

    :rtype: :py:mod:`~pyglet.model.Model`
    """
    if decoder:
        return decoder.decode(filename, file, batch=batch, group=group)
    else:
        return _codec_registry.decode(filename, file, batch=batch, group=group)


def get_default_shader():
    try:
        return pyglet.gl.current_context.model_default_plain_shader
    except AttributeError:
        vert_shader = shader.Shader(MaterialGroup.default_vert_src, 'vertex')
        frag_shader = shader.Shader(MaterialGroup.default_frag_src, 'fragment')
        default_shader_program = shader.ShaderProgram(vert_shader, frag_shader)
        pyglet.gl.current_context.model_default_plain_shader = default_shader_program
        return pyglet.gl.current_context.model_default_plain_shader


def get_default_textured_shader():
    try:
        return pyglet.gl.current_context.model_default_textured_shader
    except AttributeError:
        vert_shader = shader.Shader(TexturedMaterialGroup.default_vert_src, 'vertex')
        frag_shader = shader.Shader(TexturedMaterialGroup.default_frag_src, 'fragment')
        default_shader_program = shader.ShaderProgram(vert_shader, frag_shader)
        pyglet.gl.current_context.model_default_textured_shader = default_shader_program
        return current_context.model_default_textured_shader


class Model:
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
                the model will maintain its own internal batch.
        """
        self.vertex_lists = vertex_lists
        self.groups = groups
        self._batch = batch
        self._modelview_matrix = Mat4()

    @property
    def batch(self):
        """The graphics Batch that the Model belongs to.

        The Model can be migrated from one batch to another, or removed from
        a batch (for individual drawing). If not part of any batch, the Model
        will keep its own internal batch. Note that batch migration can be
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
            self._batch.migrate(vlist, gl.GL_TRIANGLES, group, batch)

        self._batch = batch

    @property
    def matrix(self):
        return self._modelview_matrix

    @matrix.setter
    def matrix(self, matrix):
        self._modelview_matrix = matrix
        for group in self.groups:
            group.matrix = matrix

    def draw(self):
        """Draw the model.

        This is not recommended. See the module documentation
        for information on efficient drawing of multiple models.
        """
        gl.current_context.window_block.bind(0)
        self._batch.draw_subset(self.vertex_lists)


class Material:
    __slots__ = ("name", "diffuse", "ambient", "specular", "emission", "shininess", "texture_name")

    def __init__(self, name, diffuse, ambient, specular, emission, shininess, texture_name=None):
        self.name = name
        self.diffuse = diffuse
        self.ambient = ambient
        self.specular = specular
        self.emission = emission
        self.shininess = shininess
        self.texture_name = texture_name

    def __eq__(self, other):
        return (self.name == other.name and
                self.diffuse == other.diffuse and
                self.ambient == other.ambient and
                self.specular == other.specular and
                self.emission == other.emission and
                self.shininess == other.shininess and
                self.texture_name == other.texture_name)


class BaseMaterialGroup(graphics.Group):
    default_vert_src = None
    default_frag_src = None
    matrix = Mat4()

    def __init__(self, material, program, order=0, parent=None):
        super().__init__(order, parent)
        self.material = material
        self.program = program


class TexturedMaterialGroup(BaseMaterialGroup):
    default_vert_src = """#version 330 core
    in vec3 vertices;
    in vec3 normals;
    in vec2 tex_coords;
    in vec4 colors;

    out vec4 vertex_colors;
    out vec3 vertex_normals;
    out vec2 texture_coords;
    out vec3 vertex_position;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

    uniform mat4 model;

    void main()
    {
        vec4 pos = window.view * model * vec4(vertices, 1.0);
        gl_Position = window.projection * pos;
        mat3 normal_matrix = transpose(inverse(mat3(model)));

        vertex_position = pos.xyz;
        vertex_colors = colors;
        texture_coords = tex_coords;
        vertex_normals = normal_matrix * normals;
    }
    """
    default_frag_src = """#version 330 core
    in vec4 vertex_colors;
    in vec3 vertex_normals;
    in vec2 texture_coords;
    in vec3 vertex_position;
    out vec4 final_colors;

    uniform sampler2D our_texture;

    void main()
    {
        float l = dot(normalize(-vertex_position), normalize(vertex_normals));
        final_colors = (texture(our_texture, texture_coords) * vertex_colors) * l * 1.2;
    }
    """

    def __init__(self, material, program, texture, order=0, parent=None):
        super().__init__(material, program, order, parent)
        self.texture = texture

    def set_state(self):
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(self.texture.target, self.texture.id)
        self.program.use()
        self.program['model'] = self.matrix

    def __hash__(self):
        return hash((self.texture.target, self.texture.id, self.program, self.order, self.parent))

    def __eq__(self, other):
        return (self.__class__ is other.__class__ and
                self.material == other.material and
                self.texture.target == other.texture.target and
                self.texture.id == other.texture.id and
                self.program == other.program and
                self.order == other.order and
                self.parent == other.parent)


class MaterialGroup(BaseMaterialGroup):
    default_vert_src = """#version 330 core
    in vec3 vertices;
    in vec3 normals;
    in vec4 colors;

    out vec4 vertex_colors;
    out vec3 vertex_normals;
    out vec3 vertex_position;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

    uniform mat4 model;

    void main()
    {
        vec4 pos = window.view * model * vec4(vertices, 1.0);
        gl_Position = window.projection * pos;
        mat3 normal_matrix = transpose(inverse(mat3(model)));

        vertex_position = pos.xyz;
        vertex_colors = colors;
        vertex_normals = normal_matrix * normals;
    }
    """
    default_frag_src = """#version 330 core
    in vec4 vertex_colors;
    in vec3 vertex_normals;
    in vec3 vertex_position;
    out vec4 final_colors;

    void main()
    {
        float l = dot(normalize(-vertex_position), normalize(vertex_normals));
        final_colors = vertex_colors * l * 1.2;
    }
    """

    def set_state(self):
        self.program.use()
        self.program['model'] = self.matrix


_add_default_codecs()
