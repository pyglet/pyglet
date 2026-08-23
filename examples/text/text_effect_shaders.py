"""An example usage on how to use custom shaders with text strokes and drop shadows."""

import pyglet
from pyglet.text import DropShadow, LinearGradient, Stroke


EFFECT_VERTEX_SOURCE = """#version 330 core
    in vec3 position;
    in vec4 colors;
    in vec3 tex_coords;
    in vec3 translation;
    in vec2 anchor;
    in float rotation;
    in float visible;

    out vec4 text_colors;
    out vec2 texture_coords;
    out vec4 vert_position;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

    void main()
    {
        mat4 m_rotation = mat4(1.0);
        vec3 v_anchor = vec3(anchor.x, anchor.y, 0);
        mat4 m_anchor = mat4(1.0);
        mat4 m_translate = mat4(1.0);

        m_translate[3][0] = translation.x;
        m_translate[3][1] = translation.y;
        m_translate[3][2] = translation.z;

        m_rotation[0][0] = cos(-radians(rotation));
        m_rotation[0][1] = sin(-radians(rotation));
        m_rotation[1][0] = -sin(-radians(rotation));
        m_rotation[1][1] = cos(-radians(rotation));

        gl_Position = window.projection * window.view * m_translate * m_anchor
                    * m_rotation * vec4(position + v_anchor, 1.0) * visible;
        vert_position = vec4(position + translation + v_anchor, 1.0);
        text_colors = colors;
        texture_coords = tex_coords.xy;
    }
"""

NEON_STROKE_FRAGMENT_SOURCE = """#version 330 core
    in vec4 text_colors;
    in vec2 texture_coords;
    in vec4 vert_position;

    out vec4 final_colors;

    uniform sampler2D text;
    uniform float time;
    uniform bool scissor;
    uniform vec4 scissor_area;

    void main()
    {
        vec4 glyph = texture(text, texture_coords);
        float pulse = 0.5 + 0.5 * sin(time * 3.0 + vert_position.x * 0.04);
        vec3 neon = mix(vec3(0.15, 0.8, 1.0), vec3(1.0, 0.2, 0.65), pulse);
        final_colors = vec4(mix(text_colors.rgb, neon, 0.8), text_colors.a) * glyph;
        if (scissor == true) {
            if (vert_position.x < scissor_area[0]) discard;                     // left
            if (vert_position.y < scissor_area[1]) discard;                     // bottom
            if (vert_position.x > scissor_area[0] + scissor_area[2]) discard;   // right
            if (vert_position.y > scissor_area[1] + scissor_area[3]) discard;   // top
        }
    }
"""

BLURRED_SHADOW_FRAGMENT_SOURCE = """#version 330 core
    in vec4 text_colors;
    in vec2 texture_coords;
    in vec4 vert_position;

    out vec4 final_colors;

    uniform sampler2D text;
    uniform bool scissor;
    uniform vec4 scissor_area;
    

    void main()
    {
        vec2 texel = 1.0 / vec2(textureSize(text, 0));
        float alpha = 0.0;
        for (int x = -1; x <= 1; ++x) {
            for (int y = -1; y <= 1; ++y) {
                alpha += texture(text, texture_coords + vec2(x, y) * texel).a;
            }
        }
        final_colors = vec4(text_colors.rgb, text_colors.a * alpha / 9.0);
        if (scissor == true) {
            if (vert_position.x < scissor_area[0]) discard;                     // left
            if (vert_position.y < scissor_area[1]) discard;                     // bottom
            if (vert_position.x > scissor_area[0] + scissor_area[2]) discard;   // right
            if (vert_position.y > scissor_area[1] + scissor_area[3]) discard;   // top
        }
    }
"""


def create_effect_shader(fragment_source: str):
    return pyglet.graphics.ShaderProgram(
        pyglet.graphics.Shader(EFFECT_VERTEX_SOURCE, "vertex"),
        pyglet.graphics.Shader(fragment_source, "fragment"),
    ).get_attribute_view(colors="Bn")


window = pyglet.window.Window(960, 400, "Text Effect Shaders")
window.context.set_clear_color(0.16, 0.18, 0.26, 1.0)

pink_to_blue = LinearGradient((255, 90, 140, 255), (80, 185, 255, 255))
gold_to_green = LinearGradient((255, 215, 90, 255), (105, 255, 165, 255))
neon_stroke_shader = create_effect_shader(NEON_STROKE_FRAGMENT_SOURCE)
blurred_shadow_shader = create_effect_shader(BLURRED_SHADOW_FRAGMENT_SOURCE)
batch = pyglet.graphics.Batch()

labels = [
    pyglet.text.Label(
        "Animated neon stroke",
        font_size=42,
        x=window.width // 2,
        y=260,
        anchor_x="center",
        anchor_y="center",
        color=(245, 245, 250, 255),
        stroke=Stroke(3, gold_to_green, join="round"),
        effect_shader=neon_stroke_shader,
        batch=batch,
    ),
    pyglet.text.Label(
        "Blurred drop shadow",
        font_size=42,
        x=window.width // 2,
        y=130,
        anchor_x="center",
        anchor_y="center",
        color=(245, 245, 250, 255),
        shadow=DropShadow(offset=(5, -5), color=pink_to_blue),
        effect_shader=blurred_shadow_shader,
        batch=batch,
    ),
]

elapsed_time = 0.0


def update(dt: float) -> None:
    global elapsed_time
    elapsed_time += dt


pyglet.clock.schedule_interval(update, 1 / 60)


@window.event
def on_draw() -> None:
    window.clear()
    neon_stroke_shader["time"] = elapsed_time
    batch.draw()


pyglet.app.run()
