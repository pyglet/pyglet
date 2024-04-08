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

from __future__ import annotations

from typing import Tuple

import pyglet

from pyglet import gl
from pyglet import graphics
from pyglet.math import Mat4

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
    return pyglet.gl.current_context.create_program((MaterialGroup.default_vert_src, 'vertex'),
                                                    (MaterialGroup.default_frag_src, 'fragment'))


def get_default_textured_shader():
    return pyglet.gl.current_context.create_program((TexturedMaterialGroup.default_vert_src, 'vertex'),
                                                    (TexturedMaterialGroup.default_frag_src, 'fragment'))


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

    def __init__(self, name: str = "default",
                 diffuse: Tuple[float, float, float, float] = (0.8, 0.8, 0.8, 1.0),
                 ambient: Tuple[float, float, float, float] = (0.2, 0.2, 0.2, 1.0),
                 specular: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0),
                 emission: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0),
                 shininess: float = 20,
                 texture_name: str = ""):

        self.name = name
        self.diffuse = diffuse
        self.ambient = ambient
        self.specular = specular
        self.emission = emission
        self.shininess = shininess
        self.texture_name = texture_name

    def __eq__(self, other: Material) -> bool:
        return (self.name == other.name and self.diffuse == other.diffuse and
                self.ambient == other.ambient and self.specular == other.specular and
                self.emission == other.emission and self.shininess == other.shininess and
                self.texture_name == other.texture_name)

    def __hash__(self) -> int:
        return hash((self.name, self.texture_name, tuple(self.diffuse), tuple(self.specular),
                     tuple(self.ambient), tuple(self.emission), self.shininess, self.texture_name))


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
    in vec3 position;
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
        vec4 pos = window.view * model * vec4(position, 1.0);
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
    in vec3 position;
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
        vec4 pos = window.view * model * vec4(position, 1.0);
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

    def __hash__(self):
        return hash((self.material, self.program, self.order, self.parent))

    def __eq__(self, other):
        return (self.__class__ is other.__class__ and
                self.material == other.material and
                self.program == other.program and
                self.order == other.order and
                self.parent == other.parent)


class Cube(Model):

    def __init__(self, width=1.0, height=1.0, depth=1.0, color=(1.0, 1.0, 1.0, 1.0), material=None,
                 batch=None, group=None, program=None):
        self._width = width
        self._height = height
        self._depth = depth
        self._color = color
        self._scale = 1.0

        self._batch = batch
        self._program = program if program else get_default_shader()

        # Create a Material and Group for the Model
        self._material = material if material else pyglet.model.Material(name="cube")
        self._group = pyglet.model.MaterialGroup(material=self._material, program=self._program, parent=group)

        self._vlist = self._create_vertexlist()

        super().__init__([self._vlist], [self._group], self._batch)

    def _create_vertexlist(self):
        w = self._width / 2
        h = self._height / 2
        d = self._depth / 2
        s = self._scale

        vertices = (-w, -h, -d,   # front, bottom-left    0
                    w, -h, -d,    # front, bottom-right   1
                    w, h, -d,     # front, top-right      2
                    -w, h, -d,    # front, top-left       3
                    -w, -h, d,    # back, bottom-left     4
                    w, -h, d,     # back, bottom-right    5
                    w, h, d,      # back, top-right       6
                    -w, h, d)     # back, top-left        7

        vertices = tuple(v * s for v in vertices)

        normals = (-0.5, -0.5, -1.0,    # back, bottom-left
                   0.5, -0.5, -1.0,     # back, buttom-right
                   0.5,  0.5, -1.0,     # back, top-right
                   -0.5, 0.5, -1.0,     # back, top-left
                   -0.5, -0.5, 0.0,     # front, bottom-left
                   0.5, -0.5, 0.0,      # front, bottom-right
                   0.5, 0.5, 0.0,       # front, top-right
                   -0.5, 0.5, 0.0)      # front, top-left

        indices = (0, 3, 2, 0, 2, 1,    # front
                   4, 5, 6, 4, 6, 7,    # back
                   4, 7, 3, 4, 3, 0,    # left
                   1, 2, 6, 1, 6, 5,    # right
                   3, 7, 6, 3, 6, 2,    # top
                   0, 1, 5, 0, 5, 4)    # bottom

        return self._program.vertex_list_indexed(len(vertices) // 3, pyglet.gl.GL_TRIANGLES, indices,
                                                 batch=self._batch, group=self._group,
                                                 position=('f', vertices),
                                                 normals=('f', normals),
                                                 colors=('f', self._color * (len(vertices) // 3)))


_add_default_codecs()
