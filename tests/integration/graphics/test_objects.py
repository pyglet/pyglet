from __future__ import annotations

import pytest

import pyglet
from pyglet.graphics.shader import MissingAttributeException

from tests.annotations import GraphicsAPI


_SPRITE_LAYOUT_A = {
    "position": 0,
    "translate": 1,
    "colors": 2,
    "tex_coords": 3,
    "scale": 4,
    "rotation": 5,
    "extra_attr": 6,
}

_SPRITE_LAYOUT_B = {
    "position": 5,
    "translate": 4,
    "colors": 3,
    "tex_coords": 2,
    "scale": 1,
    "rotation": 0,
    "extra_attr": 6,
}

_SHAPE_LAYOUT_A = {
    "position": 0,
    "translation": 1,
    "colors": 2,
    "rotation": 3,
    "extra_attr": 4,
}

_SHAPE_LAYOUT_B = {
    "position": 3,
    "translation": 2,
    "colors": 1,
    "rotation": 0,
    "extra_attr": 4,
}

_SPRITE_ORDER_A = ("position", "translate", "colors", "tex_coords", "scale", "rotation")
_SPRITE_ORDER_B = ("rotation", "scale", "tex_coords", "colors", "translate", "position")
_SHAPE_ORDER_A = ("position", "translation", "colors", "rotation")
_SHAPE_ORDER_B = ("rotation", "colors", "translation", "position")


def _is_gl2_backend() -> bool:
    return pyglet.options.backend in GraphicsAPI.GL2


def _build_program(vertex_source: str, fragment_source: str):
    vertex = pyglet.graphics.Shader(vertex_source, "vertex")
    fragment = pyglet.graphics.Shader(fragment_source, "fragment")
    return pyglet.graphics.ShaderProgram(vertex, fragment)


def _sprite_fragment_source() -> str:
    if _is_gl2_backend():
        return """#version 110
        varying vec4 vertex_colors;

        void main()
        {
            gl_FragColor = vertex_colors;
        }
    """
    return """#version 330 core
    in vec4 vertex_colors;
    out vec4 final_colors;

    void main()
    {
        final_colors = vertex_colors;
    }
"""


def _shape_fragment_source() -> str:
    if _is_gl2_backend():
        return """#version 110
        varying vec4 vertex_colors;

        void main()
        {
            gl_FragColor = vertex_colors;
        }
    """
    return """#version 330 core
    in vec4 vertex_colors;
    out vec4 final_color;

    void main()
    {
        final_color = vertex_colors;
    }
"""


def _sprite_vertex_source_gl3(layout: dict[str, int], *, include_extra: bool = False, include_rotation: bool = True) -> str:
    rotation_decl = f"layout(location = {layout['rotation']}) in float rotation;" if include_rotation else ""
    extra_decl = f"layout(location = {layout['extra_attr']}) in float extra_attr;" if include_extra else ""
    rotation_expr = "rotation" if include_rotation else "0.0"
    extra_expr = "extra_attr * 0.00001" if include_extra else "0.0"

    return f"""#version 330 core
    layout(location = {layout['position']}) in vec3 position;
    layout(location = {layout['translate']}) in vec3 translate;
    layout(location = {layout['colors']}) in vec4 colors;
    layout(location = {layout['tex_coords']}) in vec3 tex_coords;
    layout(location = {layout['scale']}) in vec2 scale;
    {rotation_decl}
    {extra_decl}

    out vec4 vertex_colors;

    void main()
    {{
        float theta = radians({rotation_expr});
        mat2 r = mat2(cos(theta), -sin(theta), sin(theta), cos(theta));
        vec2 rotated = r * (position.xy * scale);
        vec2 bias = tex_coords.xy * 0.0001 + vec2(dot(colors.rgb, vec3(0.00001)), colors.a * 0.00001);
        gl_Position = vec4(rotated * 0.01 + translate.xy * 0.01 + bias, (position.z + translate.z) * 0.01, 1.0);
        gl_Position.x += {extra_expr};
        vertex_colors = colors;
    }}
"""


