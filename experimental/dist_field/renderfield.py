#!/usr/bin/python
# $Id:$

import ctypes
import sys

import pyglet
from pyglet.window import key
from pyglet.gl import *

class Shader(object):
    '''Generic shader loader.'''
    def __init__(self, vertex_source, fragment_source=None):
        vertex_shader = self._create_shader(GL_VERTEX_SHADER, vertex_source)
        if fragment_source:
            fragment_shader = self._create_shader(GL_FRAGMENT_SHADER, 
                                                  fragment_source)
        
        program = glCreateProgram()
        glAttachShader(program, vertex_shader)
        if fragment_source:
            glAttachShader(program, fragment_shader)
        glLinkProgram(program)

        status = ctypes.c_int()
        glGetProgramiv(program, GL_LINK_STATUS, status)
        if not status.value:
            length = ctypes.c_int()
            glGetProgramiv(program, GL_INFO_LOG_LENGTH, length)
            log = ctypes.c_buffer(length.value)
            glGetProgramInfoLog(program, len(log), None, log)
            print >> sys.stderr, log.value
            raise RuntimeError('Program link error')

        self.program = program
        self._uniforms = {}

    def _create_shader(self, type, source):
        shader = glCreateShader(type)
        c_source = ctypes.create_string_buffer(source)
        c_source_ptr = ctypes.cast(ctypes.pointer(c_source), 
                                   ctypes.POINTER(c_char))
        glShaderSource(shader, 1, ctypes.byref(c_source_ptr), None)
        glCompileShader(shader)

        status = ctypes.c_int()
        glGetShaderiv(shader, GL_COMPILE_STATUS, status)
        if not status.value:
            length = ctypes.c_int()
            glGetShaderiv(shader, GL_INFO_LOG_LENGTH, length)
            log = ctypes.c_buffer(length.value)
            glGetShaderInfoLog(shader, len(log), None, log)
            print >> sys.stderr, log.value
            raise RuntimeError('Shader compile error')

        return shader

    def __getitem__(self, name):
        try:
            return self._uniforms[name]
        except KeyError:
            location = self._uniforms[name] = \
                glGetUniformLocation(self.program, name)
            return location

class DistFieldTextureGroup(pyglet.sprite.SpriteGroup):
    '''Override sprite's texture group to enable either the shader or alpha
    testing.'''
    def set_state(self):
        glEnable(self.texture.target)
        glBindTexture(self.texture.target, self.texture.id)

        glPushAttrib(GL_COLOR_BUFFER_BIT)
        if enable_shader:
            glUseProgram(shader.program)
            glUniform1i(shader['bidirectional'], enable_bidirectional)
            glUniform1i(shader['antialias'], enable_antialias)
            glUniform1i(shader['outline'], enable_outline)
            glUniform1f(shader['outline_width'], outline_width)
            glUniform1i(shader['glow'], enable_glow)
            glUniform1f(shader['glow_width'], glow_width)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        else:
            glEnable(GL_ALPHA_TEST)
            glAlphaFunc(GL_GEQUAL, 0.5)

    def unset_state(self):
        if enable_shader:
            glUseProgram(0)

        glPopAttrib(GL_COLOR_BUFFER_BIT)
        glDisable(self.texture.target)

class DistFieldSprite(pyglet.sprite.Sprite):
    '''Override sprite to use DistFieldTextureGroup.'''
    def __init__(self, 
                 img, x=0, y=0,
                 blend_src=GL_SRC_ALPHA,
                 blend_dest=GL_ONE_MINUS_SRC_ALPHA,
                 batch=None,
                 group=None,
                 usage='dynamic'):
        super(DistFieldSprite, self).__init__(
            img, x, y, blend_src, blend_dest, batch, group, usage)
        
        self._group = DistFieldTextureGroup(
            self._texture, blend_src, blend_dest, group)
        self._usage = usage
        self._create_vertex_list()

window = pyglet.window.Window(resizable=True)

@window.event
def on_resize(width, height):
    scale_width = width / float(image.width)
    scale_height = height / float(image.height)
    sprite.scale = min(scale_width, scale_height)
    sprite.x = width / 2
    sprite.y = height / 2

@window.event
def on_draw():
    window.clear()
    sprite.draw()

