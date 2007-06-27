import math
import random

from pyglet.gl import *
import euclid

M_2PI = math.pi * 2.0

class DisplayList(int):
    def draw(self):
        glCallList(self)

def _TRI((v1, n1, t1, b1), (v2, n2, t2, b2), (v3, n3, t3, b3)):
    glNormal3f(n1[0], n1[1], n1[2]); glVertex3f(v1[0], v1[1], v1[2])
    glNormal3f(n2[0], n2[1], n2[2]); glVertex3f(v2[0], v2[1], v2[2])
    glNormal3f(n3[0], n3[1], n3[2]); glVertex3f(v3[0], v3[1], v3[2])

def render_torus(NR = 40, NS = 40, rad1 = 5.0, rad2 = 1.5):
    def P(R, S):
        R = R * M_2PI / NR
        S = S * M_2PI / NS
        y = rad2 * math.sin(S)
        r = rad1 + rad2 * math.cos(S)
        x = r * math.cos(R)
        z = r * math.sin(R)

        nx = math.cos(R) * math.cos(S)
        nz = math.sin(R) * math.cos(S)
        ny = math.sin(S)

        tx = math.cos(R) * -math.sin(S)
        tz = math.sin(R) * -math.sin(S)
        ty = math.cos(S)

        bx = ny * tz - nz * ty
        by = nz * tx - nx * tz
        bz = nx * ty - ny * tx

        return (x, y, z), (nx, ny, nz), (tx, tz, ty), (bx, by, bz)

    glBegin(GL_TRIANGLES)
    for ring in range(NR):
        for stripe in range(NR):
            _TRI(P(ring, stripe), P(ring, stripe + 1),
                P(ring + 1, stripe + 1))
            _TRI(P(ring, stripe), P(ring + 1, stripe + 1),
                P(ring + 1, stripe))
    glEnd()

def torus_list():
    torus_dl = glGenLists(1)
    glNewList(torus_dl, GL_COMPILE)
    render_torus()
    glEndList()
    return DisplayList(torus_dl)

def render_cube():
    glBegin(GL_TRIANGLES)
    glNormal3f(+1.0, 0.0, 0.0)
    glVertex3f(+1.0, +1.0, +1.0); glVertex3f(+1.0, -1.0, +1.0); glVertex3f(+1.0, -1.0, -1.0)
    glVertex3f(+1.0, +1.0, +1.0); glVertex3f(+1.0, -1.0, -1.0); glVertex3f(+1.0, +1.0, -1.0); 

    glNormal3f(0.0, +1.0, 0.0)
    glVertex3f(+1.0, +1.0, +1.0); glVertex3f(-1.0, +1.0, +1.0); glVertex3f(-1.0, +1.0, -1.0)
    glVertex3f(+1.0, +1.0, +1.0); glVertex3f(-1.0, +1.0, -1.0); glVertex3f(+1.0, +1.0, -1.0); 

    glNormal3f(0.0, 0.0, +1.0)
    glVertex3f(+1.0, +1.0, +1.0); glVertex3f(-1.0, +1.0, +1.0); glVertex3f(-1.0, -1.0, +1.0)
    glVertex3f(+1.0, +1.0, +1.0); glVertex3f(-1.0, -1.0, +1.0); glVertex3f(+1.0, -1.0, +1.0); 

    glNormal3f(-1.0, 0.0, 0.0)
    glVertex3f(-1.0, -1.0, -1.0); glVertex3f(-1.0, -1.0, +1.0); glVertex3f(-1.0, +1.0, +1.0); 
    glVertex3f(-1.0, +1.0, -1.0); glVertex3f(-1.0, -1.0, -1.0); glVertex3f(-1.0, +1.0, +1.0);  

    glNormal3f(0.0, -1.0, 0.0)
    glVertex3f(-1.0, -1.0, -1.0); glVertex3f(-1.0, -1.0, +1.0); glVertex3f(+1.0, -1.0, +1.0);
    glVertex3f(+1.0, -1.0, -1.0); glVertex3f(-1.0, -1.0, -1.0); glVertex3f(+1.0, -1.0, +1.0);

    glNormal3f(0.0, 0.0, -1.0)
    glVertex3f(-1.0, -1.0, -1.0); glVertex3f(-1.0, +1.0, -1.0); glVertex3f(+1.0, +1.0, -1.0);
    glVertex3f(+1.0, -1.0, -1.0); glVertex3f(-1.0, -1.0, -1.0); glVertex3f(+1.0, +1.0, -1.0);
    glEnd()

def cube_list():
    cube_dl = glGenLists(1)
    glNewList(cube_dl, GL_COMPILE)
    render_cube()
    glEndList()
    return DisplayList(cube_dl)

def cube_array_list():
    cubes_dl = glGenLists(1)
    glNewList(cubes_dl, GL_COMPILE)
    glMatrixMode(GL_MODELVIEW)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glEnable(GL_COLOR_MATERIAL)
    glPushMatrix()
    for x in range(-10, +11, +2):
        for y in range(-10, +11, +2):
            for z in range(-10, +11, +2):
                glPushMatrix()
                glTranslatef(x * 2.0, y * 2.0, z * 2.0)
                glScalef(.8, .8, .8)
                glColor4f((x + 10.0) / 20.0, (y + 10.0) / 20.0,
                    (z + 10.0) / 20.0, 1.0)
                render_cube()
                glPopMatrix()
    glPopMatrix()
    glDisable(GL_COLOR_MATERIAL)
    glEndList()
    return DisplayList(cubes_dl)


_ROT_30_X = euclid.Matrix4.new_rotatex(math.pi / 12)
_ROT_N30_X = euclid.Matrix4.new_rotatex(-math.pi / 12)
_ROT_30_Z = euclid.Matrix4.new_rotatez(math.pi / 12)
_ROT_N30_Z = euclid.Matrix4.new_rotatez(-math.pi / 12)
def _tree_branch(n, l, r):
    glVertex3f(l.p1.x, l.p1.y, l.p1.z)
    glVertex3f(l.p2.x, l.p2.y, l.p2.z)
    if n == 0:
        return

    if r:
        if random.random() > .9: return
        mag = abs(l.v) * (.5 + .5 * random.random())
    else:
        mag = abs(l.v) * .75
    if n%2:
        v1 = _ROT_30_X * l.v
        v2 = _ROT_N30_X * l.v
    else:
        v1 = _ROT_30_Z * l.v
        v2 = _ROT_N30_Z * l.v
    _tree_branch(n-1, euclid.Line3(l.p2, v1, mag), r)
    _tree_branch(n-1, euclid.Line3(l.p2, v2, mag), r)

def render_tree(n=10, r=False):
    glLineWidth(2.)
    glColor4f(.5, .5, .5, .5)
    glBegin(GL_LINES)
    _tree_branch(n-1, euclid.Line3(euclid.Point3(0., 0., 0.),
        euclid.Vector3(0., 1., 0.), 1.), r)
    glEnd()

def tree_list(n=10, r=False):
    dl = glGenLists(1)
    glNewList(dl, GL_COMPILE)
    render_tree(n, r)
    glEndList()
    return DisplayList(dl)

