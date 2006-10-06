import math

from pyglet.GL.VERSION_2_0 import *

M_2PI = math.pi * 2.0

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
    return torus_dl

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
    return cube_dl

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
    glEnd()
    glPopMatrix()
    glDisable(GL_COLOR_MATERIAL)
    glEndList()
    return cubes_dl