def _sprite_vertex_source_gl2(order: tuple[str, ...], *, include_extra: bool = False, include_rotation: bool = True) -> str:
    decls = {
        "position": "attribute vec3 position;",
        "translate": "attribute vec3 translate;",
        "colors": "attribute vec4 colors;",
        "tex_coords": "attribute vec3 tex_coords;",
        "scale": "attribute vec2 scale;",
        "rotation": "attribute float rotation;",
        "extra_attr": "attribute float extra_attr;",
    }
    names = list(order)
    if include_rotation and "rotation" not in names:
        names.append("rotation")
    if include_extra and "extra_attr" not in names:
        names.append("extra_attr")

    rotation_expr = "rotation" if include_rotation else "0.0"
    extra_expr = "extra_attr * 0.00001" if include_extra else "0.0"
    lines = "\n    ".join(decls[name] for name in names)
    return f"""#version 110
    {lines}
    varying vec4 vertex_colors;

    void main()
    {{
        float theta = radians({rotation_expr});
        mat2 r = mat2(cos(theta), -sin(theta), sin(theta), cos(theta));
        vec2 rotated = r * (position.xy * scale);
        vec2 bias = tex_coords.xy * 0.0001 + vec2(dot(colors.rgb, vec3(0.00001)), colors.a * 0.00001);
        gl_Position = vec4(rotated * 0.01 + translate.xy * 0.01 + bias, (position.z + translate.z) * 0.01, 1.0);
        gl_Position.x += {extra_expr};
        vertex_colors = colors;
    }}
"""


def _shape_vertex_source_gl3(layout: dict[str, int], *, include_extra: bool = False, include_rotation: bool = True) -> str:
    rotation_decl = f"layout(location = {layout['rotation']}) in float rotation;" if include_rotation else ""
    extra_decl = f"layout(location = {layout['extra_attr']}) in float extra_attr;" if include_extra else ""
    rotation_expr = "rotation" if include_rotation else "0.0"
    extra_expr = "extra_attr * 0.00001" if include_extra else "0.0"

    return f"""#version 330 core
    layout(location = {layout['position']}) in vec2 position;
    layout(location = {layout['translation']}) in vec3 translation;
    layout(location = {layout['colors']}) in vec4 colors;
    {rotation_decl}
    {extra_decl}

    out vec4 vertex_colors;

    void main()
    {{
        float theta = radians({rotation_expr});
        mat2 r = mat2(cos(theta), -sin(theta), sin(theta), cos(theta));
        vec2 rotated = r * position;
        gl_Position = vec4(rotated * 0.01 + translation.xy * 0.01, translation.z * 0.01, 1.0);
        gl_Position.x += dot(colors.rgb, vec3(0.00001)) + colors.a * 0.00001 + {extra_expr};
        vertex_colors = colors;
    }}
"""


def _shape_vertex_source_gl2(order: tuple[str, ...], *, include_extra: bool = False, include_rotation: bool = True) -> str:
    decls = {
        "position": "attribute vec2 position;",
        "translation": "attribute vec3 translation;",
        "colors": "attribute vec4 colors;",
        "rotation": "attribute float rotation;",
        "extra_attr": "attribute float extra_attr;",
    }
    names = list(order)
    if include_rotation and "rotation" not in names:
        names.append("rotation")
    if include_extra and "extra_attr" not in names:
        names.append("extra_attr")

    rotation_expr = "rotation" if include_rotation else "0.0"
    extra_expr = "extra_attr * 0.00001" if include_extra else "0.0"
    lines = "\n    ".join(decls[name] for name in names)
    return f"""#version 110
    {lines}
    varying vec4 vertex_colors;

    void main()
    {{
        float theta = radians({rotation_expr});
        mat2 r = mat2(cos(theta), -sin(theta), sin(theta), cos(theta));
        vec2 rotated = r * position;
        gl_Position = vec4(rotated * 0.01 + translation.xy * 0.01, translation.z * 0.01, 1.0);
        gl_Position.x += dot(colors.rgb, vec3(0.00001)) + colors.a * 0.00001 + {extra_expr};
        vertex_colors = colors;
    }}
"""


