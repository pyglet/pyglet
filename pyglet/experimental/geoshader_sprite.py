from __future__ import annotations

import sys

import pyglet
from pyglet import clock, event, graphics, image
from pyglet.gl import *

_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run

vertex_source = """#version 150
    in vec3 position;
    in vec4 size;
    in vec2 scale;
    in vec4 color;
    in vec4 texture_uv;
    in float rotation;

    out vec4 geo_size;
    out vec2 geo_scale;
    out vec4 geo_color;
    out vec4 geo_tex_coords;
    out float geo_rotation;

    void main() {
        gl_Position = vec4(position, 1);
        geo_size = size;
        geo_scale = scale;
        geo_color = color;
        geo_tex_coords = texture_uv;
        geo_rotation = rotation;
    }
"""

geometry_source = """#version 150
    // We are taking single points from the vertex shader
    // and emitting 4 new vertices to create a quad/sprite.
    layout (points) in;
    layout (triangle_strip, max_vertices = 4) out;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;


    // Since geometry shader can take multiple values from a vertex
    // shader we need to define the inputs from it as arrays.
    // For our purposes, we just take single values (points).
    in vec4 geo_size[];
    in vec2 geo_scale[];
    in vec4 geo_color[];
    in vec4 geo_tex_coords[];
    in float geo_rotation[];

    out vec2 uv;
    out vec4 frag_color;

    void main() {

        // Unpack the image size and anchor
        vec2 size = geo_size[0].xy;
        vec2 anchor = geo_size[0].zw;

        // Grab the position value from the vertex shader
        vec3 center = gl_in[0].gl_Position.xyz;

        // This matrix controls the actual position of the sprite
        mat4 m_translate = mat4(1.0);
        m_translate[3][0] = center.x;
        m_translate[3][1] = center.y;
        m_translate[3][2] = center.z;

        mat4 m_rotation = mat4(1.0);
        m_rotation[0][0] =  cos(radians(-geo_rotation[0])); 
        m_rotation[0][1] =  sin(radians(-geo_rotation[0]));
        m_rotation[1][0] = -sin(radians(-geo_rotation[0]));
        m_rotation[1][1] =  cos(radians(-geo_rotation[0]));

        mat4 m_scale = mat4(1.0);
        m_scale[0][0] = geo_scale[0].x;
        m_scale[1][1] = geo_scale[0].y;

        // Final UV coords (left, bottom, right, top):
        float uv_l = geo_tex_coords[0].s;
        float uv_b = geo_tex_coords[0].t;
        float uv_r = geo_tex_coords[0].p;
        float uv_t = geo_tex_coords[0].q;

        // Emit a triangle strip to create a quad (4 vertices).
        // Prepare and reuse the transformation matrix and fragment color:
        mat4 m_pv = window.projection * window.view * m_translate * m_rotation * m_scale;
        frag_color = geo_color[0];

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
"""

fragment_source = """#version 150
    in vec2 uv;
    in vec4 frag_color;
    out vec4 final_color;

    uniform sampler2D sprite_texture;

    void main() {
        final_color = texture(sprite_texture, uv) * frag_color;
    }

"""

fragment_array_source = """#version 150 core
    in vec2 uv;
    in vec4 frag_color;
    
    out vec4 final_colors;

    uniform sampler2DArray sprite_texture;

    void main()
    {
        final_colors = texture(sprite_texture, uv) * frag_color;
    }
"""


def get_default_shader():
    return pyglet.gl.current_context.create_program((vertex_source, 'vertex'),
                                                    (geometry_source, 'geometry'),
                                                    (fragment_source, 'fragment'))


def get_default_array_shader():
    return pyglet.gl.current_context.create_program((vertex_source, 'vertex'),
                                                    (geometry_source, 'geometry'),
                                                    (fragment_array_source, 'fragment'))


class SpriteGroup(graphics.Group):
    """Shared sprite rendering group.

    The group is automatically coalesced with other sprite groups sharing the
    same parent group, texture and blend parameters.
    """

    def __init__(self, texture, blend_src, blend_dest, program, parent=None):
        """Create a sprite group.

        The group is created internally when a :py:class:`~pyglet.sprite.Sprite`
        is created; applications usually do not need to explicitly create it.

        :Parameters:
            `texture` : `~pyglet.image.Texture`
                The (top-level) texture containing the sprite image.
            `blend_src` : int
                OpenGL blend source mode; for example,
                ``GL_SRC_ALPHA``.
            `blend_dest` : int
                OpenGL blend destination mode; for example,
                ``GL_ONE_MINUS_SRC_ALPHA``.
            `program` : `~pyglet.graphics.shader.ShaderProgram`
                A custom ShaderProgram.
            `order` : int
                Change the order to render above or below other Groups.
            `parent` : `~pyglet.graphics.Group`
                Optional parent group.
        """
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


