from io import StringIO

import pytest

import pyglet
from pyglet.model.codecs.obj import load_material_library, ModelDecodeException


FIRST = '''newmtl first
Kd 1 0 0
Ka 0.1 0.2 0.3
Ks 0.4 0.5 0.6
Ke 0.7 0.8 0.9
Ns 250
d 0.3
map_Kd first.png
'''


def load_materials(tmp_path, text):
    path = tmp_path / 'materials.mtl'
    path.write_text(text)
    return load_material_library(str(path))


@pytest.mark.parametrize('attribute, first_rgb, second_rgb, default_rgb', [
    ('diffuse', [1, 0, 0], [0, 1, 0], [1, 1, 1]),
    ('ambient', [0.1, 0.2, 0.3], [1, 1, 1], [1, 1, 1]),
    ('specular', [0.4, 0.5, 0.6], [1, 1, 1], [1, 1, 1]),
    ('emission', [0.7, 0.8, 0.9], [0, 0, 0], [0, 0, 0]),
])
def test_material_colors_and_opacity_are_independent(
        tmp_path, attribute, first_rgb, second_rgb, default_rgb):
    materials = load_materials(
        tmp_path, FIRST + 'newmtl second\nKd 0 1 0\nnewmtl third\n')

    assert list(materials) == ['first', 'second', 'third']
    assert getattr(materials['first'], attribute) == first_rgb + [0.3]
    assert getattr(materials['second'], attribute) == second_rgb + [1]
    assert getattr(materials['third'], attribute) == default_rgb + [1]


@pytest.mark.parametrize('attribute, first_value, default_value', [
    ('texture_name', 'first.png', None),
    ('shininess', 32.0, 100.0),
])
def test_material_optional_properties_reset(
        tmp_path, attribute, first_value, default_value):
    materials = load_materials(tmp_path, FIRST + 'newmtl second\n')

    assert getattr(materials['first'], attribute) == first_value
    assert getattr(materials['second'], attribute) == default_value


@pytest.mark.parametrize('attribute', [
    'diffuse', 'ambient', 'specular', 'emission',
])
def test_explicit_material_properties_still_load(tmp_path, attribute):
    materials = load_materials(tmp_path, (
        'newmtl first\nKd 1 0 0\nKa 1 0 0\nKs 1 0 0\nKe 1 0 0\nd 0.25\n'
        'newmtl second\nKd 0 1 0\nKa 0 1 0\nKs 0 1 0\nKe 0 1 0\nd 0.75\n'
    ))

    assert getattr(materials['first'], attribute) == [1, 0, 0, 0.25]
    assert getattr(materials['second'], attribute) == [0, 1, 0, 0.75]


def test_obj_load_keeps_material_defaults_separate(tmp_path):
    load_materials(tmp_path, 'newmtl red\nKd 1 0 0\nd 0.5\nnewmtl default\n')
    obj = StringIO('''mtllib materials.mtl
v 1 2 3
v 4 5 6
v 7 8 9
o red_mesh
usemtl red
f 1 2 3
o default_mesh
usemtl default
f 1 2 3
''')

    scene = pyglet.model.load(str(tmp_path / 'model.obj'), file=obj)
    first, second = [mesh.primitives[0].material
                     for mesh in scene.nodes[0].meshes]

    assert first.diffuse == [1, 0, 0, 0.5]
    assert second.diffuse == [1, 1, 1, 1]


@pytest.mark.parametrize('contents', ['', '# No material definitions\n\n'])
def test_empty_material_library_has_no_materials(tmp_path, contents):
    assert load_materials(tmp_path, contents) == {}


def test_property_before_material_is_rejected(tmp_path):
    with pytest.raises(ModelDecodeException):
        load_materials(tmp_path, 'Kd 1 0 0\n')