def _sprite_vertex_source(layout_or_order, *, include_extra: bool = False, include_rotation: bool = True) -> str:
    if _is_gl2_backend():
        return _sprite_vertex_source_gl2(layout_or_order, include_extra=include_extra, include_rotation=include_rotation)
    return _sprite_vertex_source_gl3(layout_or_order, include_extra=include_extra, include_rotation=include_rotation)


def _shape_vertex_source(layout_or_order, *, include_extra: bool = False, include_rotation: bool = True) -> str:
    if _is_gl2_backend():
        return _shape_vertex_source_gl2(layout_or_order, include_extra=include_extra, include_rotation=include_rotation)
    return _shape_vertex_source_gl3(layout_or_order, include_extra=include_extra, include_rotation=include_rotation)


def _location_map(program, names: tuple[str, ...]) -> dict[str, int]:
    return {name: program.attributes[name].location for name in names if name in program.attributes}


def _assert_program_switch_success(
    drawable,
    new_program,
    *,
    expect_recreated: bool,
    expect_same_domain: bool,
) -> None:
    old_vlist = drawable._vertex_list
    old_domain = old_vlist.domain
    old_group = old_vlist.group

    drawable.program = new_program

    new_vlist = drawable._vertex_list
    assert new_vlist.group is drawable._group

    if expect_recreated:
        assert new_vlist is not old_vlist
        assert old_vlist.bucket is None
    else:
        assert new_vlist is old_vlist

    if expect_same_domain:
        assert new_vlist.domain is old_domain
    else:
        assert new_vlist.domain is not old_domain

    assert old_domain.get_drawable_bucket(old_group) is None
    assert new_vlist.domain.get_drawable_bucket(new_vlist.group) is not None


def _program_switch_expectations(drawable, new_program) -> tuple[bool, bool]:
    batch = drawable._batch
    assert batch is not None

    old_vlist = drawable._vertex_list
    old_key = batch._attributes_key(old_vlist.domain.attribute_meta)
    normalized_attributes = batch._normalized_shader_attributes(new_program, old_vlist.initial_attribs)

    # update_shader compares using drawable-owned attributes.
    update_attributes = {
        name: normalized_attributes[name]
        for name in old_vlist.initial_attribs
        if name in normalized_attributes
    }
    update_key = batch._attributes_key(update_attributes)
    if update_key == old_key:
        return False, True

    # Recreate paths (for Sprite/Shape) only pass object-owned vertex data keys.
    recreate_attributes = {
        name: normalized_attributes[name]
        for name in old_vlist.initial_attribs
        if name in normalized_attributes
    }
    recreate_key = batch._attributes_key(recreate_attributes)
    return True, recreate_key == old_key


def _assert_program_switch_missing_attribute_raises(drawable, new_program) -> None:
    old_vlist = drawable._vertex_list
    old_domain = old_vlist.domain
    old_group = old_vlist.group

    with pytest.raises(MissingAttributeException):
        drawable.program = new_program

    assert drawable._vertex_list is old_vlist
    assert old_vlist.bucket is None
    assert old_domain.get_drawable_bucket(old_group) is None

    # The original list was explicitly deleted before failing recreation.
    # Avoid a second delete in object finalizers.
    drawable._vertex_list = None


@pytest.fixture(scope="module")
def sprite_programs(gl3_context):  # noqa: ARG001
    fragment_source = _sprite_fragment_source()
    if _is_gl2_backend():
        base = _build_program(_sprite_vertex_source(_SPRITE_ORDER_A), fragment_source)
        same = _build_program(_sprite_vertex_source(_SPRITE_ORDER_A), fragment_source)
        different = _build_program(_sprite_vertex_source(_SPRITE_ORDER_B), fragment_source)
        extra = _build_program(_sprite_vertex_source(_SPRITE_ORDER_A, include_extra=True), fragment_source)
        missing = _build_program(_sprite_vertex_source(_SPRITE_ORDER_A, include_rotation=False), fragment_source)
    else:
        base = _build_program(_sprite_vertex_source(_SPRITE_LAYOUT_A), fragment_source)
        same = _build_program(_sprite_vertex_source(_SPRITE_LAYOUT_A), fragment_source)
        different = _build_program(_sprite_vertex_source(_SPRITE_LAYOUT_B), fragment_source)
        extra = _build_program(_sprite_vertex_source(_SPRITE_LAYOUT_A, include_extra=True), fragment_source)
        missing = _build_program(_sprite_vertex_source(_SPRITE_LAYOUT_A, include_rotation=False), fragment_source)

    programs = {"base": base, "same": same, "different": different, "extra": extra, "missing": missing}
    try:
        yield programs
    finally:
        for program in programs.values():
            program.delete()


