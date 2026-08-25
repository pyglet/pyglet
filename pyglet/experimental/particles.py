# Experimental GPU based particle system

from __future__ import annotations

import sys
import time

import pyglet
from pyglet import clock, event, graphics, image
from pyglet.enums import Anchor, BlendFactor, GeometryMode
from pyglet.graphics import Group
from pyglet.graphics.draw import DrawContext, BatchDrawOptions

_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run

vertex_source = """#version 150
    in vec3 position;
    in vec4 size;
    in vec4 scale;
    in vec4 velocity;
    in vec4 color_start;
    in vec4 color_end;
    in vec4 texture_uv;
    in float rotation;
    in float birth;

    out vec4 geo_size;
    out vec4 geo_scale;
    out vec4 geo_velocity;
    out vec4 geo_color_start;
    out vec4 geo_color_end;
    out vec4 geo_tex_coords;
    out float geo_rotation;
    out float geo_birth;
    out int geo_vert_id;

    void main() {
        gl_Position = vec4(position, 1);
        geo_size = size;
        geo_scale = scale;
        geo_velocity = velocity;
        geo_color_start = color_start;
        geo_color_end = color_end;
        geo_tex_coords = texture_uv;
        geo_rotation = rotation;
        geo_birth = birth;
        geo_vert_id = gl_VertexID;
    }
"""

geometry_source = """#version 150
    // We are taking single points from the vertex shader
    // and emitting 4 new vertices to create a quad.
    layout (points) in;
    layout (triangle_strip, max_vertices = 32) out;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

    uniform float time;

    // Since geometry shader can take multiple values from a vertex
    // shader we need to define the inputs from it as arrays.
    // For our purposes, we just take single values (points).
    in vec4 geo_size[];
    in vec4 geo_scale[];
    in vec4 geo_velocity[];
    in vec4 geo_color_start[];
    in vec4 geo_color_end[];
    in vec4 geo_tex_coords[];
    in float geo_rotation[];
    in float geo_birth[];
    in int geo_vert_id[];

    out vec2 uv;
    out vec4 frag_color;

    void main() {
        // Unpack the image size and anchor
        vec2 size = geo_size[0].xy;
        vec2 anchor = geo_size[0].zw;
        vec2 scale_start = geo_scale[0].xy;
        vec2 scale_end = geo_scale[0].zw;

        vec2 velocity = geo_velocity[0].xy;
        vec2 spread = geo_velocity[0].zw;

        float birth = geo_birth[0];
        float elapsed = time - birth;
        float repeater = mod(elapsed, 1.0);

        int vert_id = geo_vert_id[0];

        for(int i=0;i<8;++i){
            // TODO: user supplied rotation speed
            float time_scale = mod(elapsed - (i / 7.0), 1.0);
            float rotation = geo_rotation[0] + time_scale * 100;

            // TODO: user supplied X, Y velocities
            vec3 center = gl_in[0].gl_Position.xyz;
            center.x += time_scale * velocity.x * (spread.x * cos(vert_id + 1) * sin(i + 1));
            center.y += time_scale * velocity.y * (spread.y * sin(vert_id + 1) * cos(i + 1));

            // Interpolate between the start and end colors, based on the lifetime 
            // (end - start) * step + start
            frag_color = (geo_color_end[0] - geo_color_start[0]) * time_scale + geo_color_start[0]; 

            // Interpolate between the start and end scale, based on the lifetime 
            // (end - start) * step + start
            mat4 m_scale = mat4(1.0);
            m_scale[0][0] = ((scale_end - scale_start) * time_scale + scale_start).x;
            m_scale[1][1] = ((scale_end - scale_start) * time_scale + scale_start).y;

            // This matrix controls the actual position of the particles:
            mat4 m_translate = mat4(1.0);
            m_translate[3][0] = center.x;
            m_translate[3][1] = center.y;
            m_translate[3][2] = center.z;

            mat4 m_rotation = mat4(1.0);
            m_rotation[0][0] =  cos(radians(-rotation));
            m_rotation[0][1] =  sin(radians(-rotation));
            m_rotation[1][0] = -sin(radians(-rotation));
            m_rotation[1][1] =  cos(radians(-rotation));

            // Final UV coords (left, bottom, right, top):
            float uv_l = geo_tex_coords[0].s;
            float uv_b = geo_tex_coords[0].t;
            float uv_r = geo_tex_coords[0].p;
            float uv_t = geo_tex_coords[0].q;

            // Emit a triangle strip to create a quad (4 vertices).
            // Prepare and reuse the transformation matrix and fragment color:
            mat4 m_pv = window.projection * window.view * m_translate * m_rotation * m_scale;

            // Upper left
            gl_Position = m_pv * vec4(vec2(0.0, size.y) - anchor, 0.0, 1.0);
            uv = vec2(uv_l, uv_t);
            EmitVertex();

            // lower left
            gl_Position = m_pv * vec4(vec2(0.0, 0.0) - anchor, 0.0, 1.0);
            uv = vec2(uv_l, uv_b);
            EmitVertex();

            // upper right
            gl_Position = m_pv * vec4(vec2(size.x, size.y) - anchor, 0.0, 1.0);
            uv = vec2(uv_r, uv_t);
            EmitVertex();

            // lower right
            gl_Position = m_pv * vec4(vec2(size.x, 0.0) - anchor, 0.0, 1.0);
            uv = vec2(uv_r, uv_b);
            EmitVertex();

            // We are done with this triangle strip now
            EndPrimitive();

        }
    }
"""

