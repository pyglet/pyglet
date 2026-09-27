"""Interactive checks for text-layout rendering layers."""

from __future__ import annotations

import pytest

import pyglet
from pyglet import app, graphics, text, window
from pyglet.graphics import Shader, ShaderProgram, VertexLayout
from pyglet.text import DropShadow, Stroke
from pyglet.text.document import FormattedDocument
from pyglet.window import key
from tests.base.interactive import InteractiveTestCase


TEXT_VERTEX_SOURCE = """#version 330 core
    in vec3 position;
    in vec4 colors;
    in vec3 tex_coords;
    in vec4 translation;
    in vec2 anchor;
    in float rotation;
    in float visible;

    out vec4 text_colors;
    out vec2 texture_coords;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

    void main()
    {
        mat4 m_rotation = mat4(1.0);
        vec3 v_anchor = vec3(anchor.x, anchor.y, 0.0);
        mat4 m_translate = mat4(1.0);
        m_translate[3][0] = translation.x;
        m_translate[3][1] = translation.y;
        m_translate[3][2] = translation.z;

        m_rotation[0][0] = cos(-radians(rotation));
        m_rotation[0][1] = sin(-radians(rotation));
        m_rotation[1][0] = -sin(-radians(rotation));
        m_rotation[1][1] = cos(-radians(rotation));

        gl_Position = window.projection * window.view * m_translate * m_rotation
            * vec4(position + v_anchor, 1.0) * visible;
        gl_Position.z -= translation.w * gl_Position.w;
        text_colors = colors;
        texture_coords = tex_coords.xy;
    }
"""

DECORATION_VERTEX_SOURCE = """#version 330 core
    in vec3 position;
    in vec4 colors;
    in vec4 translation;
    in vec2 anchor;
    in float rotation;
    in float visible;

    out vec4 vert_colors;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

    void main()
    {
        mat4 m_rotation = mat4(1.0);
        vec3 v_anchor = vec3(anchor.x, anchor.y, 0.0);
        mat4 m_translate = mat4(1.0);
        m_translate[3][0] = translation.x;
        m_translate[3][1] = translation.y;
        m_translate[3][2] = translation.z;

        m_rotation[0][0] = cos(-radians(rotation));
        m_rotation[0][1] = sin(-radians(rotation));
        m_rotation[1][0] = -sin(-radians(rotation));
        m_rotation[1][1] = cos(-radians(rotation));

        gl_Position = window.projection * window.view * m_translate * m_rotation
            * vec4(position + v_anchor, 1.0) * visible;
        gl_Position.z -= translation.w * gl_Position.w;
        vert_colors = colors;
    }
"""

GLYPH_FRAGMENT_SOURCE = """#version 330 core
    in vec4 text_colors;
    in vec2 texture_coords;
    out vec4 final_colors;
    uniform sampler2D text;

    void main()
    {
        final_colors = texture(text, texture_coords) * text_colors;
        final_colors.rgb = mix(final_colors.rgb, vec3(0.15, 0.9, 1.0), 0.45);
        if (final_colors.a < 0.01) discard;
    }
"""

EFFECT_FRAGMENT_SOURCE = """#version 330 core
    in vec4 text_colors;
    in vec2 texture_coords;
    out vec4 final_colors;
    uniform sampler2D text;

    void main()
    {
        final_colors = texture(text, texture_coords) * text_colors;
        final_colors.rgb = mix(final_colors.rgb, vec3(1.0, 0.3, 0.65), 0.7);
        if (final_colors.a < 0.01) discard;
    }
"""

DECORATION_FRAGMENT_SOURCE = """#version 330 core
    in vec4 vert_colors;
    out vec4 final_colors;

    void main()
    {
        final_colors = vert_colors;
        final_colors.rgb = mix(final_colors.rgb, vec3(1.0, 0.8, 0.15), 0.55);
        if (final_colors.a < 0.01) discard;
    }
"""


def make_text_shader(fragment_source: str) -> ShaderProgram:
    return ShaderProgram(
        Shader(TEXT_VERTEX_SOURCE, "vertex"),
        Shader(fragment_source, "fragment"),
        vertex_layout=VertexLayout(colors="4Bn"),
    )