@pytest.fixture(scope="module")
def shape_programs(gl3_context):  # noqa: ARG001
    fragment_source = _shape_fragment_source()
    if _is_gl2_backend():
        base = _build_program(_shape_vertex_source(_SHAPE_ORDER_A), fragment_source)
        same = _build_program(_shape_vertex_source(_SHAPE_ORDER_A), fragment_source)
        different = _build_program(_shape_vertex_source(_SHAPE_ORDER_B), fragment_source)
        extra = _build_program(_shape_vertex_source(_SHAPE_ORDER_A, include_extra=True), fragment_source)
        missing = _build_program(_shape_vertex_source(_SHAPE_ORDER_A, include_rotation=False), fragment_source)
    else:
        base = _build_program(_shape_vertex_source(_SHAPE_LAYOUT_A), fragment_source)
        same = _build_program(_shape_vertex_source(_SHAPE_LAYOUT_A), fragment_source)
        different = _build_program(_shape_vertex_source(_SHAPE_LAYOUT_B), fragment_source)
        extra = _build_program(_shape_vertex_source(_SHAPE_LAYOUT_A, include_extra=True), fragment_source)
        missing = _build_program(_shape_vertex_source(_SHAPE_LAYOUT_A, include_rotation=False), fragment_source)

    programs = {"base": base, "same": same, "different": different, "extra": extra, "missing": missing}
    try:
        yield programs
    finally:
        for program in programs.values():
            program.delete()


@pytest.fixture()
def sprite_image():
    pixels = [255, 255, 255, 255] * 4
    return pyglet.image.ImageData(2, 2, "RGBA", bytes(pixels))


def test_sprite_program_change_same_attributes_keeps_domain_updates_group(gl3_context, sprite_programs, sprite_image):  # noqa: ARG001
    """Switch Sprite to a program with identical attributes.

    Verifies domain reuse vs recreation follows resolved attribute-key compatibility, and group/program state updates.
    """
    batch = pyglet.graphics.Batch()
    sprite = pyglet.sprite.Sprite(sprite_image, x=0, y=0, batch=batch, program=sprite_programs["base"])
    expect_recreated, expect_same_domain = _program_switch_expectations(sprite, sprite_programs["same"])

    try:
        _assert_program_switch_success(
            sprite,
            sprite_programs["same"],
            expect_recreated=expect_recreated,
            expect_same_domain=expect_same_domain,
        )
    finally:
        sprite.delete()


def test_sprite_program_change_different_attributes_recreates_with_new_domain(gl3_context, sprite_programs, sprite_image):  # noqa: ARG001
    """Switch Sprite to a program whose attribute layout differs.

    Verifies the vertex list is recreated and migrated to a new domain.
    """
    if _is_gl2_backend():
        names = ("position", "translate", "colors", "tex_coords", "scale", "rotation")
        if _location_map(sprite_programs["base"], names) == _location_map(sprite_programs["different"], names):
            pytest.xfail("Driver assigned identical attribute locations for reordered GLSL 110 declarations.")

    batch = pyglet.graphics.Batch()
    sprite = pyglet.sprite.Sprite(sprite_image, x=0, y=0, batch=batch, program=sprite_programs["base"])

    try:
        _assert_program_switch_success(
            sprite,
            sprite_programs["different"],
            expect_recreated=True,
            expect_same_domain=False,
        )
    finally:
        sprite.delete()


