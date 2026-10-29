from __future__ import annotations

from io import StringIO

import pytest

import pyglet
from pyglet.model.codecs import obj
from pyglet.model.codecs.base import Attribute, Mesh, Node, Primitive, SimpleMaterial


@pytest.fixture
def material_library(tmp_path):
    path = tmp_path / 'colors.mtl'
    path.write_text(
        'newmtl red\nKd 1 0 0\nKa 0 0 0\nKs 0 0 0\nKe 0 0 0\n'
        'newmtl blue\nKd 0 0 1\nKa 0 0 0\nKs 0 0 0\nKe 0 0 0\n'
    )
    return path


def load_scene(tmp_path, material_library, lines):
    source = 'mtllib colors.mtl\n'
    for x in range(9):
        source += f'v {x} {x % 3} -10\n'
    source += 'vn 0 0 1\nvt 0 0\n' + '\n'.join(lines)
    return pyglet.model.load(str(tmp_path / 'scene.obj'), file=StringIO(source))


@pytest.mark.parametrize('object_line', ['', 'o colors'])
@pytest.mark.parametrize('command', ['usemtl', 'usemat'])
def test_material_changes_preserve_existing_faces(tmp_path, material_library, object_line, command):
    scene = load_scene(tmp_path, material_library, [
        object_line,
        f'{command} red', 'f 1/1/1 2/1/1 3/1/1',
        f'{command} blue', 'f 4/1/1 5/1/1 6/1/1',
        f'{command} red', 'f 7/1/1 8/1/1 9/1/1',
    ])
    meshes = scene.nodes[0].meshes
    assert len(meshes) == 1
    assert meshes[0].name == ('colors' if object_line else 'unknown')
    primitives = meshes[0].primitives
    assert [p.material.name for p in primitives] == ['red', 'blue', 'red']
    assert [p.attributes[0].count for p in primitives] == [3, 3, 3]
    assert [p.attributes[0].array[0] for p in primitives] == [0, 3, 6]
    assert primitives[0].material is primitives[2].material


def test_material_selected_before_object_is_retained(tmp_path, material_library):
    scene = load_scene(tmp_path, material_library, [
        'usemtl red', 'o first', 'f 1/1/1 2/1/1 3/1/1',
        'o second', 'f 4/1/1 5/1/1 6/1/1',
    ])
    meshes = scene.nodes[0].meshes
    assert [m.name for m in meshes] == ['first', 'second']
    assert [m.primitives[0].material.name for m in meshes] == ['red', 'red']


def test_material_change_after_last_face_does_not_recolor_it(tmp_path, material_library):
    scene = load_scene(tmp_path, material_library, [
        'usemtl red', 'f 1/1/1 2/1/1 3/1/1', 'usemtl blue',
    ])
    primitives = scene.nodes[0].meshes[0].primitives
    assert len(primitives) == 1
    assert primitives[0].material.name == 'red'


def test_repeated_and_unused_material_selections_do_not_add_primitives(tmp_path, material_library):
    scene = load_scene(tmp_path, material_library, [
        'o colors', 'usemtl blue', 'usemtl red',
        'f 1/1/1 2/1/1 3/1/1', 'usemtl red', 'f 4/1/1 5/1/1 6/1/1',
    ])
    primitives = scene.nodes[0].meshes[0].primitives
    assert len(primitives) == 1
    assert primitives[0].material.name == 'red'
    assert primitives[0].attributes[0].count == 6


@pytest.mark.parametrize('object_line,name,color', [
    ('o colors', 'Default', [1, 1, 1, 1]),
    ('', 'default', [0.8, 0.8, 0.8, 1]),
])
def test_default_faces_keep_their_material(tmp_path, material_library, object_line, name, color):
    scene = load_scene(tmp_path, material_library, [
        object_line, 'f 1/1/1 2/1/1 3/1/1', 'usemtl red', 'f 4/1/1 5/1/1 6/1/1',
    ])
    primitives = scene.nodes[0].meshes[0].primitives
    assert [p.material.name for p in primitives] == [name, 'red']
    assert list(primitives[0].material.diffuse) == color


def test_polygon_triangulation_stays_with_its_material(tmp_path, material_library):
    scene = load_scene(tmp_path, material_library, [
        'usemtl red', 'f 1/1/1 2/1/1 3/1/1 4/1/1',
        'usemtl blue', 'f 5/1/1 6/1/1 7/1/1',
    ])
    primitives = scene.nodes[0].meshes[0].primitives
    assert [p.material.name for p in primitives] == ['red', 'blue']
    assert [p.attributes[0].count for p in primitives] == [6, 3]
    assert primitives[0].attributes[0].array == [
        0, 0, -10, 1, 1, -10, 2, 2, -10, 3, 0, -10, 0, 0, -10, 2, 2, -10,
    ]


@pytest.mark.parametrize('textured', [False, True])
def test_create_models_uses_every_primitive(monkeypatch, textured):
    materials = [SimpleMaterial(name='red', diffuse=(1, 0, 0, 1)),
                 SimpleMaterial(name='blue', diffuse=(0, 0, 1, 1),
                                texture_name='blue.png' if textured else None)]
    primitives = [Primitive(
        attributes=[Attribute('POSITION', 'f', 'VEC3', 3, [i, 0, -10] * 3)],
        indices=None, mode=obj.GL_TRIANGLES, material=material,
    ) for i, material in enumerate(materials)]
    scene = obj.OBJScene(nodes=[Node(meshes=[Mesh(name='colors', primitives=primitives)])])
    calls = []

    class Program:
        def vertex_list(self, count, mode, batch, group, **data):
            calls.append((count, mode, batch, group, data))
            return object()

    program = Program()
    monkeypatch.setattr(pyglet.model, 'get_default_shader', lambda: program)
    monkeypatch.setattr(pyglet.model, 'get_default_textured_shader', lambda: program)
    texture = object()
    monkeypatch.setattr(pyglet.resource, 'texture', lambda name: texture)
    batch = pyglet.graphics.Batch()
    parent = pyglet.graphics.Group()
    model, = scene.create_models(batch, parent)
    assert len(model.vertex_lists) == 2
    assert [c[3].material for c in calls] == materials
    assert all(c[0] == 3 and c[2] is batch and c[3].parent is parent for c in calls)
    assert [c[4]['COLOR_0'][1] for c in calls] == [m.diffuse * 3 for m in materials]
    assert [c[4]['POSITION'][1] for c in calls] == [[0, 0, -10] * 3, [1, 0, -10] * 3]
    if textured:
        assert calls[1][3].texture is texture
