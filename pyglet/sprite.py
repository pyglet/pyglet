# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2022 pyglet contributors
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

"""Display positioned, scaled and rotated images.

A sprite is an instance of an image displayed on-screen.  Multiple sprites can
display the same image at different positions on the screen.  Sprites can also
be scaled larger or smaller, rotated at any angle and drawn at a fractional
opacity.

The following complete example loads a ``"ball.png"`` image and creates a
sprite for that image.  The sprite is then drawn in the window's
draw event handler::

    import pyglet

    ball_image = pyglet.image.load('ball.png')
    ball = pyglet.sprite.Sprite(ball_image, x=50, y=50)

    window = pyglet.window.Window()

    @window.event
    def on_draw():
        ball.draw()

    pyglet.app.run()

The sprite can be moved by modifying the :py:attr:`~pyglet.sprite.Sprite.x` and 
:py:attr:`~pyglet.sprite.Sprite.y` properties.  Other
properties determine the sprite's :py:attr:`~pyglet.sprite.Sprite.rotation`,
:py:attr:`~pyglet.sprite.Sprite.scale` and
:py:attr:`~pyglet.sprite.Sprite.opacity`.

By default sprite coordinates are restricted to integer values to avoid
sub-pixel artifacts.  If you require to use floats, for example for smoother
animations, you can set the ``subpixel`` parameter to ``True`` when creating
the sprite (:since: pyglet 1.2).

The sprite's positioning, rotation and scaling all honor the original
image's anchor (:py:attr:`~pyglet.image.AbstractImage.anchor_x`,
:py:attr:`~pyglet.image.AbstractImage.anchor_y`).


Drawing multiple sprites
========================

Sprites can be "batched" together and drawn at once more quickly than if each
of their ``draw`` methods were called individually.  The following example
creates one hundred ball sprites and adds each of them to a :py:class:`~pyglet.graphics.Batch`.  The
entire batch of sprites is then drawn in one call::

    batch = pyglet.graphics.Batch()

    ball_sprites = []
    for i in range(100):
        x, y = i * 10, 50
        ball_sprites.append(pyglet.sprite.Sprite(ball_image, x, y, batch=batch))

    @window.event
    def on_draw():
        batch.draw()

Sprites can be freely modified in any way even after being added to a batch,
however a sprite can belong to at most one batch.  See the documentation for
:py:mod:`pyglet.graphics` for more details on batched rendering, and grouping of
sprites within batches.

.. versionadded:: 1.1
"""

import sys

import pyglet

from pyglet.gl import *
from pyglet import clock
from pyglet import event
from pyglet import graphics
from pyglet import image

_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run


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

fragment_source = """#version 150 core
    in vec4 vertex_colors;
    in vec3 texture_coords;
    out vec4 final_colors;

    uniform sampler2D sprite_texture;

    void main()
    {
        final_colors = texture(sprite_texture, texture_coords.xy) * vertex_colors;
    }
"""

fragment_array_source = """#version 150 core
    in vec4 vertex_colors;
    in vec3 texture_coords;
    out vec4 final_colors;

    uniform sampler2DArray sprite_texture;

    void main()
    {
        final_colors = texture(sprite_texture, texture_coords) * vertex_colors;
    }
"""


def get_default_shader():
    try:
        return pyglet.gl.current_context.pyglet_sprite_default_shader
    except AttributeError:
        _default_vert_shader = graphics.shader.Shader(vertex_source, 'vertex')
        _default_frag_shader = graphics.shader.Shader(fragment_source, 'fragment')
        default_shader_program = graphics.shader.ShaderProgram(_default_vert_shader, _default_frag_shader)
        pyglet.gl.current_context.pyglet_sprite_default_shader = default_shader_program
        return pyglet.gl.current_context.pyglet_sprite_default_shader


def get_default_array_shader():
    try:
        return pyglet.gl.current_context.pyglet_sprite_default_array_shader
    except AttributeError:
        _default_vert_shader = graphics.shader.Shader(vertex_source, 'vertex')
        _default_array_frag_shader = graphics.shader.Shader(fragment_array_source, 'fragment')
        default_shader_program = graphics.shader.ShaderProgram(_default_vert_shader, _default_array_frag_shader)
        pyglet.gl.current_context.pyglet_sprite_default_array_shader = default_shader_program
        return pyglet.gl.current_context.pyglet_sprite_default_array_shader


