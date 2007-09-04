#!/usr/bin/env python
import sys

from pyglet.gl import *
from pyglet import window, image

import shader

w = window.Window(512, 512)
kitten = image.load('../examples/programming_guide/kitten.jpg')

pinch_f = '''
uniform sampler2D tex;
uniform vec2 size;
uniform vec2 mouse;
uniform float strength;

void main() {
    vec2 h = vec2(1.0/size.x, 0.0);
    vec2 pos = gl_TexCoord[0].st;

    vec2 v = pos - mouse;
    float d = length(v);
    v = normalize(v);
    v = v * clamp(exp(2. * d) / strength, 0., 1.);

    gl_FragColor = texture2D(tex, pos + v);
}
'''


pinch = shader.ShaderProgram()
pinch.setShader(shader.FragmentShader('pinch_f', pinch_f))
pinch.install()
pinch.uset2F('size', float(kitten.width), float(kitten.height))

@w.event
def on_mouse_motion(x, y, *args):
    pinch.uset2F('mouse', float(x)/kitten.width, float(y)/kitten.height)
    return True

strength = 50.
pinch.uset1F('strength', strength)
@w.event
def on_mouse_scroll(x, y, dx, dy):
    global strength
    strength = max(1, strength + dy)
    pinch.uset1F('strength', float(strength))
    return True

while not w.has_exit:
    w.dispatch_events()
    glClear(GL_COLOR_BUFFER_BIT)
    kitten.blit(0, 0)
    w.flip()