fragment_source = """#version 150
    in vec2 uv;
    in vec4 frag_color;
    out vec4 final_color;

    uniform sampler2D particle_texture;

    void main() {
        final_color = texture(particle_texture, uv) * frag_color;
    }

"""


def get_default_shader():
    program = pyglet.graphics.api.get_cached_shader(
        "default_particles",
        (vertex_source, 'vertex'),
        (geometry_source, 'geometry'),
        (fragment_source, 'fragment'),
    )
    return program.get_attribute_view(color_start="Bn", color_end="Bn")


class EmitterGroup(Group):

    def __init__(self, texture, blend_src, blend_dest, program, parent=None):
        super().__init__(parent=parent)
        self.texture = texture
        self.set_shader_program(program)
        self.set_texture(texture, 0)
        self.set_blend(blend_src, blend_dest)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.texture})"


class Emitter(event.EventDispatcher):
    _batch = None
    _animation = None
    _frame_index = 0
    _anchor_x = 0.0
    _anchor_y = 0.0
    _anchor = None
    _paused = False
    _visible = True
    _vertex_list = None
    group_class = EmitterGroup

    def __init__(self, img, x, y, z, count, velocity, spread,
                 color_start=(255, 255, 255, 255), color_end=(255, 255, 255, 255),
                 scale_start=(1.0, 1.0), scale_end=(1.0, 1.0), rotation=0.0,
                 blend_src=BlendFactor.SRC_ALPHA, blend_dest=BlendFactor.ONE_MINUS_SRC_ALPHA,
                 batch=None, group=None, program=None,
                 anchor: Anchor | str | tuple[float, float] | None = None):

        self._img = img
        self._x = x
        self._y = y
        self._z = z
        self._count = count
        self._velocity = velocity + spread
        self._anchor_x = 0.0
        self._anchor_y = 0.0
        self._anchor = None
        if isinstance(anchor, tuple):
            self._anchor_x, self._anchor_y = anchor
        elif anchor is not None:
            self._anchor = Anchor(anchor)

        self._color_start = color_start
        self._color_end = color_end
        self._scale_start = scale_start
        self._scale_end = scale_end
        self._rotation = rotation

        if isinstance(img, image.Animation):
            self._animation = img
            self._texture = img.frames[0].image.get_texture()
            self._next_dt = img.frames[0].duration
            if self._next_dt:
                clock.schedule_once(self._animate, self._next_dt)
        else:
            self._texture = img.get_texture()

        self._resolve_anchor()

        self._program = program or get_default_shader()
        self._batch = batch
        self._blend_src = blend_src
        self._blend_dest = blend_dest
        self._user_group = group
        self._group = self.get_emitter_group()
        self._create_vertex_list()

    def _create_vertex_list(self):
        texture = self._texture
        count = self._count
        self._vertex_list = self.program.vertex_list(
            count, GeometryMode.POINTS, self._batch, self._group,
            position=(self._x, self._y, self._z) * count,

            size=(texture.width, texture.height, self._anchor_x, self._anchor_y) * count,
            scale=(self._scale_start + self._scale_end) * count,

            velocity=self._velocity * count,

            color_start=self._color_start * count,
            color_end=self._color_end * count,

            texture_uv=texture.uv * count,
            rotation=(self._rotation,) * count,
            birth=(time.perf_counter(),) * count)

    @property
    def program(self):
        return self._program

    @program.setter
    def program(self, program):
        if self._program == program:
            return
        self._program = program
        self._group = self.get_emitter_group()
        if (self._batch and
                self._batch.update_shader(self._vertex_list, GeometryMode.POINTS, self._group, program)):
            # Exit early if changing domain is not needed.
            return

        # Recreate vertex list.
        self._vertex_list.delete()
        self._create_vertex_list()

    def delete(self):
        """Force immediate removal of the emitter from video memory.

        This is often necessary when using batches, as the Python garbage
        collector will not necessarily call the finalizer immediately.
        """
        if self._animation:
            clock.unschedule(self._animate)
        if self._vertex_list:
            self._vertex_list.delete()
        self._vertex_list = None
        self._texture = None
        self._group = None

    def get_emitter_group(self):
        return self.group_class(self._texture, self._blend_src, self._blend_dest, self._program, self._user_group)

    def _animate(self, dt):
        self._frame_index += 1
        if self._frame_index >= len(self._animation.frames):
            self._frame_index = 0
            self.dispatch_event('on_animation_end')
            if self._vertex_list is None:
                return  # Deleted in event handler.

        frame = self._animation.frames[self._frame_index]
        self._set_texture(frame.image.get_texture())

        if frame.duration is not None:
            duration = frame.duration - (self._next_dt - dt)
            duration = min(max(0.0, duration), frame.duration)
            clock.schedule_once(self._animate, duration)
            self._next_dt = duration
        else:
            self.dispatch_event('on_animation_end')

    def _set_texture(self, texture):
        previous_size = self._texture.width, self._texture.height
        texture_changed = texture.key != self._texture.key
        self._texture = texture
        self._resolve_anchor()

        if texture_changed:
            self._group = self.get_emitter_group()
            if self._batch is not None:
                self._batch.migrate(self._vertex_list, GeometryMode.POINTS, self._group, self._batch)
            else:
                self._vertex_list.delete()
                self._create_vertex_list()
                return

        self._vertex_list.texture_uv[:] = texture.uv
        if self._anchor is not None or (texture.width, texture.height) != previous_size:
            self._update_anchor()

    def _update_anchor(self):
        texture = self._texture
        self._vertex_list.size[:] = (texture.width, texture.height, self._anchor_x, self._anchor_y) * self._count

    def _resolve_anchor(self):
        if self._anchor is None:
            return

        self._anchor_x, self._anchor_y = self._anchor.get_position(self._texture.width, self._texture.height)

    @property
    def blend_mode(self):
        """The current blend factors applied to this emitter."""
        return self._blend_src, self._blend_dest

    @blend_mode.setter
    def blend_mode(self, modes):
        src, dst = modes
        if src == self._blend_src and dst == self._blend_dest:
            return

        self._blend_src = src
        self._blend_dest = dst
        self._group = self.get_emitter_group()
        if self._batch is not None:
            self._batch.migrate(self._vertex_list, GeometryMode.POINTS, self._group, self._batch)

    @property
    def batch(self):
        """The batch that owns this emitter's vertex list."""
        return self._batch

    @batch.setter
    def batch(self, batch):
        if self._batch == batch:
            return

        if batch is not None and self._batch is not None:
            self._batch.migrate(self._vertex_list, GeometryMode.POINTS, self._group, batch)
            self._batch = batch
        else:
            self._vertex_list.delete()
            self._batch = batch
            self._create_vertex_list()

    @property
    def group(self):
        """The user-supplied parent group."""
        return self._user_group

    @group.setter
    def group(self, group):
        if self._user_group == group:
            return

        self._user_group = group
        self._group = self.get_emitter_group()
        if self._batch is not None:
            self._batch.migrate(self._vertex_list, GeometryMode.POINTS, self._group, self._batch)

    @property
    def anchor(self):
        """The named anchor position, or ``None`` when using a numeric anchor."""
        return self._anchor

    @anchor.setter
    def anchor(self, anchor):
        self._anchor = Anchor(anchor) if anchor is not None else None
        self._resolve_anchor()
        self._update_anchor()

    @property
    def anchor_x(self):
        """X coordinate of the particle anchor, relative to the image's left edge."""
        return self._anchor_x

    @anchor_x.setter
    def anchor_x(self, anchor_x):
        self._anchor = None
        self._anchor_x = anchor_x
        self._update_anchor()

    @property
    def anchor_y(self):
        """Y coordinate of the particle anchor, relative to the image's bottom edge."""
        return self._anchor_y

    @anchor_y.setter
    def anchor_y(self, anchor_y):
        self._anchor = None
        self._anchor_y = anchor_y
        self._update_anchor()

    @property
    def anchor_position(self):
        """The particle anchor's ``(x, y)`` offset from the image's lower-left corner."""
        return self._anchor_x, self._anchor_y

    @anchor_position.setter
    def anchor_position(self, position):
        self._anchor = None
        self._anchor_x, self._anchor_y = position
        self._update_anchor()

    @property
    def position(self) -> tuple[int | float, int | float, int | float]:
        return self._x, self._y, self._z

    @position.setter
    def position(self, position: tuple[int | float, int | float, int | float]):
        self._x, self._y, self._z = position
        self._vertex_list.position[:] = position

    def draw(self):
        """Draw the emitter without a batch."""
        ctx = pyglet.graphics.api.core.current_context
        draw_ctx = DrawContext(
            surface_ctx=ctx,
            backend_ctx=None,
            draw_pass=BatchDrawOptions().resolve(ctx),
            renderer=ctx.renderer,
        )
        draw_ctx.begin()
        self._group.set_state_recursive(draw_ctx)
        self._vertex_list.draw(GeometryMode.POINTS)
        self._group.unset_state_recursive(draw_ctx)

    if _is_pyglet_doc_run:
        def on_animation_end(self):
            """The emitter animation reached the final frame.

            The event is triggered only if the emitter has an animation, not an
            image. For looping animations, the event is triggered each time
            the animation loops.

            :event:
            """


