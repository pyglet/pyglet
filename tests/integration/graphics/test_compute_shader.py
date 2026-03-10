import pytest

import pyglet
from pyglet.graphics.shader import ShaderException

from tests.annotations import skip_graphics_api, GraphicsAPI


COMPUTE_SRC_GL = """#version 430 core
layout(local_size_x = 1, local_size_y = 1, local_size_z = 1) in;

layout(rgba32f) uniform image2D img_output;

void main() {
    ivec2 texel_coord = ivec2(gl_GlobalInvocationID.xy);
    imageStore(img_output, texel_coord, vec4(1.0, 0.0, 0.0, 1.0));
}
"""

COMPUTE_SRC_GLES = """#version 310 es
precision highp float;
layout(local_size_x = 1, local_size_y = 1, local_size_z = 1) in;

layout(rgba32f) uniform highp image2D img_output;

void main() {
    ivec2 texel_coord = ivec2(gl_GlobalInvocationID.xy);
    imageStore(img_output, texel_coord, vec4(1.0, 0.0, 0.0, 1.0));
}
"""


@skip_graphics_api(GraphicsAPI.GL2)
def test_compute_shader_program_creation(gl3_context):
    gl3_context.switch_to()
    backend = pyglet.options.backend

    if backend == "gles3":
        if not pyglet.graphics.api.have_version(3, 1):
            pytest.skip("Compute shader is not supported by this GLES/WebGL context.")
        compute_src = COMPUTE_SRC_GLES
    else:
        if not (pyglet.graphics.api.have_version(4, 3) or pyglet.graphics.api.have_extension("GL_ARB_compute_shader")):
            pytest.skip("Compute shader is not supported by this OpenGL context.")
        compute_src = COMPUTE_SRC_GL

    try:
        program = pyglet.graphics.ComputeShaderProgram(compute_src)
    except ShaderException as exc:
        error_text = str(exc)
        if ("Compute Shader not supported" in error_text
                or "Compute shaders require GLSL" in error_text
                or "GLSL 4.30 is not supported" in error_text):
            pytest.skip(f"Compute shader is unavailable for this runner/context: {error_text.splitlines()[-1]}")
        raise

    try:
        assert program.id > 0
        assert "img_output" in program.uniforms
        assert program.max_work_group_invocations > 0
    finally:
        program.delete()