class SpriteGroup(graphics.Group):
    """Shared sprite rendering group.

    The group is automatically coalesced with other sprite groups sharing the
    same parent group, texture and blend parameters.
    """

    def __init__(self, texture, blend_src, blend_dest, program, order=0, parent=None):
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
        super().__init__(order, parent)
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
        return "{0}({1})".format(self.__class__.__name__, self.texture)

    def __eq__(self, other):
        return (other.__class__ is self.__class__ and
                self.program is other.program and
                self.parent is other.parent and
                self.texture.target == other.texture.target and
                self.texture.id == other.texture.id and
                self.blend_src == other.blend_src and
                self.blend_dest == other.blend_dest)

    def __hash__(self):
        return hash((id(self.parent), id(self.program),
                     self.texture.id, self.texture.target,
                     self.blend_src, self.blend_dest))


class Sprite(event.EventDispatcher):
    """Instance of an on-screen image.

    See the module documentation for usage.
    """

    _batch = None
    _animation = None
    _frame_index = 0
    _paused = False
    _rotation = 0
    _opacity = 255
    _rgb = (255, 255, 255)
    _scale = 1.0
    _scale_x = 1.0
    _scale_y = 1.0
    _visible = True
    _vertex_list = None
    group_class = SpriteGroup

    def __init__(self,
                 img, x=0, y=0, z=0,
                 blend_src=GL_SRC_ALPHA,
                 blend_dest=GL_ONE_MINUS_SRC_ALPHA,
                 batch=None,
                 group=None,
                 subpixel=False):
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
        """
        self._x = x
        self._y = y
        self._z = z
        self._img = img

        if isinstance(img, image.Animation):
            self._animation = img
            self._texture = img.frames[0].image.get_texture()
            self._next_dt = img.frames[0].duration
            if self._next_dt:
                clock.schedule_once(self._animate, self._next_dt)
        else:
            self._texture = img.get_texture()

        self._batch = batch or graphics.get_default_batch()
        self._group = self.group_class(self._texture, blend_src, blend_dest, self.program, 0, group)
        self._subpixel = subpixel
        self._create_vertex_list()

    @property
    def program(self):
        if isinstance(self._img, image.TextureArrayRegion):
            program = get_default_array_shader()
        else:
            program = get_default_shader()

        return program

    def __del__(self):
        try:
            if self._vertex_list is not None:
                self._vertex_list.delete()
        except:
            pass

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

        # Easy way to break circular reference, speeds up GC
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
            self._batch.migrate(self._vertex_list, GL_TRIANGLES, self._group, batch)
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
                                       0,
                                       group)
        self._batch.migrate(self._vertex_list, GL_TRIANGLES, self._group, self._batch)

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
        self._update_position()

    def _set_texture(self, texture):
        if texture.id is not self._texture.id:
            self._group = self._group.__class__(texture,
                                                self._group.blend_src,
                                                self._group.blend_dest,
                                                self._group.program,
                                                0,
                                                self._group.parent)
            self._vertex_list.delete()
            self._texture = texture
            self._create_vertex_list()
        else:
            self._vertex_list.tex_coords[:] = texture.tex_coords
        self._texture = texture

    def _create_vertex_list(self):
        self._vertex_list = self.program.vertex_list_indexed(
            4, GL_TRIANGLES, [0, 1, 2, 0, 2, 3], self._batch, self._group,
            colors=('Bn', (*self._rgb, int(self._opacity)) * 4),
            translate=('f', (self._x, self._y, self._z) * 4),
            scale=('f', (self._scale*self._scale_x, self._scale*self._scale_y) * 4),
            rotation=('f', (self._rotation,) * 4),
            tex_coords=('f', self._texture.tex_coords))
        self._update_position()

    def _update_position(self):
        if not self._visible:
            self._vertex_list.position[:] = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        else:
            img = self._texture
            x1 = -img.anchor_x
            y1 = -img.anchor_y
            x2 = x1 + img.width
            y2 = y1 + img.height
            vertices = (x1, y1, 0, x2, y1, 0, x2, y2, 0, x1, y2, 0)

            if not self._subpixel:
                self._vertex_list.position[:] = tuple(map(int, vertices))
            else:
                self._vertex_list.position[:] = vertices

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
        self._vertex_list.translate[:] = position * 4

    @property
    def x(self):
        """X coordinate of the sprite.

        :type: int
        """
        return self._x

    @x.setter
    def x(self, x):
        self._x = x
        self._vertex_list.translate[:] = (x, self._y, self._z) * 4

    @property
    def y(self):
        """Y coordinate of the sprite.

        :type: int
        """
        return self._y

    @y.setter
    def y(self, y):
        self._y = y
        self._vertex_list.translate[:] = (self._x, y, self._z) * 4

    @property
    def z(self):
        """Z coordinate of the sprite.

        :type: int
        """
        return self._z

    @z.setter
    def z(self, z):
        self._z = z
        self._vertex_list.translate[:] = (self._x, self._y, z) * 4

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
        self._vertex_list.rotation[:] = (self._rotation,) * 4

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
        self._vertex_list.scale[:] = (scale * self._scale_x, scale * self._scale_y) * 4

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
        self._vertex_list.scale[:] = (self._scale * scale_x, self._scale * self._scale_y) * 4

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
        self._vertex_list.scale[:] = (self._scale * self._scale_x, self._scale * scale_y) * 4

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
            self._vertex_list.translate[:] = (self._x, self._y, self._z) * 4

        if rotation is not None and rotation != self._rotation:
            self._rotation = rotation
            self._vertex_list.rotation[:] = (rotation,) * 4

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
            self._vertex_list.scale[:] = (self._scale * self._scale_x, self._scale * self._scale_y) * 4

    @property
    def width(self):
        """Scaled width of the sprite.

        Read-only.  Invariant under rotation.

        :type: int
        """
        if self._subpixel:
            return self._texture.width * abs(self._scale_x) * abs(self._scale)
        else:
            return int(self._texture.width * abs(self._scale_x) * abs(self._scale))

    @property
    def height(self):
        """Scaled height of the sprite.

        Read-only.  Invariant under rotation.

        :type: int
        """
        if self._subpixel:
            return self._texture.height * abs(self._scale_y) * abs(self._scale)
        else:
            return int(self._texture.height * abs(self._scale_y) * abs(self._scale))

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
        return self._opacity

    @opacity.setter
    def opacity(self, opacity):
        self._opacity = opacity
        self._vertex_list.colors[:] = (*self._rgb, int(self._opacity)) * 4

    @property
    def color(self):
        """Blend color.

        This property sets the color of the sprite's vertices. This allows the
        sprite to be drawn with a color tint.

        The color is specified as an RGB tuple of integers '(red, green, blue)'.
        Each color component must be in the range 0 (dark) to 255 (saturated).

        :type: (int, int, int)
        """
        return self._rgb

    @color.setter
    def color(self, rgb):
        self._rgb = list(map(int, rgb))
        self._vertex_list.colors[:] = (*self._rgb, int(self._opacity)) * 4

    @property
    def visible(self):
        """True if the sprite will be drawn.

        :type: bool
        """
        return self._visible

    @visible.setter
    def visible(self, visible):
        self._visible = visible
        self._update_position()

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
        self._frame_index = max(0, min(index, len(self._animation.frames)-1))

    def draw(self):
        """Draw the sprite at its current position.

        See the module documentation for hints on drawing multiple sprites
        efficiently.
        """
        self._group.set_state_recursive()
        self._vertex_list.draw(GL_TRIANGLES)
        self._group.unset_state_recursive()

    if _is_pyglet_doc_run:
        def on_animation_end(self):
            """The sprite animation reached the final frame.

            The event is triggered only if the sprite has an animation, not an
            image.  For looping animations, the event is triggered each time
            the animation loops.

            :event:
            """


Sprite.register_event_type('on_animation_end')


class AdvancedSprite(pyglet.sprite.Sprite):
    """Is a sprite that lets you change the shader program during initialization and after
    For advanced users who understand shaders."""
    def __init__(self,
                 img, x=0, y=0, z=0,
                 blend_src=GL_SRC_ALPHA,
                 blend_dest=GL_ONE_MINUS_SRC_ALPHA,
                 batch=None,
                 group=None,
                 subpixel=False,
                 program=None):

        self._program = program

        if not program:
            if isinstance(img, image.TextureArrayRegion):
                self._program = get_default_array_shader()
            else:
                self._program = get_default_shader()

        super().__init__(img, x, y, z, blend_src, blend_dest, batch, group, subpixel)

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
                                       0,
                                       self._group)
        self._batch.migrate(self._vertex_list, GL_TRIANGLES, self._group, self._batch)
        self._program = program