Emitter.register_event_type('on_animation_end')


class ParticleManager:

    def __init__(self, img, lifespan, count, velocity,
                 spread=(10.0, 10.0),
                 color_start=(255, 255, 255, 255), color_end=(255, 255, 255, 255),
                 scale_start=(1.0, 1.0), scale_end=(1.0, 1.0), rotation=0.0,
                 batch=None, group=None,
                 anchor: Anchor | str | tuple[float, float] | None = None):

        self._img = img
        self.lifespan = lifespan
        self.count = count
        self.velocity = velocity
        self.spread = spread
        self.color_start = color_start
        self.color_end = color_end
        self.scale_start = scale_start
        self.scale_end = scale_end
        self.rotation = rotation
        self._anchor_x = 0.0
        self._anchor_y = 0.0
        self._anchor = None
        if isinstance(anchor, tuple):
            self._anchor_x, self._anchor_y = anchor
        elif anchor is not None:
            self._anchor = Anchor(anchor)

        self._batch = batch
        self._group = group
        self._program = get_default_shader()
        clock.schedule_interval(self._update_shader_time, 1 / 60)

    def _update_shader_time(self, dt):
        self._program['time'] = time.perf_counter()

    @property
    def anchor(self):
        """The named anchor position, or ``None`` when using a numeric anchor."""
        return self._anchor

    @anchor.setter
    def anchor(self, anchor):
        self._anchor = Anchor(anchor) if anchor is not None else None

    @property
    def anchor_x(self):
        """X coordinate of the particle anchor, relative to the image's left edge."""
        return self._anchor_x

    @anchor_x.setter
    def anchor_x(self, anchor_x):
        self._anchor = None
        self._anchor_x = anchor_x

    @property
    def anchor_y(self):
        """Y coordinate of the particle anchor, relative to the image's bottom edge."""
        return self._anchor_y

    @anchor_y.setter
    def anchor_y(self, anchor_y):
        self._anchor = None
        self._anchor_y = anchor_y

    @property
    def anchor_position(self):
        """The particle anchor's ``(x, y)`` offset from the image's lower-left corner."""
        return self._anchor_x, self._anchor_y

    @anchor_position.setter
    def anchor_position(self, position):
        self._anchor = None
        self._anchor_x, self._anchor_y = position

    @staticmethod
    def _delete_callback(dt, emitter):
        emitter.delete()

    def create_emitter(self, x, y, z=0):
        emitter = Emitter(self._img, x, y, z, self.count, self.velocity, self.spread,
                          color_start=self.color_start, color_end=self.color_end,
                          scale_start=self.scale_start, scale_end=self.scale_end, rotation=self.rotation,
                          batch=self._batch, group=self._group, program=self._program,
                          anchor=self._anchor if self._anchor is not None else self.anchor_position)
        pyglet.clock.schedule_once(self._delete_callback, self.lifespan, emitter)
        return emitter


if __name__ == "__main__":
    window = pyglet.window.Window(960, 540, caption="ParticleManager Demo", resizable=True)

    batch = graphics.Batch()

    label = pyglet.text.Label("Click and drag.", x=5, y=5, batch=batch)

    particle_img = image.SolidColorImagePattern((255, 255, 255, 255)).create_image(8, 8)
    manager = ParticleManager(
        particle_img,
        lifespan=1.0,
        count=12,
        velocity=(100.0, 80.0),
        spread=(0.30, 0.30),
        color_start=(255, 200, 80, 220),
        color_end=(255, 40, 20, 0),
        scale_start=(0.4, 0.4),
        scale_end=(1.2, 1.2),
        rotation=0.0,
        batch=batch,
    )

    @window.event
    def on_draw():
        window.clear()
        batch.draw()

    @window.event
    def on_mouse_press(x, y, button, modifiers):
        manager.create_emitter(x, y)

    @window.event
    def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
        manager.create_emitter(x, y)

    pyglet.app.run()