def test_sprite_program_change_same_attributes_plus_one_recreates_in_same_domain(gl3_context, sprite_programs, sprite_image):  # noqa: ARG001
    """Switch Sprite to a program with one additional attribute.

    Verifies domain reuse vs recreation matches backend-resolved attribute-key compatibility for the new program.
    """
    batch = pyglet.graphics.Batch()
    sprite = pyglet.sprite.Sprite(sprite_image, x=0, y=0, batch=batch, program=sprite_programs["base"])
    expect_recreated, expect_same_domain = _program_switch_expectations(sprite, sprite_programs["extra"])

    try:
        _assert_program_switch_success(
            sprite,
            sprite_programs["extra"],
            expect_recreated=expect_recreated,
            expect_same_domain=expect_same_domain,
        )
    finally:
        sprite.delete()


def test_sprite_program_change_missing_attribute_raises_and_removes_old_bucket(gl3_context, sprite_programs, sprite_image):  # noqa: ARG001
    """Switch Sprite to a program missing a required attribute.

    Verifies assignment raises and the previous bucket allocation is cleaned up.
    """
    batch = pyglet.graphics.Batch()
    sprite = pyglet.sprite.Sprite(sprite_image, x=0, y=0, batch=batch, program=sprite_programs["base"])
    _assert_program_switch_missing_attribute_raises(sprite, sprite_programs["missing"])


def test_shape_program_change_same_attributes_keeps_domain_updates_group(gl3_context, shape_programs):  # noqa: ARG001
    """Switch Shape to a program with identical attributes.

    Verifies domain reuse vs recreation follows resolved attribute-key compatibility, with correct group/program updates.
    """
    batch = pyglet.graphics.Batch()
    shape = pyglet.shapes.Circle(32, 32, 16, batch=batch, program=shape_programs["base"])
    expect_recreated, expect_same_domain = _program_switch_expectations(shape, shape_programs["same"])

    try:
        _assert_program_switch_success(
            shape,
            shape_programs["same"],
            expect_recreated=expect_recreated,
            expect_same_domain=expect_same_domain,
        )
    finally:
        shape.delete()


def test_shape_program_change_different_attributes_recreates_with_new_domain(gl3_context, shape_programs):  # noqa: ARG001
    """Switch Shape to a program with a different attribute layout.

    Verifies the vertex list is recreated in a different domain.
    """
    if _is_gl2_backend():
        names = ("position", "translation", "colors", "rotation")
        if _location_map(shape_programs["base"], names) == _location_map(shape_programs["different"], names):
            pytest.xfail("Driver assigned identical attribute locations for reordered GLSL 110 declarations.")

    batch = pyglet.graphics.Batch()
    shape = pyglet.shapes.Circle(32, 32, 16, batch=batch, program=shape_programs["base"])

    try:
        _assert_program_switch_success(
            shape,
            shape_programs["different"],
            expect_recreated=True,
            expect_same_domain=False,
        )
    finally:
        shape.delete()


def test_shape_program_change_same_attributes_plus_one_recreates_in_same_domain(gl3_context, shape_programs):  # noqa: ARG001
    """Switch Shape to a program that adds one extra attribute.

    Verifies domain reuse vs recreation matches backend-resolved attribute-key compatibility for the new program.
    """
    batch = pyglet.graphics.Batch()
    shape = pyglet.shapes.Circle(32, 32, 16, batch=batch, program=shape_programs["base"])
    expect_recreated, expect_same_domain = _program_switch_expectations(shape, shape_programs["extra"])

    try:
        _assert_program_switch_success(
            shape,
            shape_programs["extra"],
            expect_recreated=expect_recreated,
            expect_same_domain=expect_same_domain,
        )
    finally:
        shape.delete()


def test_shape_program_change_missing_attribute_raises_and_removes_old_bucket(gl3_context, shape_programs):  # noqa: ARG001
    """Switch Shape to a program missing a required attribute.

    Verifies failure is raised and stale bucket ownership is released."""
    batch = pyglet.graphics.Batch()
    shape = pyglet.shapes.Circle(32, 32, 16, batch=batch, program=shape_programs["base"])
    _assert_program_switch_missing_attribute_raises(shape, shape_programs["missing"])
