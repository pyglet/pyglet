from __future__ import annotations

import os

import pyglet

from pyglet.gl import GL_TRIANGLES
from pyglet.util import asstr

from .. import Model, MaterialGroup, TexturedMaterialGroup
from . import ModelDecodeException, ModelDecoder
from .base import Material, Mesh, Primitive, Node, Scene


def _new_mesh(name, material):
    # The three primitive types used in .obj files:
    primitive = Primitive(attributes={'normals': [], 'tex_coords': [], 'vertices': []}, material=material)
    mesh = Mesh(primitives=[primitive], name=name)
    return mesh


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


def parse_obj_file(filename, file=None) -> list[Mesh]:
    materials = {}
    meshes = []

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

    normals = [[0., 0., 0.]]
    tex_coords = [[0., 0.]]
    vertices = [[0., 0., 0.]]

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
                mesh.primitives[0].material = material

        elif values[0] == 'o':
            mesh = _new_mesh(name=values[1], material=default_material)
            meshes.append(mesh)

        elif values[0] == 'f':
            if material is None:
                material = Material()
            if mesh is None:
                mesh = _new_mesh(name='unknown', material=material)
                meshes.append(mesh)

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

                mesh.primitives[0].attributes['normals'] += normals[n_i]
                mesh.primitives[0].attributes['tex_coords'] += tex_coords[t_i]
                mesh.primitives[0].attributes['vertices'] += vertices[v_i]

                if i >= 3:
                    mesh.primitives[0].attributes['normals'] += n1 + nlast
                    mesh.primitives[0].attributes['tex_coords'] += t1 + tlast
                    mesh.primitives[0].attributes['vertices'] += v1 + vlast

                if i == 0:
                    n1 = normals[n_i]
                    t1 = tex_coords[t_i]
                    v1 = vertices[v_i]
                nlast = normals[n_i]
                tlast = tex_coords[t_i]
                vlast = vertices[v_i]

    return meshes


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
            material = mesh.primitives[0].material
            count = len(mesh.primitives[0].attributes['vertices']) // 3
            if material.texture_name:
                program = pyglet.model.get_default_textured_shader()
                texture = pyglet.resource.texture(material.texture_name)
                matgroup = TexturedMaterialGroup(material, program, texture, parent=group)
                vertex_lists.append(program.vertex_list(count, GL_TRIANGLES, batch, matgroup,
                                                        position=('f', mesh.primitives[0].attributes['vertices']),
                                                        normals=('f', mesh.primitives[0].attributes['normals']),
                                                        tex_coords=('f', mesh.primitives[0].attributes['tex_coords']),
                                                        colors=('f', material.diffuse * count)))
            else:
                program = pyglet.model.get_default_shader()
                matgroup = MaterialGroup(material, program, parent=group)
                vertex_lists.append(program.vertex_list(count, GL_TRIANGLES, batch, matgroup,
                                                        position=('f', mesh.primitives[0].attributes['vertices']),
                                                        normals=('f', mesh.primitives[0].attributes['normals']),
                                                        colors=('f', material.diffuse * count)))
            groups.append(matgroup)

        return Model(vertex_lists=vertex_lists, groups=groups, batch=batch)


def get_decoders():
    return [OBJModelDecoder()]


def get_encoders():
    return []
