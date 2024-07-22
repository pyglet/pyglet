"""Allows for a somewhat generic multitextured sprite.

This sprite behaves just like regular sprites.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pyglet
from pyglet.gl import glActiveTexture, glBindTexture, glEnable, GL_BLEND, glBlendFunc, glDisable, glGetIntegerv, GLint
from pyglet.gl import GL_SRC_ALPHA, GL_TEXTURE0, GL_ONE_MINUS_SRC_ALPHA, GL_TRIANGLES, GL_MAX_TEXTURE_IMAGE_UNITS

if TYPE_CHECKING:
    from pyglet.image import Texture, AbstractImage, Animation
    from pyglet.graphics import Batch, Group, ShaderProgram


class MultiTextureSpriteGroup(pyglet.graphics.Group):
    """Shared Multi-texture Sprite rendering Group.

    The Group defines custom ``__eq__`` and ``__hash__`` methods, and so will be
    automatically coalesced with other MultiTexture Sprite Groups sharing the same
    parent Group, Textures, and blend parameters.
    """

    def __init__(self, textures: dict[str, Texture], blend_src: int, blend_dest: int,
                 program: ShaderProgram | None = None, parent: Group | None = None) -> None:
        """Create a sprite group for multiple textures and samplers.

        All textures must share the same target type.  The group is created internally
        when a :py:class:`~pyglet.multitexture_sprite.MultiTextureSprite` is created;
        applications usually do not need to explicitly create it.

        Args:
            textures:
                A dictionary of textures, with the keys being the GLSL sampler name.
            blend_src:
                OpenGL blend source mode; for example, ``GL_SRC_ALPHA``.
            blend_dest:
                OpenGL blend destination mode; for example, ``GL_ONE_MINUS_SRC_ALPHA``.
            program:
                A custom ShaderProgram.
            parent:
                Optional parent group.
        """
        super().__init__(parent=parent)
        self._textures = textures
        self.blend_src = blend_src
        self.blend_dest = blend_dest
        self.program = program

    def set_state(self) -> None:
        """Called before this group is drawn to setup the shader state.

        The shader program is activated than then all textures are bound and the
        blend mode is setup.
        """
        self.program.use()

        for idx, name in enumerate(self._textures):
            self.program[name] = idx

        for i, texture in enumerate(self._textures.values()):
            glActiveTexture(GL_TEXTURE0 + i)
            glBindTexture(texture.target, texture.id)

        glEnable(GL_BLEND)
        glBlendFunc(self.blend_src, self.blend_dest)

    def unset_state(self) -> None:
        """Called after all draw calls for the group have been made.

        When done the blend mode is disabled, the shader program is deactivated,
        and all textures are deactivated.
        """
        glDisable(GL_BLEND)
        self.program.stop()
        glActiveTexture(GL_TEXTURE0)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({[(name,texture) for name,texture in self._textures.items()]})'

    def __eq__(self, other: object | Group | MultiTextureSpriteGroup) -> bool:
        """Determines if this group is the same as the other group.

        The method is broken out like this to make it easier to follow and read.
        """
        if other.__class__ is not self.__class__:
            return False

        if len(self._textures) != len(other._textures):
            return False

        for name, texture in self._textures.items():
            if name not in other._textures:
                return False

            if texture.id != other._textures[name].id or texture.target != other._textures[name].target:
                return False

        # Made it this far so just check the remainder
        return (self.program is other.program and
                self.blend_src == other.blend_src and
                self.blend_dest == other.blend_dest)

    def __hash__(self) -> int:
        return hash((self.parent, self.program,
                           self.blend_src,
                           self.blend_dest) +
                          tuple([texture.id for texture in self._textures.values()]) +
                          tuple([texture.target for texture in self._textures.values()]))


# Allows the default shader to pick the appropriate sampler for the fragment shader
_SAMPLER_TYPES = {
    pyglet.gl.GL_TEXTURE_2D: "sampler2D",
    pyglet.gl.GL_TEXTURE_2D_ARRAY: "sampler2DArray"
}

# Allows the default shader to grab the correct coords based on texture type
_SAMPLER_COORDS = {
    pyglet.gl.GL_TEXTURE_2D: ".xy",
    pyglet.gl.GL_TEXTURE_2D_ARRAY: ""
}


def _get_default_mt_shader(images: dict[str, Texture]) -> ShaderProgram:
    """Creates the default multi-texture shader based on the dict of textures passed in.

    The default shader program will 'overlay' each texture layer on top of each other taking
    into account of the alpha channel of each texture.  Textures can be either normal
    2D textures or 2D texture arrays.  The maximum number of textures you can layer is
    determined by the maximum number of samplers you can have in a fragment shader.
    """
    max_tex = GLint()
    glGetIntegerv(GL_MAX_TEXTURE_IMAGE_UNITS, max_tex)
    assert len(images) <= max_tex.value, f"Only {max_tex.value} Texture Units are available."

    # Generate the default vertex shader
    in_tex_coords = '\n'.join([f"in vec3 {name}_coords;" for name in images.keys()])
    out_tex_coords = '\n'.join([f"out vec3 {name}_coords_frag;" for name in images.keys()])
    tex_coords_assignments = '\n'.join([f"{name}_coords_frag = {name}_coords;" for name in images.keys()])

    vertex_source = f"""
    #version 150 core

    in vec3 translate;
    in vec4 colors;
    in vec2 scale;
    in vec3 position;
    in float rotation;

    {in_tex_coords}

    out vec4 vertex_colors;

    {out_tex_coords}

    uniform WindowBlock {{
        mat4 projection;
        mat4 view;
    }} window;
    mat4 m_scale = mat4(1.0);
    mat4 m_rotation = mat4(1.0);
    mat4 m_translate = mat4(1.0);

    void main()
    {{
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

        {tex_coords_assignments}
    }}
    """

    in_tex_coords = '\n'.join([f"in vec3 {name}_coords_frag;" for name in images.keys()])
    uniform_samplers = '\n'.join([f"uniform {_SAMPLER_TYPES[tex.target]} {name};" for name,tex in images.items()])
    tex_operations = '\n'.join([f"  color = layer(texture({name}, {name}_coords_frag{_SAMPLER_COORDS[tex.target]}), color);" for name, tex in images.items()])
    fragment_source = f"""
    #version 150 core

    in vec4 vertex_colors;
    {in_tex_coords}

    out vec4 final_colors;

    {uniform_samplers}

    vec4 layer(vec4 foreground, vec4 background) {{
        return foreground * foreground.a + background * (1.0 - foreground.a);
    }}

    void main() {{
        vec4 color = vec4(0.0, 0.0, 0.0, 1.0);
        {tex_operations}
        final_colors = color * vertex_colors;
    }}
    """

    return pyglet.gl.current_context.create_program((vertex_source, 'vertex'), (fragment_source, 'fragment'))


class MultiTextureSprite(pyglet.sprite.Sprite):
    """Creates a multi-textured sprite.

    Multi-textured sprites behave just like regular sprites except they can
    contain multiple texture layers.  The default behavior is to overlay each
    layer on top of each other.  Each texture layer can be either a static image
    or an animation.  If the default behavior is not desired then a custom
    shader program can be supplied overriding the default program.

    The following complete example loads a 2 layer sprite and draws it to the
    screen::

      import pyglet

      batch = pyglet.graphics.Batch()

      logo_image = pyglet.image.load('logo.png')
      kitten_image = pyglet.image.load('kitten.png')
      sprite = pyglet.experimental.MultiTextureSprite({'kitten': kitten_image, 'logo': logo_image},
                                                      x=50, y=50, batch=batch)

      window = pyglet.window.Window()

      @window.event
      def on_draw():
        batch.draw()

      pyglet.app.run()

    If a custom program is provided then several assumptions are made by the
    MultiTextureSprite class.

    * The vertex shader is expected to have each texture coordinates passed in
      with variables named ``<name>_coords`` as vec3 types where ``<name>`` is
      the name of the layer given to the constructor.
    * The fragment shader is expected to have samplers of the appropriate type
      with variables named ``<name>`` where ``<name>`` is the name of the layer
      given to the constructor.

    """
    group_class = MultiTextureSpriteGroup

    def __init__(self,
                 images: dict[str, AbstractImage | Animation],
                 x: float = 0, y: float = 0, z: float = 0,
                 blend_src: int = GL_SRC_ALPHA,
                 blend_dest: int = GL_ONE_MINUS_SRC_ALPHA,
                 batch: Batch | None = None,
                 group: Group | None = None,
                 subpixel: bool = False,
                 program: ShaderProgram | None = None) -> None:
        """Create a Sprite instance.

        If the texture layers are different sizes then the largest texture by area is picked for
        size of the sprite and then the other layers are scaled to that size.

        Args:
            images:
                A dict object with the key being the name of the texture and the
                value is either an Animation or AbstractImage. Currently,
                each item must be of the same size.
            x:
                X coordinate of the sprite.
            y:
                Y coordinate of the sprite.
            z:
                Z coordinate of the sprite.
            blend_src:
                OpenGL blend source mode.  The default is suitable for
                compositing sprites drawn from back-to-front.
            blend_dest:
                OpenGL blend destination mode.  The default is suitable for
                compositing sprites drawn from back-to-front.
            batch:
                Optional batch to add the sprite to.
            group:
                Optional parent group of the sprite.
            subpixel:
                Allow floating-point coordinates for the sprite. By default,
                coordinates are restricted to integer values.
            program:
                A specific shader program to initialize the sprite with.  The
                default multi-texture overlay shader will be used if one is
                not provided.
        """
        # Ensure the images are textures and load them up into a dict.
        self._textures = {}
        self._texture = None
        for name, img in images.items():
            if isinstance(img, pyglet.image.Animation):
                # Grab the first frame
                self._textures[name] = img.frames[0].image.get_texture()
            else:
                self._textures[name] = img.get_texture()

            if not self._texture or (self._textures[name].height * self._textures[name].width) > (self._texture.height * self._texture.width):
                self._texture = self._textures[name]

        if not program:
            self._program = _get_default_mt_shader(self._textures)
        else:
            self._program = program

        # Right now don't call super unfortunently so we have to do everything ourselves
        self._x = x
        self._y = y
        self._z = z

        # Go through the images and find all animations
        self._animations = {}
        for name, img in images.items():
            if isinstance(img, pyglet.image.Animation):
                # Setup all of the animation things
                # The key needs to match the key for self._textures so we change it out as needed
                self._animations[name] = { "animation": img, "frame_idx": 0, "next_dt": img.frames[0].duration }
                if img.frames[0].duration:
                    pyglet.clock.schedule_once(self._animate, self._animations[name]["next_dt"], name)

        self._batch = batch
        self._blend_src = blend_src
        self._blend_dest = blend_dest
        self._user_group = group
        self._group = self.get_sprite_group()
        self._subpixel = subpixel
        # FIXME: This is to satisfy the main sprite code and should be done better
        #self._texture = list(self._textures.values())[0].get_texture()
        self._create_vertex_list()

    def delete(self) -> None:
        """Force immediate removal of the sprite from video memory.

        This method removes any scheduled animation calls and then calls
        pyglet.sprite.Sprite.delete method.
        """
        if self._animations:
            pyglet.clock.unschedule(self._animate)

        super().delete()

    def get_sprite_group(self) -> MultiTextureSpriteGroup:
        """Creates and returns a group to be used to render the sprite.

        This is used internally to create a consolidated group for rendering.
        """
        return self.group_class(self._textures, self._blend_src, self._blend_dest, self._program, self._user_group)

    def _animate(self, dt, key) -> None:
        if key in self._animations:
            animation = self._animations[key]
            animation["frame_idx"] += 1
            if animation["frame_idx"] >= len(animation["animation"].frames):
                animation["frame_idx"] = 0
                self.dispatch_event('on_animation_end')
                if self._vertex_list is None:
                    return

            frame = animation["animation"].frames[animation["frame_idx"]]

            if frame.duration is not None:
                duration = frame.duration - (animation["next_dt"] - dt)
                duration = min(max(0, duration), frame.duration)
                animation["next_dt"] = duration
                self._set_multi_texture(key, frame.image.get_texture())
                pyglet.clock.schedule_once(self._animate, animation["next_dt"], key)

    def _set_multi_texture(self, key, new_tex: Texture) -> None:
        if new_tex.id is not self._textures[key].id:
            # Need to make a shallow copy to allow the batch object
            # to correctly split this sprite from other sprite's groups.
            # if not then you will be modifing all othe the other sprites
            # textures dict object as well.
            self._textures = self._textures.copy()
            self._textures[key] = new_tex
            self._vertex_list.delete()
            self._group = self.get_sprite_group()
            self._create_vertex_list()
        else:
            self._textures[key] = new_tex
            getattr(self._vertex_list,f"{key}_coords")[:] = self._textures[key].tex_coords

    def _create_vertex_list(self) -> None:
        """
        Override so we can send over texture coords for each texture being used.
        """
        tex_coords = {}
        for name, tex in self._textures.items():
            tex_coords[f"{name}_coords"] = ('f', tex.tex_coords)

        self._vertex_list = self._program.vertex_list_indexed(
            4, GL_TRIANGLES, [0, 1, 2, 0, 2, 3], self._batch, self._group,
            position=('f', self._get_vertices()),
            colors=('Bn', self._rgba * 4),
            translate=('f', (self._x, self._y, self._z) * 4),
            scale=('f', (self._scale * self._scale_x, self._scale * self._scale_y) * 4),
            rotation=('f', (self._rotation,) * 4),
            **tex_coords)

    def set_frame_index(self, name: str, frame_idx: int) -> None:
        """Set the current Animation frame for the requested texture layer

        If the texture layer isn't an animation then this method has no effect.

        Args:
            name:
              The dict key given for the texture layer in the constructor
            frame_idx:
              The frame index to set for the given layer.
        """
        if name in self._animations:
            animation = self._animations[name]
            if frame_idx < len(animation["animation"].frames):
                animation["frame_idx"] = frame_idx
                frame = animation["animation"].frames[animation["frame_idx"]]
                self._set_multi_texture(name, frame.image.get_texture())

    def get_frame_index(self, name: str) -> int:
        """Get the current Animation frame for the requested texture layer

        If the texture layer isn't an animation then this method always returns 0.

        Args:
            name:
              The dict key given for the texture layer in the constructor
        """
        if name in self._animations:
            animation = self._animations[name]
            return animation["frame_idx"]

        return 0

    def get_layer(self, name: str) -> AbstractImage | Animation | None:
        """Return the requested layer.  If it is not found then None is returned

        Args:
            name:
              The dict key given for the texture layer in the constructor.
        """
        if name in self._animations:
            return self._animations[name]
        elif name in self._textures:
            return self._textures[name]

        return None

    def set_layer(self, name: str, img: AbstractImage | Animation) -> None:
        """Sets the layer to the new image or animation.

        This method has no effect if name is not a valid layer.  Note: if you
        want to swap out a layer which is an animation then this will cause
        all other animated layers for this sprite to pause until the swap is done.

        Args:
            name:
              The dict key given for the texture layer in the constructor
            img:
               The Image or Animation to set
        """
        if name in self._animations:
            # Need to stop all animations temporarly so we can swap the layer out
            pyglet.clock.unschedule(self._animate)
            self._animations.pop(name)

        # Grab the texture and replace what was there
        tex = None
        if isinstance(img, pyglet.image.Animation):
            # Add the animation and schedule it based on pause
            self._animations[name] = {"animation": img, "frame_idx": 0, "next_dt": img.frames[0].duration}
            if img.frames[0].duration and not self._paused:
                pyglet.clock.schedule_once(self._animate, self._animations[name]["next_dt"], name)

            tex = img.frames[0].image.get_texture()
        else:
            tex = img.get_texture()

        if tex:
            self._set_multi_texture(name, tex)

            if (tex.width * tex.height) > (self._texture.width * self._texture.height):
                self._texture = tex
                # Only update if we actually changed the "base" texture
                self._update_position()

    @property
    def frame_index(self) -> None:
        raise NotImplementedError("MultiTextureSprite does not support the frame_index property.  Use get_frame_index instead.")

    @frame_index.setter
    def frame_index(self, index: int) -> None:
        raise NotImplementedError("MultiTextureSprite does not support the frame_index property.  Use set_frame_index instead.")

    @property
    def image(self) -> None:
        raise NotImplementedError("MultiTextureSprite does not support the image property.  Use get_layer instead.")

    @image.setter
    def image(self, img: AbstractImage | Animation) -> None:
        raise NotImplementedError("MultiTextureSprite does not support the image property.  Use set_layer instead.")

    @property
    def paused(self) -> bool:
        return self._paused

    @paused.setter
    def paused(self, pause: bool) -> None:
        if not hasattr(self, '_animations') or pause == self._paused:
            return

        self._paused = pause

        if pause:
            pyglet.clock.unschedule(self._animate)
        else:
            # Kick off all animations again
            for name, animation in self._animations.items():
                frame = animation["animation"].frames[animation["frame_idx"]]
                if frame.duration:
                    animation["next_dt"] = frame.duration
                    pyglet.clock.schedule_once(self._animate, self._animations[name]["next_dt"], name)
