"""Simple example showing how to change the shader of a sprite."""
import pyglet
from pyglet.window import key


window = pyglet.window.Window(960, 540, caption="Sprite Shader Toggle", vsync=True)
batch = pyglet.graphics.Batch()

pyglet.resource.path = ["../resources"]
pyglet.resource.reindex()

image = pyglet.resource.texture("pyglet.png")
image.anchor_x = image.width // 2
image.anchor_y = image.height // 2

sprite = pyglet.sprite.Sprite(image, x=window.width // 2, y=window.height // 2, batch=batch)
sprite.scale = 2.0

# Keep the built-in default sprite program.
default_program = pyglet.sprite.get_default_shader()

# Vertex shader is based on default vertex shader.
vertex_source = """#version 150 core
    in vec3 translate;
    in vec4 colors;
    in vec3 tex_coords;
    in vec2 scale;
    in vec3 position;
    in float rotation;

    out vec4 vertex_colors;
    out vec3 texture_coords;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

    mat4 m_scale = mat4(1.0);
    mat4 m_rotation = mat4(1.0);
    mat4 m_translate = mat4(1.0);

    void main()
    {
        m_scale[0][0] = scale.x;
        m_scale[1][1] = scale.y;
        m_translate[3][0] = translate.x;
        m_translate[3][1] = translate.y;
        m_translate[3][2] = translate.z;
        m_rotation[0][0] =  cos(-radians(rotation));
        m_rotation[0][1] =  sin(-radians(rotation));
        m_rotation[1][0] = -sin(-radians(rotation));
        m_rotation[1][1] =  cos(-radians(rotation));

        gl_Position = window.projection * window.view * m_translate * m_rotation * m_scale * vec4(position, 1.0);

        vertex_colors = colors;
        texture_coords = tex_coords;
    }
"""

# Time based effect.
fragment_source = """#version 150 core
    in vec4 vertex_colors;
    in vec3 texture_coords;
    out vec4 final_colors;

    uniform sampler2D sprite_texture;
    uniform float u_time;

    void main()
    {
        vec2 uv = texture_coords.xy;
        vec4 base_color = texture(sprite_texture, uv) * vertex_colors;
        float pulse = 0.65 + 0.35 * sin(u_time * 3.0);
        float scan = 0.90 + 0.10 * sin((uv.y * 140.0) + (u_time * 8.0));
        final_colors = vec4(base_color.rgb * pulse * scan, base_color.a);
    }
"""

custom_program = pyglet.graphics.ShaderProgram(
    pyglet.graphics.Shader(vertex_source, "vertex"),
    pyglet.graphics.Shader(fragment_source, "fragment"),
)

using_custom_program = False

help_label = pyglet.text.Label(
    "SPACE: Toggle shader",
    x=10,
    y=10,
    anchor_x="left",
    anchor_y="bottom",
    batch=batch,
)

mode_label = pyglet.text.Label(
    "Mode: Default",
    x=10,
    y=40,
    anchor_x="left",
    anchor_y="bottom",
    batch=batch,
)


@window.event
def on_key_press(symbol, modifiers):
    global using_custom_program
    if symbol == key.SPACE:
        using_custom_program = not using_custom_program
        sprite.program = custom_program if using_custom_program else default_program
        mode_label.text = "Mode: Custom Shader" if using_custom_program else "Mode: Default Shader"


def update(dt):
    if using_custom_program:
        custom_program["u_time"] = update.time_elapsed
    update.time_elapsed += dt


update.time_elapsed = 0.0
pyglet.clock.schedule(update)


@window.event
def on_draw():
    window.clear()
    batch.draw()


pyglet.app.run()
