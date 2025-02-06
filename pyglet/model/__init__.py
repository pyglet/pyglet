"""Loading of 3D scenes and models.

The :py:mod:`~pyglet.model` module provides an interface for loading 3D "scenes"
and models. A :py:class:`~pyglet.model.Scene` is a logical container that can
contain the data of one or more models, and is closely based on the design
of the glTF format.

The following example loads a ``"teapot.obj"`` file. The wavefront format
only contains a single model (mesh)::

    import pyglet

    window = pyglet.window.Window()
    batch = pyglet.graphics.Batch()

    scene = pyglet.model.load('teapot.obj')
    models = scene.create_models(batch=batch)

    @window.event
    def on_draw():
        batch.draw()

    pyglet.app.run()


You can also load scenes with :py:meth:`~pyglet.resource.scene`.
See :py:mod:`~pyglet.resource` for more information.
"""
from __future__ import annotations

from math import pi, sin, cos
from typing import TYPE_CHECKING

import pyglet
from pyglet import gl, graphics
from pyglet.math import Mat4

from .codecs import add_default_codecs as _add_default_codecs
from .codecs import registry as _codec_registry
from .codecs.base import Material, Scene, SimpleMaterial

if TYPE_CHECKING:
    from typing import BinaryIO, TextIO
    from pyglet.image import Texture
    from pyglet.graphics import Batch, Group
    from pyglet.graphics.shader import ShaderProgram
    from pyglet.graphics.vertexdomain import VertexList
    from pyglet.image import Texture
    from pyglet.model.codecs import ModelDecoder


def load(filename: str, file: BinaryIO | TextIO | None = None, decoder: ModelDecoder | None = None) -> Scene:
    """Load a 3D scene from a file.

    Args:
        filename:
            Used to guess the scene format, or to load the file if ``file`` is unspecified.
        file:
            An open file containing the source of the scene data in any supported format.
        decoder:
            The specific decoder to use to load the Scene. If None, use default decoders
            that match the filename extension.
    """
    if decoder:
        return decoder.decode(filename, file)

    return _codec_registry.decode(filename, file)


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


class BaseMaterialGroup(graphics.Group):
    default_vert_src: str
    default_frag_src: str
    matrix: Mat4 = Mat4()

    def __init__(self, material: SimpleMaterial, program: ShaderProgram, order: int = 0, parent: Group | None = None) -> None:
        super().__init__(order, parent)
        self.material = material
        self.program = program


