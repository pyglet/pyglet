from io import StringIO

import pytest

from pyglet.model.codecs.obj import parse_obj_file


VERTICES = 'v 1 2 3\nv 4 5 6\nv 7 8 9\n'
NORMALS = 'vn 1 0 0\nvn 0 1 0\nvn 0 0 1\n'
TEX_COORDS = 'vt 0.1 0.2\nvt 0.3 0.4\nvt 0.5 0.6\n'
POSITIONS = [1, 2, 3, 4, 5, 6, 7, 8, 9]


def parse_primitive(contents):
    meshes = parse_obj_file('relative.obj', StringIO(contents))
    assert len(meshes) == 1
    return meshes[0].primitives[0]


@pytest.mark.parametrize('relative', [False, True])
@pytest.mark.parametrize('syntax', ['v', 'v/vt', 'v//vn', 'v/vt/vn'])
def test_obj_face_indices(syntax, relative):
    indices = [-3, -2, -1] if relative else [1, 2, 3]
    tokens = []
    for index in indices:
        tokens.append({
            'v': f'{index}',
            'v/vt': f'{index}/{index}',
            'v//vn': f'{index}//{index}',
            'v/vt/vn': f'{index}/{index}/{index}',
        }[syntax])
    primitive = parse_primitive(
        VERTICES + NORMALS + TEX_COORDS + 'f ' + ' '.join(tokens))

    assert primitive.attributes[0].array == POSITIONS
    assert primitive.attributes[1].array == (
        [1, 0, 0, 0, 1, 0, 0, 0, 1] if 'vn' in syntax else [0] * 9)
    assert primitive.attributes[2].array == (
        [0.1, 0.2, 0.3, 0.4, 0.5, 0.6] if 'vt' in syntax else [0] * 6)


@pytest.mark.parametrize('relative_fields', [
    (True, False, False), (False, True, False), (False, False, True),
    (True, True, False), (True, False, True), (False, True, True),
])
def test_obj_can_mix_absolute_and_relative_fields(relative_fields):
    references = [(-3, -2, -1) if relative else (1, 2, 3)
                  for relative in relative_fields]
    tokens = ['/'.join(map(str, triplet)) for triplet in zip(*references)]
    primitive = parse_primitive(
        VERTICES + NORMALS + TEX_COORDS + 'f ' + ' '.join(tokens))

    assert primitive.attributes[0].array == POSITIONS
    assert primitive.attributes[1].array == [1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert primitive.attributes[2].array == [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]


@pytest.mark.parametrize('face', ['f 1 2 3 4', 'f -4 -3 -2 -1'])
def test_obj_quad_indices(face):
    primitive = parse_primitive(VERTICES + 'v 10 11 12\n' + face)

    assert primitive.attributes[0].count == 6
    assert primitive.attributes[0].array == [
        1, 2, 3, 4, 5, 6, 7, 8, 9,
        10, 11, 12, 1, 2, 3, 7, 8, 9,
    ]


@pytest.mark.parametrize('relative', [False, True])
def test_obj_relative_indices_use_current_vertex_list(relative):
    first = 'f -3 -2 -1\n' if relative else 'f 1 2 3\n'
    second = 'f -3 -2 -1\n' if relative else 'f 4 5 6\n'
    primitive = parse_primitive(
        VERTICES + first + 'v 10 11 12\nv 13 14 15\nv 16 17 18\n' + second)

    assert primitive.attributes[0].array == list(range(1, 19))
