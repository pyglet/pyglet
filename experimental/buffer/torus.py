#!/usr/bin/env python


from math import pi, sin, cos

from pyglet.gl import *
from pyglet import clock
from pyglet import window

import buffer

vbo = True
interleaved = True
index_vbo = True
dl = False
usage = GL_STATIC_DRAW

try:
    # Try and create a window with multisampling (antialiasing)
    config = Config(sample_buffers=1, samples=4, 
                    depth_size=16, double_buffer=True,)
    w = window.Window(resizable=True, config=config, vsync=False)
except window.NoSuchConfigException:
    # Fall back to no multisampling for old hardware
    w = window.Window(resizable=True)

@w.event
def on_resize(width, height):
    # Override the default on_resize handler to create a 3D projection
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60., width / float(height), .1, 1000.)
    glMatrixMode(GL_MODELVIEW)

def setup():
    # One-time GL setup
    glClearColor(1, 1, 1, 1)
    glColor3f(1, 0, 0)
    glEnable(GL_DEPTH_TEST)

    # Uncomment this line for a wireframe view
    #glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

    # Simple light setup.  On Windows GL_LIGHT0 is enabled by default,
    # but this is not the case on Linux or Mac, so remember to always 
    # include it.
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_LIGHT1)

    # Define a simple function to create ctypes arrays of floats:
    def vec(*args):
        return (GLfloat * len(args))(*args)

    glLightfv(GL_LIGHT0, GL_POSITION, vec(.5, .5, 1, 0))
    glLightfv(GL_LIGHT0, GL_SPECULAR, vec(.5, .5, 1, 1))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, vec(1, 1, 1, 1))
    glLightfv(GL_LIGHT1, GL_POSITION, vec(1, 0, .5, 0))
    glLightfv(GL_LIGHT1, GL_DIFFUSE, vec(.5, .5, .5, 1))
    glLightfv(GL_LIGHT1, GL_SPECULAR, vec(1, 1, 1, 1))

    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, vec(0.5, 0, 0.3, 1))
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, vec(1, 1, 1, 1))
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 50)

class Torus(object):
    def __init__(self, radius, inner_radius, slices, inner_slices):
        # Create the vertex and normal arrays.
        vertices = []
        normals = []

        u_step = 2 * pi / (slices - 1)
        v_step = 2 * pi / (inner_slices - 1)
        u = 0.
        for i in range(slices):
            cos_u = cos(u)
            sin_u = sin(u)
            v = 0.
            for j in range(inner_slices):
                cos_v = cos(v)
                sin_v = sin(v)

                d = (radius + inner_radius * cos_v)
                x = d * cos_u
                y = d * sin_u
                z = inner_radius * sin_v

                nx = cos_u * cos_v
                ny = sin_u * cos_v
                nz = sin_v

                vertices.extend([x, y, z])
                normals.extend([nx, ny, nz])
                v += v_step
            u += u_step

        self.buffer = buffer.create(len(vertices) * 24,
            GL_ARRAY_BUFFER, usage, vbo=vbo)
        if interleaved:
            self.vertices, self.normals = buffer.interleaved('V3F', 'N3F')
        else:
            self.vertices, self.normals = buffer.serialized(
                len(vertices), 'V3F', 'N3F')

        self.buffer.bind()
        self.vertices.set(self.buffer, vertices)
        self.normals.set(self.buffer, normals)
        self.buffer.unbind()

        # Create a list of triangle indices.
        indices = []
        for i in range(slices - 1):
            for j in range(inner_slices - 1):
                p = i * inner_slices + j
                indices.extend([p, p + inner_slices, p + inner_slices + 1])
                indices.extend([p, p + 1, p + inner_slices + 1])
        #self.index_buffer = buffer.create_index(len(indices),
        #    GL_UNSIGNED_SHORT)
        #self.index_buffer.set_data(indices)

        self.index_buffer = buffer.create(len(indices) * 4, 
            GL_ELEMENT_ARRAY_BUFFER, usage, vbo=vbo)
        self.indices = buffer.ElementIndexAccessor(GL_UNSIGNED_INT)
        self.indices.set(self.index_buffer, indices)
        self.index_count = len(indices)
        print 'vbo = ', vbo
        print 'interleaved = ', interleaved
        print 'dl = ', dl
        print 'vertices', (len(vertices) // 3)
        print 'indices', self.index_count

        if dl:
            list = glGenLists(1)
            glNewList(list, GL_COMPILE)
            self.draw()
            glEndList()
            self.draw = lambda: glCallList(list)

    def draw(self):
        self.buffer.bind()
        self.vertices.enable()
        self.normals.enable()
        self.vertices.set_pointer(self.buffer.ptr)
        self.normals.set_pointer(self.buffer.ptr)
        self.index_buffer.bind()
        self.indices.draw(self.index_buffer, GL_TRIANGLES, 0, self.index_count)

setup()
torus = Torus(1, 0.3, 500, 500)
rx = ry = rz = 0
count = 0

while not w.has_exit:
    dt = clock.tick()
    rx += dt * 1
    ry += dt * 80
    rz += dt * 30
    rx %= 360
    ry %= 360
    rz %= 360

    w.dispatch_events()

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glTranslatef(0, 0, -4)
    glRotatef(rz, 0, 0, 1)
    glRotatef(ry, 0, 1, 0)
    glRotatef(rx, 1, 0, 0)
    torus.draw()

    w.flip()

    if count > 1.:
        count = 0
        print clock.get_fps()
    count += dt