@window.event
def on_key_press(symbol, modifiers):
    global enable_shader
    global enable_bidirectional
    global enable_antialias
    global enable_outline
    global enable_glow
    global outline_width
    global glow_width
    if symbol == key.S:
        enable_shader = not enable_shader
    elif symbol == key.B:
        enable_bidirectional = not enable_bidirectional
    elif symbol == key.A:
        enable_antialias = not enable_antialias
    elif symbol == key.O:
        enable_outline = not enable_outline
        enable_glow = False
    elif symbol == key.G:
        enable_glow = not enable_glow
        enable_outline = False
    elif symbol == key.PERIOD:
        if enable_glow:
            glow_width += 0.005
        else:
            outline_width += 0.005
    elif symbol == key.COMMA:
        if enable_glow:
            glow_width -= 0.005
        else:
            outline_width -= 0.005

    print '-' * 78
    print 'enable_shader', enable_shader
    print 'enable_bidirectional', enable_bidirectional
    print 'enable_antialias', enable_antialias
    print 'enable_outline', enable_outline
    print 'enable_glow', enable_glow
    print 'outline_width', outline_width

image = pyglet.image.load(sys.argv[1])
image.anchor_x = image.width // 2
image.anchor_y = image.height // 2
sprite = DistFieldSprite(image)
    
shader = Shader('''
/* Vertex shader */
void main() 
{
    /* Pass through */
    gl_Position = ftransform();
    gl_FrontColor = gl_Color;
    gl_TexCoord[0] = gl_MultiTexCoord0;
}
''',
'''
/* Fragment shader */
uniform sampler2D tex;

uniform bool bidirectional;
uniform bool antialias;
uniform bool outline;
uniform bool glow;
uniform float outline_width;
uniform float glow_width;
const vec4 outline_color = vec4(0.0, 0.0, 1.0, 1.0);
const vec4 glow_color = vec4(1.0, 0.0, 0.0, 1.0);

void main()
{
    float alpha_mask;
    if (bidirectional)
    {
        vec4 field = texture2D(tex, gl_TexCoord[0].st);
        alpha_mask = float(field.r >= 0.5 && field.g >= 0.5);
    }
    else
    {
        alpha_mask = texture2D(tex, gl_TexCoord[0].st).a;
    }
    float alpha_width = fwidth(alpha_mask);
    float intensity = alpha_mask;

    gl_FragColor = gl_Color;

    if (glow)
    {
        float glow_min = 0.5 - glow_width;
        intensity = (alpha_mask - glow_min) / (0.5 - glow_min);
        float glow_intensity = 0.0;
        if (antialias)
            glow_intensity = 1.0 - smoothstep(0.5 - alpha_width,
                                              0.5 + alpha_width,
                                              alpha_mask) * 2.0;
        else
            glow_intensity = float(alpha_mask < 0.5);


        gl_FragColor = lerp(gl_FragColor, glow_color, glow_intensity);
    }
    else if (outline)
    {
        float outline_intensity = 0.0;
        float outline_min = 0.5 - outline_width;
        float outline_max = 0.5;
        if (antialias)
        {

            outline_intensity = 1.0 - smoothstep(outline_max - alpha_width,
                                                 outline_max + alpha_width,
                                                 alpha_mask) * 2.0;
                                        
            intensity *= smoothstep(outline_min - alpha_width, 
                                    outline_min + alpha_width, 
                                    alpha_mask) * 2.0;
        }
        else
        {
            outline_intensity = 
                float(alpha_mask >= outline_min && alpha_mask <= outline_max);
            intensity = float(alpha_mask >= outline_min);
        }
        gl_FragColor = lerp(gl_FragColor, outline_color, outline_intensity);
    }
    else if (antialias) 
    {
        intensity *= smoothstep(0.5 - alpha_width, 
                                0.5 + alpha_width, 
                                alpha_mask) * 2.0;
    }
    else
    {
        intensity = float(alpha_mask >= 0.5);
    }

    gl_FragColor.a = intensity;
}
''')
enable_shader = True
enable_bidirectional = False
enable_antialias = False
enable_outline = False
enable_glow = False
outline_width = 0.02
glow_width = 0.1

pyglet.app.run()
