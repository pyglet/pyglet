from __future__ import annotations

from io import StringIO

import pytest

import pyglet


@pytest.mark.parametrize('textured', [False, True])
def test_load_and_create_multimaterial_model(tmp_path, monkeypatch, textured):
    material_path = tmp_path / 'colors.mtl'
    material_path.write_text(
        'newmtl red\nKd 1 0 0\nKa 0 0 0\nKs 0 0 0\nKe 0 0 0\n'
        'newmtl blue\nKd 0 0 1\nKa 0 0 0\nKs 0 0 0\nKe 0 0 0\n'
        + ('map_Kd blue.png\n' if textured else '')
    )
    source = (
        'mtllib colors.mtl\no colors\n'
        'v 2 2 -10\nv 12 2 -10\nv 2 12 -10\n'
        'v 18 2 -10\nv 28 2 -10\nv 18 12 -10\n'
        'vn 0 0 1\nvt 0 0\n'
        'usemtl red\nf 1/1/1 2/1/1 3/1/1\n'
        'usemtl blue\nf 4/1/1 5/1/1 6/1/1\n'
    )
    window = pyglet.window.Window(width=32, height=32, visible=False)
    model = None
    texture = None
    try:
        if textured:
            texture = pyglet.image.SolidColorImagePattern((255, 255, 255, 255)).create_image(1, 1).get_texture()
            monkeypatch.setattr(pyglet.resource, 'texture', lambda name: texture)
        scene = pyglet.model.load(str(tmp_path / 'scene.obj'), file=StringIO(source))
        batch = pyglet.graphics.Batch()
        model, = scene.create_models(batch)
        assert len(model.vertex_lists) == 2
        assert [v.count for v in model.vertex_lists] == [3, 3]
        assert [list(v.COLOR_0) for v in model.vertex_lists] == [
            [1, 0, 0, 1] * 3, [0, 0, 1, 1] * 3,
        ]
        assert [g.material.name for g in model.groups] == ['red', 'blue']
        window.clear()
        batch.draw()
        image = pyglet.image.get_buffer_manager().get_color_buffer().get_image_data()
        pixels = image.get_bytes('RGB', image.width * 3)
        colors = list(zip(pixels[0::3], pixels[1::3], pixels[2::3]))
        assert any(red > 0 and green == blue == 0 for red, green, blue in colors)
        assert any(blue > 0 and red == green == 0 for red, green, blue in colors)
    finally:
        if model is not None:
            for vertex_list in model.vertex_lists:
                vertex_list.delete()
        if texture is not None:
            texture.delete()
        window.close()