class Sprite(event.EventDispatcher):
    _batch = None
    _animation = None
    _frame_index = 0
    _paused = False
    _rotation = 0
    _scale = 1.0
    _scale_x = 1.0
    _scale_y = 1.0
    _visible = True
    _vertex_list = None
    group_class = SpriteGroup

    def __init__(self,
                 img, x=0, y=0, z=0,
                 blend_src=GL_SRC_ALPHA, blend_dest=GL_ONE_MINUS_SRC_ALPHA,
                 batch=None, group=None, subpixel=False, program=None):
        """Create a sprite.

        :Parameters:
            `img` : `~pyglet.image.AbstractImage` or `~pyglet.image.Animation`
                Image or animation to display.
            `x` : int
                X coordinate of the sprite.
            `y` : int
                Y coordinate of the sprite.
            `z` : int
                Z coordinate of the sprite.
            `blend_src` : int
                OpenGL blend source mode.  The default is suitable for
                compositing sprites drawn from back-to-front.
            `blend_dest` : int
                OpenGL blend destination mode.  The default is suitable for
                compositing sprites drawn from back-to-front.
            `batch` : `~pyglet.graphics.Batch`
                Optional batch to add the sprite to.
            `group` : `~pyglet.graphics.Group`
                Optional parent group of the sprite.
            `subpixel` : bool
                Allow floating-point coordinates for the sprite. By default,
                coordinates are restricted to integer values.
            `program` : `~pyglet.graphics.shader.ShaderProgram`
                A custom shader to use. This shader program must contain the
                exact same attribute names and types as the default shader.
                The class methods and properties depend on this, and will
                crash otherwise.
        """
        self._x = x
        self._y = y
        self._z = z
        self._img = img

        self._rgba = [255, 255, 255, 255]

        if isinstance(img, image.Animation):
            self._animation = img
            self._texture = img.frames[0].image.get_texture()
            self._next_dt = img.frames[0].duration
            if self._next_dt:
                clock.schedule_once(self._animate, self._next_dt)
        else:
            self._texture = img.get_texture()

        if not program:
            if isinstance(img, image.TextureArrayRegion):
                self._program = get_default_array_shader()
            else:
                self._program = get_default_shader()
        else:
            self._program = program

        self._batch = batch or graphics.get_default_batch()
        self._user_group = group
        self._group = self.group_class(self._texture, blend_src, blend_dest, self.program, group)
        self._subpixel = subpixel

        self._create_vertex_list()

    def _create_vertex_list(self):
        texture = self._texture
        self._vertex_list = self.program.vertex_list(
            1, GL_POINTS, self._batch, self._group,
            position=('f', (self._x, self._y, self._z)),
            size=('f', (texture.width, texture.height, texture.anchor_x, texture.anchor_y)),
            scale=('f', (self._scale_x, self._scale_y)),
            color=('Bn', self._rgba),
            texture_uv=('f', texture.uv),
            rotation=('f', (self._rotation,)))

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
        """Force immediate removal of the sprite from video memory.

        This is often necessary when using batches, as the Python garbage
        collector will not necessarily call the finalizer as soon as the
        sprite is garbage.
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
            duration = min(max(0, duration), frame.duration)
            clock.schedule_once(self._animate, duration)
            self._next_dt = duration
        else:
            self.dispatch_event('on_animation_end')

    @property
    def batch(self):
        """Graphics batch.

        The sprite can be migrated from one batch to another, or removed from
        its batch (for individual drawing).  Note that this can be an expensive
        operation.

        :type: :py:class:`pyglet.graphics.Batch`
        """
        return self._batch

    @batch.setter
    def batch(self, batch):
        if self._batch == batch:
            return

        if batch is not None and self._batch is not None:
            self._batch.migrate(self._vertex_list, GL_POINTS, self._group, batch)
            self._batch = batch
        else:
            self._vertex_list.delete()
            self._batch = batch
            self._create_vertex_list()

    @property
    def group(self):
        """Parent graphics group.

        The sprite can change its rendering group, however this can be an
        expensive operation.

        :type: :py:class:`pyglet.graphics.Group`
        """
        return self._group.parent

    @group.setter
    def group(self, group):
        if self._group.parent == group:
            return
        self._group = self.group_class(self._texture,
                                       self._group.blend_src,
                                       self._group.blend_dest,
                                       self._group.program,
                                       group)
        self._batch.migrate(self._vertex_list, GL_POINTS, self._group, self._batch)

    @property
    def image(self):
        """Image or animation to display.

        :type: :py:class:`~pyglet.image.AbstractImage` or
               :py:class:`~pyglet.image.Animation`
        """
        if self._animation:
            return self._animation
        return self._texture

    @image.setter
    def image(self, img):
        if self._animation is not None:
            clock.unschedule(self._animate)
            self._animation = None

        if isinstance(img, image.Animation):
            self._animation = img
            self._frame_index = 0
            self._set_texture(img.frames[0].image.get_texture())
            self._next_dt = img.frames[0].duration
            if self._next_dt:
                clock.schedule_once(self._animate, self._next_dt)
        else:
            self._set_texture(img.get_texture())

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
    def position(self):
        """The (x, y, z) coordinates of the sprite, as a tuple.

        :Parameters:
            `x` : int
                X coordinate of the sprite.
            `y` : int
                Y coordinate of the sprite.
            `z` : int
                Z coordinate of the sprite.
        """
        return self._x, self._y, self._z

    @position.setter
    def position(self, position):
        self._x, self._y, self._z = position
        self._vertex_list.position[:] = position

    @property
    def x(self):
        """X coordinate of the sprite.

        :type: int
        """
        return self._x

    @x.setter
    def x(self, x):
        self._x = x
        self._vertex_list.position[:] = x, self._y, self._z

    @property
    def y(self):
        """Y coordinate of the sprite.

        :type: int
        """
        return self._y

    @y.setter
    def y(self, y):
        self._y = y
        self._vertex_list.position[:] = self._x, y, self._z

    @property
    def z(self):
        """Z coordinate of the sprite.

        :type: int
        """
        return self._z

    @z.setter
    def z(self, z):
        self._z = z
        self._vertex_list.position[:] = self._x, self._y, z

    @property
    def rotation(self):
        """Clockwise rotation of the sprite, in degrees.

        The sprite image will be rotated about its image's (anchor_x, anchor_y)
        position.

        :type: float
        """
        return self._rotation

    @rotation.setter
    def rotation(self, rotation):
        self._rotation = rotation
        self._vertex_list.rotation[0] = self._rotation

    @property
    def scale(self):
        """Base Scaling factor.

        A scaling factor of 1 (the default) has no effect.  A scale of 2 will
        draw the sprite at twice the native size of its image.

        :type: float
        """
        return self._scale

    @scale.setter
    def scale(self, scale):
        self._scale = scale
        self._vertex_list.scale[:] = scale * self._scale_x, scale * self._scale_y

    @property
    def scale_x(self):
        """Horizontal scaling factor.

         A scaling factor of 1 (the default) has no effect.  A scale of 2 will
         draw the sprite at twice the native width of its image.

        :type: float
        """
        return self._scale_x

    @scale_x.setter
    def scale_x(self, scale_x):
        self._scale_x = scale_x
        self._vertex_list.scale[:] = self._scale * scale_x, self._scale * self._scale_y

    @property
    def scale_y(self):
        """Vertical scaling factor.

         A scaling factor of 1 (the default) has no effect.  A scale of 2 will
         draw the sprite at twice the native height of its image.

        :type: float
        """
        return self._scale_y

    @scale_y.setter
    def scale_y(self, scale_y):
        self._scale_y = scale_y
        self._vertex_list.scale[:] = self._scale * self._scale_x, self._scale * scale_y

    def update(self, x=None, y=None, z=None, rotation=None, scale=None, scale_x=None, scale_y=None):
        """Simultaneously change the position, rotation or scale.

        This method is provided for convenience. There is not much
        performance benefit to updating multiple Sprite attributes at once.

        :Parameters:
            `x` : int
                X coordinate of the sprite.
            `y` : int
                Y coordinate of the sprite.
            `z` : int
                Z coordinate of the sprite.
            `rotation` : float
                Clockwise rotation of the sprite, in degrees.
            `scale` : float
                Scaling factor.
            `scale_x` : float
                Horizontal scaling factor.
            `scale_y` : float
                Vertical scaling factor.
        """
        translations_outdated = False

        # only bother updating if the translation actually changed
        if x is not None:
            self._x = x
            translations_outdated = True
        if y is not None:
            self._y = y
            translations_outdated = True
        if z is not None:
            self._z = z
            translations_outdated = True

        if translations_outdated:
            self._vertex_list.position[:] = (self._x, self._y, self._z)

        if rotation is not None and rotation != self._rotation:
            self._rotation = rotation
            self._vertex_list.rotation[:] = rotation

        scales_outdated = False

        # only bother updating if the scale actually changed
        if scale is not None:
            self._scale = scale
            scales_outdated = True
        if scale_x is not None:
            self._scale_x = scale_x
            scales_outdated = True
        if scale_y is not None:
            self._scale_y = scale_y
            scales_outdated = True

        if scales_outdated:
            self._vertex_list.scale[:] = self._scale * self._scale_x, self._scale * self._scale_y

    @property
    def width(self):
        """Scaled width of the sprite.

        Invariant under rotation.

        :type: int
        """
        w = self._texture.width * abs(self._scale_x) * abs(self._scale)
        return w if self._subpixel else int(w)

    @width.setter
    def width(self, width):
        self.scale_x = width / (self._texture.width * abs(self._scale))

    @property
    def height(self):
        """Scaled height of the sprite.

        Invariant under rotation.

        :type: int
        """
        h = self._texture.height * abs(self._scale_y) * abs(self._scale)
        return h if self._subpixel else int(h)

    @height.setter
    def height(self, height):
        self.scale_y = height / (self._texture.height * abs(self._scale))

    @property
    def opacity(self):
        """Blend opacity.

        This property sets the alpha component of the colour of the sprite's
        vertices.  With the default blend mode (see the constructor), this
        allows the sprite to be drawn with fractional opacity, blending with the
        background.

        An opacity of 255 (the default) has no effect.  An opacity of 128 will
        make the sprite appear translucent.

        :type: int
        """
        return self._rgba[3]

    @opacity.setter
    def opacity(self, opacity):
        self._rgba[3] = opacity
        self._vertex_list.color[:] = self._rgba

    @property
    def color(self):
        """Blend color.

        This property sets the color of the sprite's vertices. This allows the
        sprite to be drawn with a color tint.

        The color is specified as an RGB tuple of integers '(red, green, blue)'.
        Each color component must be in the range 0 (dark) to 255 (saturated).

        :type: (int, int, int)
        """
        return self._rgba[:3]

    @color.setter
    def color(self, rgb):
        self._rgba[:3] = list(map(int, rgb))
        self._vertex_list.color[:] = self._rgba

    @property
    def visible(self):
        """True if the sprite will be drawn.

        :type: bool
        """
        return self._visible

    @visible.setter
    def visible(self, visible):
        self._visible = visible
        self._vertex_list.texture_uv[:] = (0, 0, 0, 0) if not visible else self._texture.uv

    @property
    def paused(self):
        """Pause/resume the Sprite's Animation

        If `Sprite.image` is an Animation, you can pause or resume
        the animation by setting this property to True or False.
        If not an Animation, this has no effect.

        :type: bool
        """
        return self._paused

    @paused.setter
    def paused(self, pause):
        if not hasattr(self, '_animation') or pause == self._paused:
            return
        if pause is True:
            clock.unschedule(self._animate)
        else:
            frame = self._animation.frames[self._frame_index]
            self._next_dt = frame.duration
            if self._next_dt:
                clock.schedule_once(self._animate, self._next_dt)
        self._paused = pause

    @property
    def frame_index(self):
        """The current Animation frame.

        If the `Sprite.image` is an `Animation`,
        you can query or set the current frame.
        If not an Animation, this will always
        be 0.

        :type: int
        """
        return self._frame_index

    @frame_index.setter
    def frame_index(self, index):
        # Bound to available number of frames
        if self._animation is None:
            return
        self._frame_index = max(0, min(index, len(self._animation.frames) - 1))

    def draw(self):
        """Draw the sprite at its current position.

        See the module documentation for hints on drawing multiple sprites
        efficiently.
        """
        self._group.set_state_recursive()
        self._vertex_list.draw(GL_POINTS)
        self._group.unset_state_recursive()

    def __del__(self):
        try:
            if self._vertex_list is not None:
                self._vertex_list.delete()
        except:
            pass

    if _is_pyglet_doc_run:
        def on_animation_end(self):
            """The sprite animation reached the final frame.

            The event is triggered only if the sprite has an animation, not an
            image.  For looping animations, the event is triggered each time
            the animation loops.

            :event:
            """


Sprite.register_event_type('on_animation_end')
