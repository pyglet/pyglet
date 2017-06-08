import os
import pyglet

from pyglet.gl import GL_TRIANGLES
from pyglet.model.codecs import ModelDecoder
from pyglet.model import ModelException, Model, MaterialGroup, TexturedMaterialGroup


class MaterialSet(object):
    def __init__(self, group):
        self.group = group

        # Interleaved array of floats in GL_T2F_N3F_V3F format
        self.vertices = []
        self.normals = []
        self.tex_coords = []
        self.array = None


class Mesh(object):
    def __init__(self, name):
        self.name = name
        self.materials = []


def load_material_library(path, filename):

    file = open(os.path.join(path, filename), 'r')

    material_name = None
    diffuse = [0.8, 0.8, 0.8]
    ambient = [1.0, 1.0, 1.0]
    specular = [0.0, 0.0, 0.0]
    emission = [0.0, 0.0, 0.0]
    shininess = 0.0
    opacity = 1.0
    texture = None

    materials = {}

    for line in file:
        if line.startswith('#'):
            continue
        values = line.split()
        if not values:
            continue

        if values[0] == 'newmtl':
            material_name = values[1]
        elif material_name is None:
            raise ModelException('Expected "newmtl" in %s' % filename)

        try:
            if values[0] == 'Kd':
                diffuse = list(map(float, values[1:]))
            elif values[0] == 'Ka':
                ambient = list(map(float, values[1:]))
            elif values[0] == 'Ks':
                specular = list(map(float, values[1:]))
            elif values[0] == 'Ke':
                emission = list(map(float, values[1:]))
            elif values[0] == 'Ns':
                shininess = float(values[1])
            elif values[0] == 'd':
                opacity = float(values[1])
            elif values[0] == 'map_Kd':
                try:
                    texture = pyglet.resource.image(values[1]).texture
                except BaseException as ex:
                    raise ModelException('Could not load texture %s: %s' % (values[1], ex))

            if texture:
                group = TexturedMaterialGroup(material_name, diffuse, ambient, specular,
                                              emission, shininess, opacity, texture)
            else:
                group = MaterialGroup(material_name, diffuse, ambient, specular,
                                      emission, shininess, opacity)

            materials[material_name] = group

        except BaseException as ex:
            raise ModelException('Parse error in {0}.'.format((filename, ex)))

    return materials


def parse_obj_file(filename, file=None):
    materials = {}
    mesh_list = []

    if file is None:
        file = open(filename, 'r')

    path = os.path.dirname(filename)

    mesh = None
    material_set = None
    group = None

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
            materials = load_material_library(path, values[1])
        elif values[0] in ('usemtl', 'usemat'):
            group = materials.get(values[1], None)
            if group is None:
                print('Unknown material: %s' % values[1])
            if mesh is not None:
                material_set = MaterialSet(group)
                mesh.materials.append(material_set)
        elif values[0] == 'o':
            mesh = Mesh(values[1])
            mesh_list.append(mesh)
            material_set = None
        elif values[0] == 'f':
            if mesh is None:
                mesh = Mesh('')
                mesh_list.append(mesh)
            if group is None:
                raise ModelException('Unable to create Material Group')
            if material_set is None:
                material_set = MaterialSet(group)
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

    return mesh_list


###################################################
#   Decoder definitions start here:
###################################################

class OBJModelDecoder(ModelDecoder):
    def get_file_extensions(self):
        return ['.obj']

    def decode(self, file, filename, batch):
        if not batch:
            batch = pyglet.graphics.Batch()
            own_batch = True
        else:
            own_batch = False

        mesh_list = parse_obj_file(filename)
        vertex_lists = []

        for mesh in mesh_list:
            for material in mesh.materials:
                vertex_lists.append(batch.add(len(material.vertices) // 3,
                                              GL_TRIANGLES,
                                              material.group,
                                              ('v3f/static', material.vertices),
                                              ('n3f/static', material.normals),
                                              ('t2f/static', material.tex_coords)))

        return Model(vertex_lists, batch, own_batch=own_batch)


def get_decoders():
    return [OBJModelDecoder()]


def get_encoders():
    return []
