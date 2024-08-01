# Experimental GPU based particle system

from __future__ import annotations

import sys
import time

import pyglet
from pyglet import clock, event, graphics, image
from pyglet.gl import *

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
    return pyglet.gl.current_context.create_program((vertex_source, 'vertex'),
                                                    (geometry_source, 'geometry'),
                                                    (fragment_source, 'fragment'))


class EmitterGroup(graphics.Group):
    def __init__(self, texture, blend_src, blend_dest, program, parent=None):
        super().__init__(parent=parent)
        self.texture = texture
        self.blend_src = blend_src
        self.blend_dest = blend_dest
        self.program = program

    def set_state(self):
        self.program.use()

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(self.texture.target, self.texture.id)

        glEnable(GL_BLEND)
        glBlendFunc(self.blend_src, self.blend_dest)

    def unset_state(self):
        glDisable(GL_BLEND)
        self.program.stop()

    def __repr__(self):
        return f"{self.__class__.__name__}({self.texture})"

    def __eq__(self, other):
        return (other.__class__ is self.__class__ and
                self.program is other.program and
                self.parent == other.parent and
                self.texture.target == other.texture.target and
                self.texture.id == other.texture.id and
                self.blend_src == other.blend_src and
                self.blend_dest == other.blend_dest)

    def __hash__(self):
        return hash((self.program, self.parent,
                     self.texture.id, self.texture.target,
                     self.blend_src, self.blend_dest))


class Emitter(event.EventDispatcher):
    _batch = None
    _animation = None
    _frame_index = 0
    _paused = False
    _rotation = 0
    _visible = True
    _vertex_list = None
    group_class = EmitterGroup

    def __init__(self, img, x, y, z, count, velocity, spread,
                 color_start=(255, 255, 255, 255), color_end=(255, 255, 255, 255),
                 scale_start=(1.0, 1.0), scale_end=(1.0, 1.0),
                 blend_src=GL_SRC_ALPHA, blend_dest=GL_ONE_MINUS_SRC_ALPHA,
                 batch=None, group=None, program=None):

        self._img = img
        self._x = x
        self._y = y
        self._z = z
        self._count = count
        self._velocity = velocity + spread

        self._color_start = color_start
        self._color_end = color_end
        self._scale_start = scale_start
        self._scale_end = scale_end

        if isinstance(img, image.Animation):
            self._animation = img
            self._texture = img.frames[0].image.get_texture()
            self._next_dt = img.frames[0].duration
            if self._next_dt:
                clock.schedule_once(self._animate, self._next_dt)
        else:
            self._texture = img.get_texture()

        self._program = program or get_default_shader()
        self._batch = batch or graphics.get_default_batch()
        self._user_group = group
        self._group = self.group_class(self._texture, blend_src, blend_dest, self.program, group)
        self._create_vertex_list()

    def _create_vertex_list(self):
        texture = self._texture
        count = self._count
        self._vertex_list = self.program.vertex_list(
            count, GL_POINTS, self._batch, self._group,
            position=('f', (self._x, self._y, self._z) * count),

            size=('f', (texture.width, texture.height, texture.anchor_x, texture.anchor_y) * count),
            scale=('f', (self._scale_start + self._scale_end) * count),

            velocity=('f', self._velocity * count),

            color_start=('Bn', self._color_start * count),
            color_end=('Bn', self._color_end * count),

            texture_uv=('f', texture.uv * count),
            rotation=('f', (self._rotation,) * count),
            birth=('f', (time.perf_counter(),) * count))

    @property
    def program(self):
        return self._program

    @program.setter
    def program(self, program):
        if self._program == program:
            return
        self._group = self.group_class(self._texture,
                                       self._group.blend_src,
                                       self._group.blend_dest,
                                       program,
                                       self._user_group)
        if (self._batch and
                self._batch.update_shader(self._vertex_list, GL_POINTS, self._group, program)):
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
        self._vertex_list.delete()
        self._vertex_list = None
        self._texture = None
        self._group = None

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
        if texture.id is not self._texture.id:
            self._group = self._group.__class__(texture,
                                                self._group.blend_src,
                                                self._group.blend_dest,
                                                self._group.program,
                                                self._group.parent)
            self._vertex_list.delete()
            self._texture = texture
            self._create_vertex_list()
        else:
            self._vertex_list.texture_uv[:] = texture.uv
        self._texture = texture

    @property
    def position(self) -> tuple[int | float, int | float, int | float]:
        return self._x, self._y, self._z

    @position.setter
    def position(self, position: tuple[int | float, int | float, int | float]):
        self._x, self._y, self._z = position
        self._vertex_list.position[:] = position

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
                 scale_start=(1.0, 1.0), scale_end=(1.0, 1.0),
                 batch=None, group=None):

        self._img = img
        self._lifespan = lifespan
        self._count = count
        self._velocity = velocity
        self._spread = spread
        self._color_start = color_start
        self._color_end = color_end
        self._scale_start = scale_start
        self._scale_end = scale_end

        self._batch = batch
        self._group = group
        self._program = get_default_shader()
        clock.schedule_interval(self._update_shader_time, 1 / 60)

        # TODO: remove debug
        self.total_number = 0
        self.total_label = pyglet.text.Label("particles: 0", 10, 10, dpi=256, color=(10, 200, 10), batch=batch)

    def _update_shader_time(self, dt):
        self._program['time'] = time.perf_counter()

    def _delete_callback(self, dt, emitter):
        emitter.delete()

        # TODO: remove debug
        self.total_number -= 1
        self.total_label.text = f"particles: {self.total_number * self._count * 8!s}"

    def create_emitter(self, x, y, z=0):
        emitter = Emitter(self._img, x, y, z, self._count, self._velocity, self._spread,
                          color_start=self._color_start, color_end=self._color_end,
                          scale_start=self._scale_start, scale_end=self._scale_end,
                          batch=self._batch, group=self._group)
        pyglet.clock.schedule_once(self._delete_callback, self._lifespan, emitter)

        # TODO: remove debug
        self.total_number += 1
        self.total_label.text = f"particles: {self.total_number * self._count * 8!s}"

        return emitter
