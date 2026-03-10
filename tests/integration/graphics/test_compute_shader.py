import pytest

import pyglet

from tests.annotations import skip_graphics_api, GraphicsAPI


COMPUTE_SRC = """#version 430 core
layout(local_size_x = 1, local_size_y = 1, local_size_z = 1) in;

layout(rgba32f) uniform image2D img_output;

void main() {
    ivec2 texel_coord = ivec2(gl_GlobalInvocationID.xy);
    imageStore(img_output, texel_coord, vec4(1.0, 0.0, 0.0, 1.0));
}
"""


@skip_graphics_api(GraphicsAPI.GL2)
def test_compute_shader_program_creation(gl3_context):
    gl3_context.switch_to()

    if not (pyglet.graphics.api.have_version(4, 3) or pyglet.graphics.api.have_extension("GL_ARB_compute_shader")):
        pytest.skip("Compute shader is not supported by this context.")

    program = pyglet.graphics.ComputeShaderProgram(COMPUTE_SRC)
    try:
        assert program.id > 0
        assert "img_output" in program.uniforms
        assert program.max_work_group_invocations > 0
    finally:
        program.delete()
