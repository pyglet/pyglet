import pyglet

from pyglet import clock
from pyglet import graphics
from pyglet import image

from pyglet.gl import GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_POINTS
from pyglet.sprite import Sprite, SpriteGroup

############################

vertex_src = """#version 150
    in vec2 position;
    in vec4 size;
    in vec4 color;
    in vec4 tex_coords;
    in float rotation;

    out vec4 geo_size;
    out vec4 geo_color;
    out vec4 geo_tex_coords;
    out float geo_rotation;

    void main() {
        gl_Position = vec4(position, 0, 1);
        geo_size = size;
        geo_color = color;
        geo_tex_coords = tex_coords;
        geo_rotation = rotation;
    }
"""

geometry_src = """#version 150
    // We are taking single points form the vertex shader
    // and emitting 4 new vertices creating a quad/sprites
    layout (points) in;
    layout (triangle_strip, max_vertices = 4) out;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;


    // Since geometry shader can take multiple values from a vertex
    // shader we need to define the inputs from it as arrays.
    // In our instance we just take single values (points)
    in vec4 geo_size[];
    in vec4 geo_color[];
    in vec4 geo_tex_coords[];
    in float geo_rotation[];

    out vec2 uv;
    out vec4 frag_color;

    void main() {

        // We grab the position value from the vertex shader
        vec2 center = gl_in[0].gl_Position.xy;

        // Calculate the half size of the sprites for easier calculations
        vec2 hsize = geo_size[0].xy / 2.0;

        // Convert the rotation to radians
        float angle = radians(-geo_rotation[0]);

        // Create a scale vector
        vec2 scale = vec2(geo_size[0][2], geo_size[0][3]);

        // Create a 2d rotation matrix
        mat2 rot = mat2(cos(angle), sin(angle),
                       -sin(angle), cos(angle));

        // Calculate the left, bottom, right, top:
        float tl = geo_tex_coords[0].s;
        float tb = geo_tex_coords[0].t;
        float tr = geo_tex_coords[0].s + geo_tex_coords[0].p;
        float tt = geo_tex_coords[0].t + geo_tex_coords[0].q;

        // Emit a triangle strip creating a quad (4 vertices).
        // Here we need to make sure the rotation is applied before we position the sprite.
        // We just use hardcoded texture coordinates here. If an atlas is used we
        // can pass an additional vec4 for specific texture coordinates.
        // Each EmitVertex() emits values down the shader pipeline just like a single
        // run of a vertex shader, but in geomtry shaders we can do it multiple times!

        // Upper left
        gl_Position = window.projection * window.view * vec4(rot * vec2(-hsize.x, hsize.y) * scale + center, 0.0, 1.0);
        uv = vec2(tl, tt);
        frag_color = geo_color[0];
        EmitVertex();

        // lower left
        gl_Position = window.projection * window.view * vec4(rot * vec2(-hsize.x, -hsize.y) * scale + center, 0.0, 1.0);
        uv = vec2(tl, tb);
        frag_color = geo_color[0];
        EmitVertex();

        // upper right
        gl_Position = window.projection * window.view * vec4(rot * vec2(hsize.x, hsize.y) * scale + center, 0.0, 1.0);
        uv = vec2(tr, tt);
        frag_color = geo_color[0];
        EmitVertex();

        // lower right
        gl_Position = window.projection * window.view * vec4(rot * vec2(hsize.x, -hsize.y) * scale + center, 0.0, 1.0);
        uv = vec2(tr, tb);
        frag_color = geo_color[0];
        EmitVertex();

        // We are done with this triangle strip now
        EndPrimitive();
    }
"""

fragment_src = """#version 150
    in vec2 uv;
    in vec4 frag_color;

    out vec4 final_color;

    uniform sampler2D sprite_texture;

    void main() {
        final_color = texture(sprite_texture, uv) * frag_color;
    }

"""


def get_geo_shader():
    try:
        return pyglet.gl.current_context.pyglet_sprite_geo_shader
    except AttributeError:
        new_vert_shader = graphics.shader.Shader(vertex_src, 'vertex')
        new_geom_shader = graphics.shader.Shader(geometry_src, 'geometry')
        new_frag_shader = graphics.shader.Shader(fragment_src, 'fragment')
        new_program = graphics.shader.ShaderProgram(new_vert_shader, new_geom_shader, new_frag_shader)
        pyglet.gl.current_context.pyglet_sprite_geo_shader = new_program
        return pyglet.gl.current_context.pyglet_sprite_geo_shader


class GeoSprite(Sprite):
    """Instance of an on-screen image.

    See the module documentation for usage.
    """

    _batch = None
    _animation = None
    _frame_index = 0
    _paused = False
    _rotation = 0
    _rgba = [255, 255, 255, 255]
    _scale = 1.0
    _scale_x = 1.0
    _scale_y = 1.0
    _visible = True

    def __init__(self,
                 img, x=0, y=0,
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

        if isinstance(img, image.Animation):
            self._animation = img
            self._texture = img.frames[0].image.get_texture()
            self._next_dt = img.frames[0].duration
            if self._next_dt:
                clock.schedule_once(self._animate, self._next_dt)
        else:
            self._texture = img.get_texture()

        program = get_geo_shader()

        self._batch = batch or graphics.get_default_batch()
        self._group = SpriteGroup(self._texture, blend_src, blend_dest, program, 0, group)
        self._subpixel = subpixel

        # TODO: add a property to the Texture class:
        tex_coords = (self._texture.tex_coords[0], self._texture.tex_coords[1],
                      self._texture.tex_coords[3], self._texture.tex_coords[7])

        self._vertex_list = self._batch.add(
            1, GL_POINTS, self._group,
            ('position2f', (int(x) if subpixel else x, int(y) if subpixel else y)),
            ('size4f', (self._texture.width, self._texture.height, 1, 1)),
            ('rotation1f', (self._rotation,)),
            ('color4Bn', self._rgba),
            ('tex_coords4f', tex_coords)
        )

    @property
    def position(self):
        """The (x, y) coordinates of the sprite, as a tuple.

        :Parameters:
            `x` : int
                X coordinate of the sprite.
            `y` : int
                Y coordinate of the sprite.
        """
        return self._x, self._y

    @position.setter
    def position(self, position):
        self._x, self._y = position
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
        self._vertex_list.position[:] = x, self._y

    @property
    def y(self):
        """Y coordinate of the sprite.

        :type: int
        """
        return self._y

    @y.setter
    def y(self, y):
        self._y = y
        self._vertex_list.position[:] = self._x, y

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
        self._vertex_list.rotation[0] = rotation

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
        self._vertex_list.size[2:4] = (scale * self._scale_x, scale * self._scale_y)

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
        self._vertex_list.size[2:4] = (self._scale * scale_x, self._scale * self._scale_y)

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
        self._vertex_list.size[2:4] = (self._scale * self._scale_x, self._scale * scale_y)

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
