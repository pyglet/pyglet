"""Allows for a somewhat generic multitextured sprite.

This sprite behaves just like regular sprites.

"""
from __future__ import annotations

import pyglet
from pyglet.gl import glActiveTexture, GL_TEXTURE0, glBindTexture, glEnable, GL_BLEND, glBlendFunc, glDisable, \
    GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_TRIANGLES

class MultiTextureSpriteGroup(pyglet.sprite.SpriteGroup):
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
        self.textures = textures
        texture = list(self.textures.values())[0]
        self.target = texture.target
        super().__init__(texture, blend_src, blend_dest, program, parent)

    def set_state(self) -> None:
        self.program.use()

        for idx, name in enumerate(self.textures):
            self.program[name] = idx

        for i, texture in enumerate(self.textures.values()):
            glActiveTexture(GL_TEXTURE0 + i)
            glBindTexture(self.target, texture.id)

        glEnable(GL_BLEND)
        glBlendFunc(self.blend_src, self.blend_dest)

    def unset_state(self) -> None:
        glDisable(GL_BLEND)
        self.program.stop()
        glActiveTexture(GL_TEXTURE0)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.texture}-{self.texture.id})'

    def __eq__(self, other: object | Group | MultiTextureSpriteGroup) -> bool:
        """Determines if this group is the same as the other group.

        The method is broken out like this to make it easier to follow and read.
        """
        if other.__class__ is not self.__class__:
            return False

        # Check targets and ids
        for name, texture in self.textures.items():
            if name not in other.textures:
                return False

            if texture.id != other.textures[name].id or texture.target != other.texture.target:
                return False

        # Made it this far so just check the remainder
        return (self.program is other.program and
                self.blend_src == other.blend_src and
                self.blend_dest == other.blend_dest)

    def __hash__(self) -> int:
        tex_id = tuple([texture.id for texture in self.textures.values()])
        tex_target = tuple([texture.target for texture in self.textures.values()])
        return hash((self.parent,
                     self.blend_src, self.blend_dest) + tex_id + tex_target)