class TexturedMaterialGroup(BaseMaterialGroup):
    default_vert_src = """#version 330 core
    in vec3 POSITION;
    in vec3 NORMAL;
    in vec2 TEXCOORD_0;
    in vec4 COLOR_0;

    out vec3 position;
    out vec3 normal;
    out vec2 texcoord_0;
    out vec4 color_0;    

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

    uniform mat4 model;

    void main()
    {
        mat4 mv = window.view * model;
        vec4 pos = mv * vec4(POSITION, 1.0);
        gl_Position = window.projection * pos;
        mat3 normal_matrix = transpose(inverse(mat3(mv)));

        position = pos.xyz;
        normal = normal_matrix * NORMAL;
        texcoord_0 = TEXCOORD_0;
        color_0 = COLOR_0;
    }
    """
    default_frag_src = """#version 330 core
    in vec4 color_0;
    in vec3 normal;
    in vec2 texcoord_0;
    in vec3 position;
    out vec4 final_colors;

    uniform sampler2D our_texture;

    void main()
    {
        float l = dot(normalize(-position), normalize(normal));
        vec4 tex_color = texture(our_texture, texcoord_0) * color_0;
        // 75/25 light ambient
        final_colors = tex_color * l * 0.75 + tex_color * vec4(0.25);
    }
    """

    def __init__(self, material: SimpleMaterial, program: ShaderProgram,
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
    in vec3 POSITION;
    in vec3 NORMAL;
    in vec4 COLOR_0;

    out vec4 color_0;
    out vec3 normal;
    out vec3 position;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

    uniform mat4 model;

    void main()
    {
        mat4 mv = window.view * model;
        vec4 pos = mv * vec4(POSITION, 1.0);
        gl_Position = window.projection * pos;
        mat3 normal_matrix = transpose(inverse(mat3(mv)));

        position = pos.xyz;
        color_0 = COLOR_0;
        normal = normal_matrix * NORMAL;
    }
    """
    default_frag_src = """#version 330 core
    in vec4 color_0;
    in vec3 normal;
    in vec3 position;
    out vec4 final_colors;

    void main()
    {
        float l = dot(normalize(-position), normalize(normal));
        // 75/25 light ambient
        final_colors = color_0 * l * 0.75 + color_0 * vec4(0.25);
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
        self._material = material if material else SimpleMaterial(name="cube")
        self._group = pyglet.model.MaterialGroup(material=self._material, program=self._program, parent=group)

        self._vlist = self._create_vertexlist()

        super().__init__([self._vlist], [self._group], self._batch)

    def _create_vertexlist(self):
        w = self._width / 2
        h = self._height / 2
        d = self._depth / 2

        vertices = [
            -w, -h, -d,   # front, bottom-left    0
            w, -h, -d,    # front, bottom-right   1
            w, h, -d,     # front, top-right      2         Front
            -w, h, -d,    # front, top-left       3

            w, -h, d,     # back, bottom-right    4
            -w, -h, d,    # back, bottom-left     5
            -w, h, d,     # back, top-left        6         Back
            w, h, d,      # back, top-right       7

            w, -h, -d,    # front, bottom-right   8
            w, -h, d,     # back, bottom-right    9
            w, h, d,      # back, top-right      10         Right
            w, h, -d,     # front, top-right     11

            -w, -h, d,    # back, bottom-left    12
            -w, -h, -d,   # front, bottom-left   13
            -w, h, -d,    # front, top-left      14         Left
            -w, h, d,     # back, top-left       15

            -w, h, -d,    # front, top-left      16
            w, h, -d,     # front, top-right     17
            w, h, d,      # back, top-right      18         Top
            -w, h, d,     # back, top-left       19

            -w, -h, d,    # back, bottom-left    20
            w, -h, d,     # back, bottom-right   21
            w, -h, -d,    # front, bottom-right  22         Bottom
            -w, -h, -d,   # front, bottom-left   23
        ]

        normals = [0, 0, -1, 0, 0, -1, 0, 0, -1, 0, 0, -1,     # front face
                   0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1,         # back face
                   1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0,         # right face
                   -1, 0, 0, -1, 0, 0, -1, 0, 0, -1, 0, 0,     # left face
                   0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0,         # top face
                   0, -1, 0, 0, -1, 0, 0, -1, 0, 0, -1, 0]     # bottom face

        indices = [23, 22, 20, 22, 21, 20,  # bottom
                   19, 18, 16, 18, 17, 16,  # top
                   15, 14, 12, 14, 13, 12,  # left
                   11, 10, 8, 10, 9, 8,     # right
                   7, 6, 4, 6, 5, 4,        # back
                   3, 2, 0, 2, 1, 0]        # front

        return self._program.vertex_list_indexed(len(vertices) // 3, pyglet.gl.GL_TRIANGLES, indices,
                                                 batch=self._batch, group=self._group,
                                                 POSITION=('f', vertices),
                                                 NORMAL=('f', normals),
                                                 COLOR_0=('f', self._color * (len(vertices) // 3)))


class Sphere(Model):

    def __init__(self, radius=1.0, stacks=30, sectors=30, color=(1.0, 1.0, 1.0, 1.0),
                 material=None, batch=None, group=None, program=None):
        self._radius = radius
        self._stacks = stacks
        self._sectors = sectors
        self._color = color

        self._batch = batch
        self._program = program if program else get_default_shader()

        # Create a Material and Group for the Model
        self._material = material if material else SimpleMaterial(name="sphere")
        self._group = pyglet.model.MaterialGroup(material=self._material, program=self._program, parent=group)

        self._vlist = self._create_vertexlist()

        super().__init__([self._vlist], [self._group], self._batch)

    def _create_vertexlist(self):
        radius = self._radius / 2
        sectors = self._sectors
        stacks = self._stacks

        vertices = []
        normals = []
        indices = []

        sector_step = 2 * pi / sectors
        stack_step = pi / stacks

        for i in range(stacks + 1):
            stack_angle = pi / 2 - i * stack_step
            for j in range(sectors + 1):
                sector_angle = j * sector_step
                vertices.append(radius * cos(stack_angle) * cos(sector_angle))    # x
                vertices.append(radius * cos(stack_angle) * sin(sector_angle))    # y
                vertices.append(radius * sin(stack_angle))                             # z
                normals.append(cos(stack_angle) * cos(sector_angle))              # x
                normals.append(cos(stack_angle) * sin(sector_angle))              # y
                normals.append(sin(stack_angle))                                       # z

        # Generate indices
        for i in range(stacks):
            for j in range(sectors):
                first = i * (sectors + 1) + j
                second = first + sectors + 1
                indices.extend([first, second, second + 1])
                indices.extend([first, second + 1, first + 1])

        return self._program.vertex_list_indexed(len(vertices) // 3, pyglet.gl.GL_TRIANGLES, indices,
                                                 batch=self._batch, group=self._group,
                                                 POSITION=('f', vertices),
                                                 NORMAL=('f', normals),
                                                 COLOR_0=('f', self._color * (len(vertices) // 3)))


_add_default_codecs()
