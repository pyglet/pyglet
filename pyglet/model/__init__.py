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


"""
from __future__ import annotations

from math import pi, sin, cos
from typing import TYPE_CHECKING

import pyglet
from pyglet import gl, graphics
from pyglet.math import Mat4

from .codecs import add_default_codecs as _add_default_codecs
from .codecs import registry as _codec_registry
from .codecs.base import Material, Scene

if TYPE_CHECKING:
    from typing import BinaryIO
    from pyglet.image import Texture
    from pyglet.graphics import Batch, Group
    from pyglet.graphics.shader import ShaderProgram
    from pyglet.graphics.vertexdomain import VertexList
    from pyglet.image import Texture
    from pyglet.model.codecs import ModelDecoder


def load(filename: str, file: BinaryIO | None = None, decoder: ModelDecoder | None = None,
         batch: Batch | None = None, group: Group | None = None) -> Model:
    """Load a 3D model from a file.

    Args:
        filename:
            Used to guess the model format, and to load the file if ``file`` is
            unspecified.
        file:
            An open file containing the source of model data in any supported format.
        decoder:
            If unspecified, all decoders that are registered for the filename
            extension are tried. An exception is raised if no codecs are
            registered for the file extension, or if decoding fails.
        batch:
            An optional Batch instance to add this model to.
        group:
            An optional top level Group.
    """
    if decoder:
        return decoder.decode(filename, file, batch=batch, group=group)
    else:
        return _codec_registry.decode(filename, file, batch=batch, group=group)


def load_scene(filename: str, file: BinaryIO | None = None, decoder: ModelDecoder | None = None) -> Scene:
    """Load a 3D scene from a file.

    Args:
        filename:
            Used to guess the scene format, and to load the file if ``file`` is
            unspecified.
        file:
            An open file containing the source of the scene data in any supported format.
        decoder:
            If unspecified, all decoders that are registered for the filename
            extension are tried in order. An exception is raised if no codecs are
            registered for the file extension, or if decoding fails.
    """
    pass


def get_default_shader() -> ShaderProgram:
    return pyglet.gl.current_context.create_program((MaterialGroup.default_vert_src, 'vertex'),
                                                    (MaterialGroup.default_frag_src, 'fragment'))


def get_default_textured_shader() -> ShaderProgram:
    return pyglet.gl.current_context.create_program((TexturedMaterialGroup.default_vert_src, 'vertex'),
                                                    (TexturedMaterialGroup.default_frag_src, 'fragment'))


class Model:
    """Instance of a 3D object.

    See the module documentation for usage.
    """

    def __init__(self, vertex_lists: list[VertexList], groups: list[Group], batch: Batch | None = None) -> None:
        """Create a model instance.

        Args:
            vertex_lists:
                A list of :py:class:`~pyglet.graphics.VertexList` or
                :py:class:`~pyglet.graphics.IndexedVertexList`.
            groups:
                A list of :py:class:`~pyglet.model.TexturedMaterialGroup`, or
                 :py:class:`~pyglet.model.MaterialGroup`. Each group corresponds
                 to a vertex list in ``vertex_lists`` at the same index.
            batch:
                The batch to add the model to. If no batch is provided,
                the model will maintain its own internal batch.
        """
        self.vertex_lists = vertex_lists
        self.groups = groups
        self._batch = batch or graphics.Batch()
        self._modelview_matrix = Mat4()

    @property
    def batch(self) -> Batch:
        """The graphics Batch that the Model belongs to.

        The Model can be migrated from one batch to another, or removed from
        a batch (for individual drawing). If not part of any batch, the Model
        will keep its own internal batch. Note that batch migration can be
        an expensive operation.
        """
        return self._batch

    @batch.setter
    def batch(self, batch: Batch | None):
        if self._batch == batch:
            return

        if batch is None:
            batch = graphics.Batch()

        for group, vlist in zip(self.groups, self.vertex_lists):
            self._batch.migrate(vlist, gl.GL_TRIANGLES, group, batch)

        self._batch = batch

    @property
    def matrix(self) -> Mat4:
        return self._modelview_matrix

    @matrix.setter
    def matrix(self, matrix: Mat4):
        self._modelview_matrix = matrix
        for group in self.groups:
            group.matrix = matrix

    def draw(self) -> None:
        """Draw the model.

        This is not recommended. See the module documentation
        for information on efficient drawing of multiple models.
        """
        gl.current_context.window_block.bind(0)
        self._batch.draw_subset(self.vertex_lists)


class BaseMaterialGroup(graphics.Group):
    default_vert_src: str
    default_frag_src: str
    matrix: Mat4 = Mat4()

    def __init__(self, material: Material, program: ShaderProgram, order: int = 0, parent: Group | None = None) -> None:
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
        mat4 mv = window.view * model;
        vec4 pos = mv * vec4(position, 1.0);
        gl_Position = window.projection * pos;
        mat3 normal_matrix = transpose(inverse(mat3(mv)));

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
        vec4 tex_color = texture(our_texture, texture_coords) * vertex_colors;
        // 75/25 light ambient
        final_colors = tex_color * l * 0.75 + tex_color * vec4(0.25);
    }
    """

    def __init__(self, material: Material, program: ShaderProgram,
                 texture: Texture, order: int = 0, parent: Group | None = None):
        super().__init__(material, program, order, parent)
        self.texture = texture

    def set_state(self) -> None:
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(self.texture.target, self.texture.id)
        self.program.use()
        self.program['model'] = self.matrix

    def __hash__(self) -> int:
        return hash((self.texture.target, self.texture.id, self.program, self.order, self.parent))

    def __eq__(self, other) -> bool:
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
        mat4 mv = window.view * model;
        vec4 pos = mv * vec4(position, 1.0);
        gl_Position = window.projection * pos;
        mat3 normal_matrix = transpose(inverse(mat3(mv)));

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
        // 75/25 light ambient
        final_colors = vertex_colors * l * 0.75 + vertex_colors * vec4(0.25);
    }
    """

    def set_state(self) -> None:
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

    def __init__(self, width=1.0, height=1.0, depth=1.0, color=(1.0, 1.0, 1.0, 1.0),
                 material=None, batch=None, group=None, program=None):
        self._width = width
        self._height = height
        self._depth = depth
        self._color = color

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

        vertices = (-w, -h, -d,   # front, bottom-left    0
                    w, -h, -d,    # front, bottom-right   1
                    w, h, -d,     # front, top-right      2
                    -w, h, -d,    # front, top-left       3
                    -w, -h, d,    # back, bottom-left     4
                    w, -h, d,     # back, bottom-right    5
                    w, h, d,      # back, top-right       6
                    -w, h, d)     # back, top-left        7

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


class Sphere(Model):

    def __init__(self, radius=1.0, segments=30, color=(1.0, 1.0, 1.0, 1.0),
                 material=None, batch=None, group=None, program=None):
        self._radius = radius
        self._segments = segments
        self._color = color

        self._batch = batch
        self._program = program if program else get_default_shader()

        # Create a Material and Group for the Model
        self._material = material if material else pyglet.model.Material(name="sphere")
        self._group = pyglet.model.MaterialGroup(material=self._material, program=self._program, parent=group)

        self._vlist = self._create_vertexlist()

        super().__init__([self._vlist], [self._group], self._batch)

    def _create_vertexlist(self):
        radius = self._radius
        segments = self._segments

        vertices = []
        indices = []

        for i in range(segments):
            u = i * pi / segments
            for j in range(segments):
                v = j * 2 * pi / segments
                x = radius * sin(u) * cos(v)
                y = radius * sin(u) * sin(v)
                z = radius * cos(u)
                vertices.extend((x, y, z))

        for i in range(segments):
            for j in range(segments):
                indices.extend((i * segments + j, (i - 1) * segments + j, i * segments + (j - 1)))
                indices.extend((i * segments + j, (i + 1) * segments + j, i * segments + (j + 1)))

        normals = vertices

        return self._program.vertex_list_indexed(len(vertices) // 3, pyglet.gl.GL_TRIANGLES, indices,
                                                 batch=self._batch, group=self._group,
                                                 position=('f', vertices),
                                                 normals=('f', normals),
                                                 colors=('f', self._color * (len(vertices) // 3)))


_add_default_codecs()
