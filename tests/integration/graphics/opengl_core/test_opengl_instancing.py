from __future__ import annotations

import random

import pytest
import ctypes

from tests.annotations import skip_graphics_api, GraphicsAPI


pytestmark = [skip_graphics_api(GraphicsAPI.GL2)]


_vertex_source: str = """#version 330 core
    in vec3 position;
    in vec3 translate;
    in vec4 colors;
    in vec3 tex_coords;
    out vec4 vertex_colors;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

    void main()
    {
         mat4 m_translate = mat4(1.0);
         m_translate[3][0] = translate.x;
         m_translate[3][1] = translate.y;
         m_translate[3][2] = translate.z;

        gl_Position = window.projection * window.view * m_translate * vec4(position, 1.0);

        vertex_colors = colors;
    }
"""

_fragment_source: str = """#version 330 core
    in vec4 vertex_colors;
    out vec4 final_colors;

    void main()
    {
        final_colors = vertex_colors;
    }
"""


@pytest.fixture(scope="module")
def shader_program(gl3_context):
    """Compile and link the ShaderProgram once per module, and delete at the end."""
    from pyglet.graphics import ShaderProgram, Shader
    vertex = Shader(_vertex_source, "vertex")
    fragment = Shader(_fragment_source, "fragment")
    program = ShaderProgram(vertex, fragment)
    try:
        yield program
    finally:
        # Ensures deletion even if a test failed
        program.delete()


@pytest.fixture
def vlist_factory(shader_program):
    """Helper to create a fresh instanced vertex list bound to the shared program."""
    from pyglet.graphics import GeometryMode
    def make(verts, indices=(0,1,2,0,2,3)):
        return shader_program.vertex_list_instanced_indexed(
            4,
            mode=GeometryMode.TRIANGLES,
            indices=list(indices),
            instance_attributes={"colors": 1, "translate": 1},
            batch=None,
            group=None,
            position=("f", tuple(verts)),
            colors=("f", (1.0, 0.0, 0.0, 1.0)),
            translate=("f", (500.0, 500.0, 0.0)),
        )
    return make


def test_instancing_count(vlist_factory):
    """Ensure the instance count is correct."""
    verts = (
        0.0, 0.0, 0.0,
        1.0, 0.0, 0.0,
        1.0, 1.0, 0.0,
        0.0, 1.0, 0.0,
    )
    vlist = vlist_factory(verts)

    size = 128.0
    instance_count = 25
    for i in range(instance_count):
        vlist.create_instance(
            colors=(random.random(), random.random(), random.random(), 1.0),
            translate=(i * size, i * size, 0.0),
        )

    assert vlist.instance_bucket is not None
    assert vlist.instance_bucket.instance_count == instance_count + 1  # the initial list


def test_missing_instance_attribute_raises(vlist_factory):
    """Test that ensures that an exception is raised if an instance attribute is missing."""
    verts = (0.0,) * 12
    vlist = vlist_factory(verts)
    with pytest.raises(KeyError):
        vlist.create_instance(colors=(1,1,1,1))  # missing translate


def _divisor_of(loc: int) -> int:
    from pyglet.graphics.api.gl import gl
    val = gl.GLint()
    gl.glGetVertexAttribiv(loc, gl.GL_VERTEX_ATTRIB_ARRAY_DIVISOR, ctypes.byref(val))
    return int(val.value)


def test_attribute_divisors(shader_program, vlist_factory):
    """Ensure the attribute divisor is set correctly in the VAO."""
    vlist = vlist_factory((0.0,) * 12)

    # Bind the VAO that vlist configured
    vlist.instance_bucket.vao.bind()

    pos_loc = shader_program._attributes["position"].location
    col_loc = shader_program._attributes["colors"].location
    trn_loc = shader_program._attributes["translate"].location

    assert _divisor_of(pos_loc) == 0
    assert _divisor_of(col_loc) == 1
    assert _divisor_of(trn_loc) == 1


def test_instance_deletion(shader_program, vlist_factory):
    """Ensure the attribute divisor is set correctly in the VAO."""
    vlist = vlist_factory((0.0,) * 12)

    instances = []
    for i in range(10):
        instances.append(vlist.create_instance(colors=(1,1,1,1), translate=(100*i,100,0)))

    last_instance = instances[-1]

    # Delete instance in center.
    test_instance = instances[5]

    assert test_instance.slot == 6

    test_instance.delete()

    # Previous instance should stay the same
    assert instances[4].slot == 5

    # Last instance should move to fill the spot.
    assert last_instance.slot == 6


def test_instance_deletion(shader_program, vlist_factory):
    """Ensure the attribute divisor is set correctly in the VAO."""
    vlist = vlist_factory((0.0,) * 12)

    instances = []
    for i in range(10):
        instances.append(vlist.create_instance(colors=(1,1,1,1), translate=(100*i,100,0)))

    last_instance = instances[-1]

    # Delete instance in center.
    test_instance = instances[5]

    assert test_instance.slot == 6

    test_instance.delete()

    # Previous instance should stay the same
    assert instances[4].slot == 5

    # Last instance should move to fill the spot.
    assert last_instance.slot == 6
