import os
import ctypes
from pyglet.GL.future import *

THREEFV = ctypes.c_float * 3

def MTL(filename):
    contents = {}
    mtl = None
    for line in open(filename, "r"):
        if line.startswith('#'): continue
        values = line.split()
        if not values: continue
        if values[0] == 'newmtl':
            mtl = contents[values[1]] = {}
        elif mtl is None:
            raise ValueError, "mtl file doesn't start with newmtl stmt"
        elif values[0] == 'map_Kd':
            # load the texture referred to by this declaration
            mtl[values[0]] = values[1]
            surf = pygame.image.load(mtl['map_Kd'])
            image = pygame.image.tostring(surf, 'RGBA', 1)
            ix, iy = surf.get_rect().size
            texid = mtl['texture_Kd'] = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texid)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
                GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER,
                GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ix, iy, 0, GL_RGBA,
                GL_UNSIGNED_BYTE, image)
        else:
            mtl[values[0]] = map(float, values[1:])
    return contents

class OBJ:
    def __init__(self, filename, swapyz=False):
        """Loads a Wavefront OBJ file. """
        self.filename = filename
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []
        self.mtl = None

        material = None
        path = os.path.split(filename)[0]
        use_texture = False
        for line in open(filename, "r"):
            if line.startswith('#'): continue
            values = line.split()
            if not values: continue
            if values[0] == 'v':
                v = map(float, values[1:4])
                if swapyz:
                    v = v[0], v[2], v[1]
                self.vertices.append(v)
            elif values[0] == 'vn':
                v = map(float, values[1:4])
                if swapyz:
                    v = v[0], v[2], v[1]
                self.normals.append(v)
            elif values[0] == 'vt':
                self.texcoords.append(map(float, values[1:3]))
            elif values[0] in ('usemtl', 'usemat'):
                material = values[1]
            elif values[0] == 'mtllib':
                self.mtl = MTL(os.path.join(path, values[1]))
                for name in self.mtl:
                    if 'texture_Kd' in self.mtl[name]:
                        use_texture = True
            elif values[0] == 'f':
                face = []
                texcoords = []
                norms = []
                for v in values[1:]:
                    w = v.split('/')
                    vert = int(w[0])
                    if vert < 0:
                        # refers to -ve indexed verts defined up to this
                        # point
                        vert += len(self.vertices)
                    face.append(vert)
                    if len(w) >= 2 and len(w[1]) > 0:
                        texcoords.append(int(w[1]))
                    else:
                        texcoords.append(0)
                    if len(w) >= 3 and len(w[2]) > 0:
                        norms.append(int(w[2]))
                    else:
                        norms.append(0)
                self.faces.append((face, norms, texcoords, material))
            else:
                #print 'UNHANDLED', values
                continue

        self.gl_list = glGenLists(1)
        glNewList(self.gl_list, GL_COMPILE)
        if use_texture: glEnable(GL_TEXTURE_2D)

        for face in self.faces:
            vertices, normals, texture_coords, material = face

            if material:
                mtl = self.mtl[material]
                if 'texture_Kd' in mtl:
                    # use diffuse texmap
                    glBindTexture(GL_TEXTURE_2D, mtl['texture_Kd'])
                else:
                    # just use diffuse colour
                    glColor3f(*mtl['Kd'])
            else:
                glColor4f(1., 1., 1., 1.)

            glBegin(GL_POLYGON)
            for i in range(0, len(vertices)):
                if normals[i]:
                    glNormal3f(*self.normals[normals[i] - 1])
                if texture_coords[i]:
                    glTexCoord2f(*self.texcoords[texture_coords[i] - 1])
                glVertex3f(*self.vertices[vertices[i] - 1])
            glEnd()
        if use_texture: glDisable(GL_TEXTURE_2D)
        glEndList()

    def __repr__(self):
        return '<OBJ %r>'%self.filename

    def draw(self):
        glPushAttrib(GL_ENABLE_BIT)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        glCallList(self.gl_list)
        glPopAttrib()

