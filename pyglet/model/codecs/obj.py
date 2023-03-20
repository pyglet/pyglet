import os

import pyglet

from pyglet.gl import GL_TRIANGLES
from pyglet.util import asstr

from .. import Model, Material, MaterialGroup, TexturedMaterialGroup
from . import ModelDecodeException, ModelDecoder


class Mesh:
    def __init__(self, name):
        self.name = name
        self.material = None

        self.indices = []
        self.vertices = []
        self.normals = []
        self.tex_coords = []
        self.colors = []


def load_material_library(filename):
    file = open(filename, 'r')

    name = None
    diffuse = [1.0, 1.0, 1.0]
    ambient = [1.0, 1.0, 1.0]
    specular = [1.0, 1.0, 1.0]
    emission = [0.0, 0.0, 0.0]
    shininess = 100.0
    opacity = 1.0
    texture_name = None

    matlib = {}

    for line in file:
        if line.startswith('#'):
            continue
        values = line.split()
        if not values:
            continue

        if values[0] == 'newmtl':
            if name is not None:
                # save previous material
                for item in (diffuse, ambient, specular, emission):
                    item.append(opacity)
                matlib[name] = Material(name, diffuse, ambient, specular, emission, shininess, texture_name)
            name = values[1]

        elif name is None:
            raise ModelDecodeException(f'Expected "newmtl" in {filename}')

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
                shininess = float(values[1])            # Blender exports 1~1000
                shininess = (shininess * 128) / 1000    # Normalize to 1~128 for OpenGL
            elif values[0] == 'd':
                opacity = float(values[1])
            elif values[0] == 'map_Kd':
                texture_name = values[1]

        except BaseException as ex:
            raise ModelDecodeException('Parsing error in {0}.'.format((filename, ex)))

    file.close()

    for item in (diffuse, ambient, specular, emission):
        item.append(opacity)

    matlib[name] = Material(name, diffuse, ambient, specular, emission, shininess, texture_name)

    return matlib


def parse_obj_file(filename, file=None):
    materials = {}
    mesh_list = []

    location = os.path.dirname(filename)

    try:
        if file is None:
            with open(filename, 'r') as f:
                file_contents = f.read()
        else:
            file_contents = asstr(file.read())
    except (UnicodeDecodeError, OSError):
        raise ModelDecodeException

    material = None
    mesh = None

    vertices = [[0., 0., 0.]]
    normals = [[0., 0., 0.]]
    tex_coords = [[0., 0.]]

    diffuse = [1.0, 1.0, 1.0, 1.0]
    ambient = [1.0, 1.0, 1.0, 1.0]
    specular = [1.0, 1.0, 1.0, 1.0]
    emission = [0.0, 0.0, 0.0, 1.0]
    shininess = 100.0

    default_material = Material("Default", diffuse, ambient, specular, emission, shininess)

    for line in file_contents.splitlines():

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
            material_abspath = os.path.join(location, values[1])
            materials = load_material_library(filename=material_abspath)            

        elif values[0] in ('usemtl', 'usemat'):
            material = materials.get(values[1])
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

            for i, v in enumerate(values[1:]):
                v_i, t_i, n_i = (list(map(int, [j or 0 for j in v.split('/')])) + [0, 0])[:3]
                if v_i < 0:
                    v_i += len(vertices) - 1
                if t_i < 0:
                    t_i += len(tex_coords) - 1
                if n_i < 0:
                    n_i += len(normals) - 1

                mesh.normals += normals[n_i]
                mesh.tex_coords += tex_coords[t_i]
                mesh.vertices += vertices[v_i]

                if i >= 3:
                    # Triangulate
                    mesh.normals += n1 + nlast
                    mesh.tex_coords += t1 + tlast
                    mesh.vertices += v1 + vlast

                if i == 0:
                    n1 = normals[n_i]
                    t1 = tex_coords[t_i]
                    v1 = vertices[v_i]
                nlast = normals[n_i]
                tlast = tex_coords[t_i]
                vlast = vertices[v_i]

    return mesh_list


###################################################
#   Decoder definitions start here:
###################################################

class OBJModelDecoder(ModelDecoder):
    def get_file_extensions(self):
        return ['.obj']

    def decode(self, filename, file, batch, group=None):

        if not batch:
            batch = pyglet.graphics.Batch()

        mesh_list = parse_obj_file(filename=filename, file=file)

        vertex_lists = []
        groups = []

        for mesh in mesh_list:
            material = mesh.material
            count = len(mesh.vertices) // 3
            if material.texture_name:
                program = pyglet.model.get_default_textured_shader()
                texture = pyglet.resource.texture(material.texture_name)
                matgroup = TexturedMaterialGroup(material, program, texture, parent=group)
                vertex_lists.append(program.vertex_list(count, GL_TRIANGLES, batch, matgroup,
                                                        position=('f', mesh.vertices),
                                                        normals=('f', mesh.normals),
                                                        tex_coords=('f', mesh.tex_coords),
                                                        colors=('f', material.diffuse * count)))
            else:
                program = pyglet.model.get_default_shader()
                matgroup = MaterialGroup(material, program, parent=group)
                vertex_lists.append(program.vertex_list(count, GL_TRIANGLES, batch, matgroup,
                                                        position=('f', mesh.vertices),
                                                        normals=('f', mesh.normals),
                                                        colors=('f', material.diffuse * count)))
            groups.append(matgroup)

        return Model(vertex_lists=vertex_lists, groups=groups, batch=batch)


def get_decoders():
    return [OBJModelDecoder()]


def get_encoders():
    return []