class MultiTextureSprite(pyglet.sprite.Sprite):
    """Creates a multi-textured sprite."""
    group_class = MultiTextureSpriteGroup

    def __init__(self,
                 images: list[AbstractImage | Animation],
                 x: float = 0, y: float = 0, z: float = 0,
                 blend_src: int = GL_SRC_ALPHA,
                 blend_dest: int = GL_ONE_MINUS_SRC_ALPHA,
                 batch: Batch | None = None,
                 group: Group | None = None,
                 subpixel: bool = False) -> None:
        """Create a Sprite instance.

        Args:
            images:
                A list of images or animations for the sprite.  Currently
                each item must be of the same target and size.
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
        """
        # Ensure the images are textures and load them up into a dict.
        self.textures = {}
        for idx, img in enumerate(images):
            if isinstance(img, pyglet.image.Animation):
                # Grab the first frame
                self.textures[f"tex_{idx}"] = img.frames[0].image.get_texture()
            else:
                self.textures[f"tex_{idx}"] = img.get_texture()
        assert all(tex.target for tex in self.textures.values()) is True, "All textures need to be the same target."

        # Create our new shader that handles multiple texture sprites.
        v_source = """#version 150 core
                      in vec3 translate;
                      in vec4 colors;"""

        # Create tex coordinate variables for each supplied texture
        for name,tex in self.textures.items():
            v_source += f"in vec3 {name}_coords;"

        v_source += """in vec2 scale;
                       in vec3 position;
                       in float rotation;

                       out vec4 vertex_colors;"""

        for name, tex in self.textures.items():
            v_source += f"out vec3 {name}_coords_frag;"

        v_source += """uniform WindowBlock
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

                       vertex_colors = colors;"""

        for name, tex in self.textures.items():
            v_source += f"{name}_coords_frag = {name}_coords;"

        v_source += "}"

        f_source = """#version 150 core
            in vec4 vertex_colors;"""
        for name, tex in self.textures.items():
            f_source += f"in vec3 {name}_coords_frag;"

        f_source += "out vec4 final_colors;"
        # For now each texture gets its own sampler.  This works even for atlases because
        # it is ok to pass in the same id for multiple samplers.  This limits the max
        # number of potential textures but makes generating the shader simpler and
        # increases the chance that other multi-textured sprites will be grouped together
        # for drawing.
        for name, tex in self.textures.items():
            f_source += f"uniform sampler2D {name};"

        f_source += """
            vec4 layer(vec4 foreground, vec4 background) {
                return foreground * foreground.a + background * (1.0 - foreground.a);
            }"""
        f_source += """

            void main()
            {
                vec4 color = vec4(0.0, 0.0, 0.0, 1.0);"""

        for name, tex in self.textures.items():
            f_source += f"color = layer(texture({name}, {name}_coords_frag.xy),color);"
        f_source += """
                final_colors = color * vertex_colors;
            }
        """
        # Creating the program this way allows for caching of and therefore efficent grouping
        program = pyglet.gl.current_context.create_program((v_source, 'vertex'), (f_source, 'fragment'))

        # Right now don't call super unfortunently so we have to do everything ourselves
        self._x = x
        self._y = y
        self._z = z

        # Go through the images and find all animations
        self._animations = {}
        # FIXME: Look at optimizing this with the loops above
        for idx, img in enumerate(images):
            if isinstance(img, pyglet.image.Animation):
                # Setup all of the animation things
                # The key needs to match the key for self.textures so we change it out as needed
                self._animations[f"tex_{idx}"] = { "animation": img, "frame_idx": 0, "next_dt": img.frames[0].duration }
                if img.frames[0].duration:
                    pyglet.clock.schedule_once(self._animate, self._animations[f"tex_{idx}"]["next_dt"], f"tex_{idx}")

        self._program = program
        self._batch = batch
        self._blend_src = blend_src
        self._blend_dest = blend_dest
        self._user_group = group
        self._group = self.get_sprite_group()
        self._subpixel = subpixel
        # FIXME: This is to satisfy the main sprite code and should be done better
        self._texture = list(self.textures.values())[0].get_texture()
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
        return self.group_class(self.textures, self._blend_src, self._blend_dest, self._program, self._user_group)

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
        if new_tex.id is not self.textures[key].id:
            self.textures[key] = new_tex
            self._vertex_list.delete()
            self._group = self.get_sprite_group()
            self._create_vertex_list()
        else:
            self.textures[key] = new_tex
            getattr(self._vertex_list,f"{key}_coords")[:] = self.textures[key].tex_coords

    def _create_vertex_list(self) -> None:
        """
        Override so we can send over texture coords for each texture being used.
        """
        tex_coords = {}
        for name, tex in self.textures.items():
            tex_coords[f"{name}_coords"] = ('f', tex.tex_coords)

        self._vertex_list = self.program.vertex_list_indexed(
            4, GL_TRIANGLES, [0, 1, 2, 0, 2, 3], self._batch, self._group,
            position=('f', self._get_vertices()),
            colors=('Bn', (*self._rgb, int(self._opacity)) * 4),
            translate=('f', (self._x, self._y, self._z) * 4),
            scale=('f', (self._scale * self._scale_x, self._scale * self._scale_y) * 4),
            rotation=('f', (self._rotation,) * 4),
            **tex_coords)

    def set_frame_index(self, tex_idx, frame_idx):
        """Set the current Animation frame for the requested texture layer

        If the texture layer isn't an animation then this method has no effect.
        """
        key = f"tex_{tex_idx}"
        if key in self._animations:
            animation = self._animations[key]
            if frame_idx < len(animation["animation"].frames):
                animation["frame_idx"] = frame_idx
                frame = animation["animation"].frames[animation["frame_idx"]]
                self._set_multi_texture(key, frame.image.get_texture())
