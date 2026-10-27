import io

import pytest
import pyglet


@pytest.mark.parametrize('texture_vertices, expected', [
    ('vt 0.25\nvt 0.5\nvt 0.75\n', (0.25, 0, 0.5, 0, 0.75, 0)),
    ('vt 0.25 0.5\nvt 0.5 0.75\nvt 0.75 1\n', (0.25, 0.5, 0.5, 0.75, 0.75, 1)),
])
def test_textured_obj_uploads_a_pair_of_coordinates_per_vertex(tmp_path, monkeypatch, texture_vertices, expected):
    with (tmp_path / 'texture.png').open('wb') as texture_file:
        pyglet.image.SolidColorImagePattern().create_image(1, 1).save('texture.png', file=texture_file)
    (tmp_path / 'material.mtl').write_text('newmtl Surface\nmap_Kd texture.png\n')
    loader = pyglet.resource.Loader([str(tmp_path)])
    monkeypatch.setattr(pyglet.resource, 'texture', loader.texture)
    source = ('mtllib material.mtl\nusemtl Surface\n'
              'v 0 0 0\nv 1 0 0\nv 0 1 0\n' + texture_vertices +
              'f 1/1 2/2 3/3\n')
    scene = pyglet.model.load(str(tmp_path / 'triangle.obj'), file=io.StringIO(source))
    models = scene.create_models(pyglet.graphics.Batch())
    vertex_list = models[0].vertex_lists[0]
    try:
        assert vertex_list.count == 3
        assert tuple(vertex_list.TEXCOORD_0) == pytest.approx(expected)
    finally:
        vertex_list.delete()
