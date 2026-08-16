"""Minimal Compute Shader example.

This example creates a Compute Shader from source,
attached a texture to it, and writes into the texture.
The texture is then saved to disk as a .png file.
"""

import pyglet

from pyglet.graphics.api.gl import GL_ALL_BARRIER_BITS, GL_RGBA8


compute_src = """#version 430 core
layout (local_size_x = 1, local_size_y = 1, local_size_z = 1) in;

layout(rgba8) uniform image2D img_output;

void main() {
    vec4 value = vec4(0.0, 0.0, 0.0, 1.0);
    ivec2 texel_coord = ivec2(gl_GlobalInvocationID.xy);
    value.r = float(texel_coord.x)/(gl_NumWorkGroups.x);
    value.g = float(texel_coord.y)/(gl_NumWorkGroups.y);

    imageStore(img_output, texel_coord, value);
}
"""

# Make a non-visible Window in order to create a Context:
window = pyglet.window.Window(visible=False)


program = pyglet.graphics.ComputeShaderProgram(compute_src)

# Create an RGBA32F Texture that we can bind to the ShaderProgram.
# This will be bound to "layout(rgba32f) ..." in the Shader source.
out_texture = pyglet.graphics.Texture.create(540, 540, internal_format_size=8, internal_format_type='B')

# The image binding unit in the shader needs to be set for the texture.
# The uniform set for the image can be used. In most cases this will be 0 unless explicitly
# changed via layout qualifier of layout(binding=X, rgba32f)
unit, level = program['img_output']

# Bind it to the uniform:
out_texture.bind_image_texture(unit=unit, level=level, fmt=GL_RGBA8)


with program:
    program.dispatch(out_texture.width, out_texture.height, 1, barrier=GL_ALL_BARRIER_BITS)


image = out_texture.get_image_data()
image.save('compute_output.png')

print("Saved 'compute_output.png'")
