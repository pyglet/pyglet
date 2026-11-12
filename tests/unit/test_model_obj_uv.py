import io

import pytest

from pyglet.model.codecs.obj import parse_obj_file


@pytest.mark.parametrize('face_size', [3, 4])
@pytest.mark.parametrize('texture_vertices, expected', [
    (['0.25', '0.5', '0.75', '1'],
     [(0.25, 0), (0.5, 0), (0.75, 0), (1, 0)]),
    (['0.25 0.5', '0.5 0.75', '0.75 1', '1 0.25'],
     [(0.25, 0.5), (0.5, 0.75), (0.75, 1), (1, 0.25)]),
    (['0.25 0.5 0.9', '0.5 0.75 0.8', '0.75 1 0.7', '1 0.25 0.6'],
     [(0.25, 0.5), (0.5, 0.75), (0.75, 1), (1, 0.25)]),
    (['0.25', '0.5 0.25', '0.75 0.5 0.9', '1'],
     [(0.25, 0), (0.5, 0.25), (0.75, 0.5), (1, 0)]),
    ([], [(0, 0)] * 4),
])
def test_texture_coordinates_have_two_components_per_vertex(face_size, texture_vertices, expected):
    source = 'v 0 0 0\nv 1 0 0\nv 1 1 0\nv 0 1 0\n'
    source += ''.join('vt ' + vertex + '\n' for vertex in texture_vertices)
    face = [f'{i}/{i}' if texture_vertices else str(i) for i in range(1, face_size + 1)]
    source += 'f ' + ' '.join(face) + '\n'
    primitive = parse_obj_file('coordinates.obj', io.StringIO(source))[0].primitives[0]
    position, normal, uv = primitive.attributes
    vertex_count = 3 if face_size == 3 else 6
    indices = [0, 1, 2] if face_size == 3 else [0, 1, 2, 3, 0, 2]

    assert uv.array == pytest.approx([component for i in indices for component in expected[i]])
    assert uv.type == 'VEC2'
    assert uv.count == vertex_count
    assert position.type == normal.type == 'VEC3'
    assert position.count == normal.count == vertex_count
    assert len(uv.array) == vertex_count * 2