class DepthLayerWindow(window.Window):
    """A window that exercises the text layer stack with independently toggled state."""

    background_color = (85, 55, 160, 255)
    underline_color = (255, 195, 50, 255)
    strikethrough_color = (255, 100, 180, 255)
    shadow = DropShadow(offset=(12, -12), color=(10, 10, 20, 230))
    stroke = Stroke(5, (50, 180, 255, 255), join="round")

    def __init__(self) -> None:
        config = pyglet.graphics.api.get_config(depth_size=24)
        super().__init__(1100, 720, "Text layer depth-sorting spot check", config=config, visible=False)
        self.context.set_clear_color(0.30, 0.30, 0.30, 1.0)
        self.batch = graphics.Batch()
        self.hud_batch = graphics.Batch()

        self.glyph_shader = make_text_shader(GLYPH_FRAGMENT_SOURCE)
        self.effect_shader = make_text_shader(EFFECT_FRAGMENT_SOURCE)
        self.decoration_shader = ShaderProgram(
            Shader(DECORATION_VERTEX_SOURCE, "vertex"),
            Shader(DECORATION_FRAGMENT_SOURCE, "fragment"),
            vertex_layout=VertexLayout(colors="4Bn"),
        )
        self.label = text.Label(
            "FEATURE LAYERED TEXT",
            font_size=56,
            x=self.width // 2,
            y=360,
            anchor_x="center",
            anchor_y="center",
            color=(245, 245, 255, 255),
            shadow=self.shadow,
            stroke=self.stroke,
            batch=self.batch,
            depth_sorting=True,
        )
        self.default_glyph_shader = self.label.program
        self.state = {
            "background": True,
            "foreground": True,
            "shadow": True,
            "stroke": True,
            "depth_sorting": True,
            "glyph_shader": False,
            "decoration_shader": False,
            "effect_shader": False,
        }
        self.layer_status = text.Label("", font_size=16, x=self.width // 2, y=48, anchor_x="center",
                                       color=(255, 225, 150, 255), batch=self.hud_batch)
        self.shader_status = text.Label("", font_size=16, x=self.width // 2, y=22, anchor_x="center",
                                        color=(255, 225, 150, 255), batch=self.hud_batch)
        self.reset()

    def apply_layers(self) -> None:
        self.label.set_style("background_color", self.background_color if self.state["background"] else None)
        self.label.set_style("underline", self.underline_color if self.state["foreground"] else None)
        self.label.set_style("strikethrough", self.strikethrough_color if self.state["foreground"] else None)
        self.label.shadow = self.shadow if self.state["shadow"] else None
        self.label.stroke = self.stroke if self.state["stroke"] else None

    def apply_shaders(self) -> None:
        self.label.program = self.glyph_shader if self.state["glyph_shader"] else self.default_glyph_shader
        self.label.decoration_shader = self.decoration_shader if self.state["decoration_shader"] else None
        self.label.effect_shader = self.effect_shader if self.state["effect_shader"] else None

    def update_status(self) -> None:
        self.layer_status.text = (
            f"depth (Space): {'on' if self.state['depth_sorting'] else 'off'}   "
            f"background (D): {'on' if self.state['background'] else 'off'}   "
            f"foreground (U): {'on' if self.state['foreground'] else 'off'}   "
            f"shadow (S): {'on' if self.state['shadow'] else 'off'}   "
            f"stroke (T): {'on' if self.state['stroke'] else 'off'}"
        )
        self.shader_status.text = (
            f"glyph shader (1): {'custom' if self.state['glyph_shader'] else 'default'}   "
            f"decoration shader (2): {'custom' if self.state['decoration_shader'] else 'default'}   "
            f"effect shader (3): {'custom' if self.state['effect_shader'] else 'default'}"
        )

    def reset(self) -> None:
        self.state.update(
            background=True,
            foreground=True,
            shadow=True,
            stroke=True,
            depth_sorting=True,
            glyph_shader=False,
            decoration_shader=False,
            effect_shader=False,
        )
        self.label.depth_sorting = True
        self.apply_layers()
        self.apply_shaders()
        self.update_status()

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        if symbol == key.ESCAPE:
            self.close()
            return
        if symbol == key.D:
            self.state["background"] = not self.state["background"]
            self.apply_layers()
        elif symbol == key.U:
            self.state["foreground"] = not self.state["foreground"]
            self.apply_layers()
        elif symbol == key.S:
            self.state["shadow"] = not self.state["shadow"]
            self.apply_layers()
        elif symbol == key.T:
            self.state["stroke"] = not self.state["stroke"]
            self.apply_layers()
        elif symbol == key.SPACE:
            self.state["depth_sorting"] = not self.state["depth_sorting"]
            self.label.depth_sorting = self.state["depth_sorting"]
        elif symbol == key._1:
            self.state["glyph_shader"] = not self.state["glyph_shader"]
            self.apply_shaders()
        elif symbol == key._2:
            self.state["decoration_shader"] = not self.state["decoration_shader"]
            self.apply_shaders()
        elif symbol == key._3:
            self.state["effect_shader"] = not self.state["effect_shader"]
            self.apply_shaders()
        elif symbol == key.R:
            self.reset()
            return
        else:
            return
        self.update_status()

    def on_draw(self) -> None:
        self.clear()
        self.batch.draw()
        self.hud_batch.draw()


