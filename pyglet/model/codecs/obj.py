import os
from pyglet import graphics
from pyglet.gl import *

from pyglet.model.codecs import ModelDecoder
from pyglet.model import ModelData


class OBJModelDecoder(ModelDecoder):

    def get_file_extensions(self):
        return ['.obj']

    def decode(self, file, filename):
        pass
        # return ModelData()


def get_decoders():
    return [OBJModelDecoder()]


######################################################


class ModelMaterialGroup(pyglet.graphics.Group):
    diffuse = [.8, .8, .8]
    ambient = [.2, .2, .2]
    specular = [0., 0., 0.]
    emission = [0., 0., 0.]
    shininess = 0.
    opacity = 1.
    texture = None

    def __init__(self, name, **kwargs):
        self.name = name
        super(ModelMaterialGroup, self).__init__(**kwargs)

    def set_state(self, face=GL_FRONT_AND_BACK):
        if self.texture:
            glEnable(self.texture.target)
            glBindTexture(self.texture.target, self.texture.id)
        else:
            glDisable(GL_TEXTURE_2D)

        glMaterialfv(face, GL_DIFFUSE, (GLfloat * 4)(*(self.diffuse + [self.opacity])))
        glMaterialfv(face, GL_AMBIENT, (GLfloat * 4)(*(self.ambient + [self.opacity])))
        glMaterialfv(face, GL_SPECULAR, (GLfloat * 4)(*(self.specular + [self.opacity])))
        glMaterialfv(face, GL_EMISSION, (GLfloat * 4)(*(self.emission + [self.opacity])))
        glMaterialf(face, GL_SHININESS, self.shininess)

    def unset_state(self):
        if self.texture:
            glDisable(self.texture.target)
        glDisable(GL_COLOR_MATERIAL)

    def __eq__(self, other):
        if self.texture is None:
            return super(ModelMaterialGroup, self).__eq__(other)
        return (self.__class__ is other.__class__ and
                self.texture.id == other.texture.id and
                self.texture.target == other.texture.target and
                self.parent == other.parent)

    def __hash__(self):
        if self.texture is None:
            return super(ModelMaterialGroup, self).__hash__()
        return hash((self.texture.id, self.texture.target))


class MaterialSet(object):
    def __init__(self, material):
        self.material = material

        # Interleaved array of floats in GL_T2F_N3F_V3F format
        self.vertices = []
        self.normals = []
        self.tex_coords = []
        self.array = None


class Mesh(object):
    def __init__(self, name):
        self.name = name
        self.materials = []


class Obj(object):

    def __init__(self, filename, file=None, path=None):
        self.materials = {}
        self.meshes = {}        # Name mapping
        self.mesh_list = []     # Also includes anonymous meshes

        if file is None:
            file = open(filename, 'r')

        if path is None:
            path = os.path.dirname(filename)
        self.path = path

        mesh = None
        material_set = None
        material = None

        vertices = [[0., 0., 0.]]
        normals = [[0., 0., 0.]]
        tex_coords = [[0., 0.]]

        for line in file:
            if line.startswith('#'):
                continue
            values = line.split()
            if not values:
                continue

            if values[0] == 'v':
                vertices.append(list(map(float, values[1:4])))
            elif values[0] == 'vn':
                normals.append(list(map(float, values[1:4])))
            elif values[0] == 'vt':
                tex_coords.append(list(map(float, values[1:3])))
            elif values[0] == 'mtllib':
                self.load_material_library(values[1])
            elif values[0] in ('usemtl', 'usemat'):
                material = self.materials.get(values[1], None)
                if material is None:
                    print('Unknown material: %s' % values[1])
                if mesh is not None:
                    material_set = MaterialSet(material)
                    mesh.materials.append(material_set)
            elif values[0] == 'o':
                mesh = Mesh(values[1])
                self.meshes[mesh.name] = mesh
                self.mesh_list.append(mesh)
                material_set = None
            elif values[0] == 'f':
                if mesh is None:
                    mesh = Mesh('')
                    self.mesh_list.append(mesh)
                if material is None:
                    # FIXME
                    material = ModelMaterialGroup("<unknown>")
                if material_set is None:
                    material_set = MaterialSet(material)
                    mesh.materials.append(material_set)

                # For fan triangulation, remember first and latest vertices
                n1 = None
                nlast = None
                t1 = None
                tlast = None
                v1 = None
                vlast = None
                # points = []
                for i, v in enumerate(values[1:]):
                    v_index, t_index, n_index = \
                        (list(map(int, [j or 0 for j in v.split('/')])) + [0, 0])[:3]
                    if v_index < 0:
                        v_index += len(vertices) - 1
                    if t_index < 0:
                        t_index += len(tex_coords) - 1
                    if n_index < 0:
                        n_index += len(normals) - 1
                    # vertex = tex_coords[t_index] + \
                    #         normals[n_index] + \
                    #         vertices[v_index]

                    material_set.normals += normals[n_index]
                    material_set.tex_coords += tex_coords[t_index]
                    material_set.vertices += vertices[v_index]

                    if i >= 3:
                        # Triangulate
                        material_set.normals += n1 + nlast
                        material_set.tex_coords += t1 + tlast
                        material_set.vertices += v1 + vlast

                    if i == 0:
                        n1 = normals[n_index]
                        t1 = tex_coords[t_index]
                        v1 = vertices[v_index]
                    nlast = normals[n_index]
                    tlast = tex_coords[t_index]
                    vlast = vertices[v_index]

    def open_material_file(self, filename):
        '''Override for loading from archive/network etc.'''
        return open(os.path.join(self.path, filename), 'r')

    def load_material_library(self, filename):
        material = None
        file = self.open_material_file(filename)

        for line in file:
            if line.startswith('#'):
                continue
            values = line.split()
            if not values:
                continue

            if values[0] == 'newmtl':
                material = ModelMaterialGroup(values[1])
                self.materials[material.name] = material
            elif material is None:
                print('Expected "newmtl" in %s' % filename)
                continue

            try:
                if values[0] == 'Kd':
                    material.diffuse = list(map(float, values[1:]))
                elif values[0] == 'Ka':
                    material.ambient = list(map(float, values[1:]))
                elif values[0] == 'Ks':
                    material.specular = list(map(float, values[1:]))
                elif values[0] == 'Ke':
                    material.emissive = list(map(float, values[1:]))
                elif values[0] == 'Ns':
                    material.shininess = float(values[1])
                elif values[0] == 'd':
                    material.opacity = float(values[1])
                elif values[0] == 'map_Kd':
                    try:
                        material.texture = pyglet.resource.image(values[1]).texture
                    except BaseException as ex:
                        print('Could not load texture %s: %s' % (values[1], ex))
            except BaseException as ex:
                print('Parse error in {0}.'.format((filename, ex)))

