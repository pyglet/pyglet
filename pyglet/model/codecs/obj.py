from __future__ import annotations

import os

import pyglet

from pyglet.gl import GL_TRIANGLES
from pyglet.util import asstr

from . import ModelDecodeException, ModelDecoder
from .base import SimpleMaterial, Mesh, Primitive, Attribute, Node, Scene
from .. import Model, MaterialGroup, TexturedMaterialGroup
from ...graphics import Batch, Group


def _new_mesh(name, material):
    # The three primitive types used in .obj files:
    attributes = [Attribute('POSITION', 'f', 'VEC3', 0, []),
                  Attribute('NORMAL', 'f', 'VEC3', 0, []),
                  Attribute('TEXCOORD_0', 'f', 'VEC3', 0, [])]
    primitive = Primitive(attributes=attributes, indices=None, material=material, mode=GL_TRIANGLES)
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
                matlib[name] = SimpleMaterial(name, diffuse, ambient, specular, emission, shininess, texture_name)
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

    matlib[name] = SimpleMaterial(name, diffuse, ambient, specular, emission, shininess, texture_name)

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

    default_material = SimpleMaterial("Default", diffuse, ambient, specular, emission, shininess)

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
                material = SimpleMaterial()
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

                mesh.primitives[0].attributes[0].array += vertices[v_i]
                mesh.primitives[0].attributes[1].array += normals[n_i]
                mesh.primitives[0].attributes[2].array += tex_coords[t_i]

                if i >= 3:
                    mesh.primitives[0].attributes[0].array += v1 + vlast
                    mesh.primitives[0].attributes[1].array += n1 + nlast
                    mesh.primitives[0].attributes[2].array += t1 + tlast

                if i == 0:
                    n1 = normals[n_i]
                    t1 = tex_coords[t_i]
                    v1 = vertices[v_i]
                nlast = normals[n_i]
                tlast = tex_coords[t_i]
                vlast = vertices[v_i]

        for mesh in meshes:
            for primitive in mesh.primitives:
                for attribute in primitive.attributes:
                    attribute.count = len(attribute.array) // 3

    return meshes


class OBJScene(Scene):

    def create_models(self, batch: Batch, group: Group | None = None) -> list[Model]:
        vertex_lists = []
        groups = []
        for node in self.nodes:
            for mesh in node.meshes:
                material = mesh.primitives[0].material
                count = mesh.primitives[0].attributes[0].count

                if material.texture_name:
                    program = pyglet.model.get_default_textured_shader()
                    texture = pyglet.resource.texture(material.texture_name)
                    matgroup = TexturedMaterialGroup(material, program, texture, parent=group)
                else:
                    program = pyglet.model.get_default_shader()
                    matgroup = MaterialGroup(material, program, parent=group)

                data = {a.name: (a.fmt, a.array) for a in mesh.primitives[0].attributes}
                # Add additional material data:
                data['COLOR_0'] = 'f', material.diffuse * count

                vertex_lists.append(program.vertex_list(count, GL_TRIANGLES, batch, matgroup, **data))
                groups.append(matgroup)

        return [Model(vertex_lists=vertex_lists, groups=groups, batch=batch)]


###################################################
#   Decoder definitions start here:
###################################################

class OBJModelDecoder(ModelDecoder):
    def get_file_extensions(self):
        return ['.obj']

    def decode(self, filename, file):

        mesh_list = parse_obj_file(filename=filename, file=file)
        return OBJScene(nodes=[Node(meshes=mesh_list)])


def get_decoders():
    return [OBJModelDecoder()]


def get_encoders():
    return []