class WordEffectWindow(window.Window):
    """A window that checks effects applied to document word ranges."""

    def __init__(self) -> None:
        config = pyglet.graphics.api.get_config(depth_size=24)
        super().__init__(1100, 720, "Per-word text effects spot check", config=config, visible=False)
        self.context.set_clear_color(0.30, 0.30, 0.30, 1.0)
        self.batch = graphics.Batch()
        self.hud_batch = graphics.Batch()

        document = FormattedDocument("SHADOW   STROKE   BOTH   FILL")
        document.set_style(0, len(document.text), {"font_size": 52, "color": (245, 245, 255, 255)})
        shadow_start = document.text.index("SHADOW")
        stroke_start = document.text.index("STROKE")
        both_start = document.text.index("BOTH")
        shadow = DropShadow(offset=(10, -10), color=(10, 10, 20, 230))
        stroke = Stroke(5, (50, 180, 255, 255), join="round")
        document.set_style(shadow_start, shadow_start + len("SHADOW"), {"shadow": shadow})
        document.set_style(stroke_start, stroke_start + len("STROKE"), {"stroke": stroke})
        document.set_style(
            both_start,
            both_start + len("BOTH"),
            {"shadow": shadow, "stroke": stroke},
        )

        self.label = text.DocumentLabel(
            document,
            x=self.width // 2,
            y=360,
            anchor_x="center",
            anchor_y="center",
            batch=self.batch,
            depth_sorting=True,
        )
        text.Label("Per-word document effect spot check", font_size=26, x=self.width // 2, y=660,
                   anchor_x="center", batch=self.hud_batch)
        text.Label("SHADOW: shadow only   STROKE: stroke only   BOTH: shadow + stroke   FILL: no effect",
                   font_size=16, x=self.width // 2, y=620, anchor_x="center",
                   color=(185, 200, 225, 255), batch=self.hud_batch)
        self.status = text.Label("", font_size=16, x=self.width // 2, y=48, anchor_x="center",
                                 color=(255, 225, 150, 255), batch=self.hud_batch)
        self.update_status()

    def update_status(self) -> None:
        self.status.text = f"depth sorting (Space): {'on' if self.label.depth_sorting else 'off'}   quit (Esc)"

    def on_key_press(self, symbol: int, modifiers: int) -> None:  # noqa: ARG002
        if symbol == key.ESCAPE:
            self.close()
        elif symbol == key.SPACE:
            self.label.depth_sorting = not self.label.depth_sorting
            self.update_status()

    def on_draw(self) -> None:
        self.clear()
        self.batch.draw()
        self.hud_batch.draw()


@pytest.mark.requires_user_action
class TextLayoutDepthSortingTest(InteractiveTestCase):
    def test_text_layer_depth_sorting(self) -> None:
        """Check text layer order after toggling effects, decorations, and shaders.

        Start with depth sorting enabled. The central label should show a purple
        background behind a dark shadow and cyan stroke, with white glyph fill
        on top and yellow/pink foreground decorations.

        Keys:
        D toggles the background decoration; U toggles underline and
        strikethrough; S toggles the drop shadow; T toggles the stroke; and
        Space toggles depth sorting. 1 toggles the glyph shader, 2 toggles the
        decoration shader, and 3 toggles the effect shader used by the shadow
        and stroke. R restores the initial state and Escape closes the window.

        Confirm that toggling every layer and shader preserves the expected
        order, then close the window to answer the interactive prompt.
        """
        self.window = DepthLayerWindow()
        self.window.set_visible()
        app.run()
        self.user_verify("Did every layer remain correctly ordered?", take_screenshot=False)

    def test_effects_per_word(self) -> None:
        """Check that document styles apply effects to only their word ranges.

        SHADOW should have only the dark shadow. STROKE should have only the
        cyan stroke. BOTH should have both effects, and FILL should remain plain.
        Toggle depth sorting with Space and verify that every word retains its
        assigned effect. Escape closes the window.
        """
        self.window = WordEffectWindow()
        self.window.set_visible()
        app.run()
        self.user_verify("Did each word retain its assigned effects?", take_screenshot=False)
