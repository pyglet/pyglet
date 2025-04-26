"""Minimal Compute Shader example.

This example creates a Compute Shader from source,
attached a texture to it, and writes into the texture.
The texture is then saved to disk as a .png file.
"""

import pyglet

from pyglet.gl import GL_RGBA32F, GL_ALL_BARRIER_BITS


compute_src = """#version 430 core
layout (local_size_x = 1, local_size_y = 1, local_size_z = 1) in;

layout(rgba32f) uniform image2D img_output;

void main() {
    vec4 value = vec4(0.0, 0.0, 0.0, 1.0);
    ivec2 texel_coord = ivec2(gl_GlobalInvocationID.xy);
    value.r = float(texel_coord.x)/(gl_NumWorkGroups.x);
    value.g = float(texel_coord.y)/(gl_NumWorkGroups.y);

    imageStore(img_output, texel_coord, value);
}
"""

program = pyglet.graphics.shader.ComputeShaderProgram(compute_src)

# Create an RGBA32F Texture that we can bind to the ShaderProgram.
out_texture = pyglet.image.Texture.create(540, 540, internalformat=GL_RGBA32F)

# The image binding unit in the shader needs to be set for the texture.
# The uniform set for the image can be used. In most cases this will be 0 unless explicitly
# changed via layout qualifier of layout(binding=X, rgba32f)
output_binding = program['img_output']
out_texture.bind_image_texture(unit=output_binding)


with program:
    program.dispatch(out_texture.width, out_texture.height, 1, barrier=GL_ALL_BARRIER_BITS)


out_texture.save('compute_output.png')
print("Saved 'compute_output.png'")
