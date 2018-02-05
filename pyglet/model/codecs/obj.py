import os
import pyglet

from pyglet.model.codecs import ModelDecoder
from pyglet.model import ModelException, Model


class Material(object):
    __slots__ = ("name", "diffuse", "ambient", "specular",
                 "emission", "shininess", "opacity", "texture_name")

    def __init__(self, name, diffuse, ambient, specular,
                 emission, shininess, opacity, texture_name=None):
        self.name = name
        self.diffuse = diffuse
        self.ambient = ambient
        self.specular = specular
        self.emission = emission
        self.shininess = shininess
        self.opacity = opacity
        self.texture_name = texture_name


class Mesh(object):
    def __init__(self, name):
        self.name = name
        self.material = None
        # Interleaved array of floats in GL_T2F_N3F_V3F format
        self.vertices = []
        self.normals = []
        self.tex_coords = []


def load_material_library(path, filename):

    file = open(os.path.join(path, filename), 'r')

    name = None
    diffuse = [0.8, 0.8, 0.8]
    ambient = [1.0, 1.0, 1.0]
    specular = [0.0, 0.0, 0.0]
    emission = [0.0, 0.0, 0.0]
    shininess = 100.0
    opacity = 1.0
    texture_name = None

    for line in file:
        if line.startswith('#'):
            continue
        values = line.split()
        if not values:
            continue

        if values[0] == 'newmtl':
            name = values[1]
        elif name is None:
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
                texture_name = values[1]

        except BaseException as ex:
            raise ModelException('Parsing error in {0}.'.format((filename, ex)))

    file.close()

    return Material(name, diffuse, ambient, specular, emission, shininess, opacity, texture_name)


def parse_obj_file(filename, file=None):
    materials = {}
    mesh_list = []

    if file is None:
        file = open(filename, 'r')

    path = os.path.dirname(filename)

    material = None
    mesh = None

    vertices = [[0., 0., 0.]]
    normals = [[0., 0., 0.]]
    tex_coords = [[0., 0.]]

    diffuse = [1.0, 1.0, 1.0]
    ambient = [1.0, 1.0, 1.0]
    specular = [1.0, 1.0, 1.0]
    emission = [0.0, 0.0, 0.0]
    shininess = 100.0
    opacity = 1.0

    default_material = Material("Default", diffuse, ambient, specular, emission, shininess, opacity)

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
            material = load_material_library(path, values[1])
            materials[material.name] = material

        elif values[0] in ('usemtl', 'usemat'):
            # TODO: fail on missing material instead of using default?
            material = materials.get(values[1], default_material)
            if mesh is not None:
                mesh.material = material

        elif values[0] == 'o':
            mesh = Mesh(name=values[1])
            mesh_list.append(mesh)

        elif values[0] == 'f':
            if mesh is None:
                mesh = Mesh(name='')
                mesh_list.append(mesh)
            if material is None:
                material = default_material
            if mesh.material is None:
                mesh.material = material

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
                # vertex = tex_coords[t_index] + normals[n_index] + vertices[v_index]

                mesh.normals += normals[n_index]
                mesh.tex_coords += tex_coords[t_index]
                mesh.vertices += vertices[v_index]

                if i >= 3:
                    # Triangulate
                    mesh.normals += n1 + nlast
                    mesh.tex_coords += t1 + tlast
                    mesh.vertices += v1 + vlast

                if i == 0:
                    n1 = normals[n_index]
                    t1 = tex_coords[t_index]
                    v1 = vertices[v_index]
                nlast = normals[n_index]
                tlast = tex_coords[t_index]
                vlast = vertices[v_index]

    file.close()

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

        mesh_list = parse_obj_file(filename=filename)

        return Model(mesh_list=mesh_list, batch=batch)


def get_decoders():
    return [OBJModelDecoder()]


def get_encoders():
    return []
