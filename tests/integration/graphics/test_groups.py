import ctypes
from unittest.mock import MagicMock

import pyglet


class GroupNoState(pyglet.graphics.Group):
    """This group has no state to be set.

    It should be optimized out.
    """


class GroupWithUniqueGLState(pyglet.graphics.Group):
    """This group has a state.

    It should exist after optimization.
    """
    def initialize(self):
        self.set_states = [pyglet.graphics.GLState(pyglet.gl.gl.glEnable, (pyglet.gl.gl.GL_SCISSOR_TEST,))]


test_image = pyglet.image.ImageData(1, 1, 'RGBA', (ctypes.c_byte * 4)(0, 0, 0, 0))

import inspect

def _validate_group(batch, no_state_groups, state_groups, expected_sets, expected_unsets, expected_optimized_sets,
                    expected_optimized_unsets, expected_binds, expected_draws):
    draw_list = batch._create_draw_list()  # noqa: SLF001

    batch._draw_list = draw_list

    original_function_names = [func.__name__ for func in draw_list]

    print(original_function_names)

    assert original_function_names.count("set_state") == expected_sets
    assert original_function_names.count("unset_state") == expected_unsets

    vao_binds = original_function_names.count("bind_vao")
    draw_calls = original_function_names.count("<lambda>")

    print("VAO", vao_binds, "DRAW", draw_calls)

    # draw_list_groups = [draw_group for domain, mode, draw_group in draw_list]
    #
    # optimized = batch._optimize_draw_list(draw_list)  # noqa: SLF001
    #
    # optimized_bound_instances = [func.__self__ for func in optimized if hasattr(func, '__self__')]
    #

    # for nsg in no_state_groups:
    #     assert nsg in draw_list_groups  # Group exists in original draw list.
    #     assert nsg not in optimized_bound_instances  # No state, no set.
    #
    # for sg in state_groups:
    #     assert sg in draw_list_groups  # Group exists in original draw list.
    #     assert sg in optimized_bound_instances  # State set, should be found.
    #
    # # set_state, bind, <lambda>, and unset_state
    # function_names = [func.__name__ for func in optimized]
    #
    # assert function_names.count("set_state") == expected_optimized_sets
    # assert function_names.count("unset_state") == expected_optimized_unsets
    # assert function_names.count("bind") == expected_binds
    # assert function_names.count("<lambda>") == expected_draws


def test_group_parent_no_state(gl3_context):
    # Make sure a parent state is optimized out if it has no state.
    batch = pyglet.graphics.Batch()

    group = GroupNoState()

    sprite = pyglet.sprite.Sprite(test_image, x=0, y=0, group=group, batch=batch)

    _validate_group(batch, [group], [sprite._group],
                    expected_sets=5,  # program, blend enable, blend mode, active texture, texture state
                    expected_unsets=2,
                    expected_optimized_sets=1,
                    expected_optimized_unsets=1,
                    expected_draws=1,
                    expected_binds=1,
                    )

def test_group_parent_with_state(gl3_context):
    """State should be kept of parent."""
    batch = pyglet.graphics.Batch()

    group = GroupWithUniqueGLState()

    sprite = pyglet.sprite.Sprite(test_image, x=0, y=0, group=group, batch=batch)

    _validate_group(batch, [], [group, sprite._group],
                    expected_sets=5,
                    expected_unsets=2,
                    expected_optimized_sets=2,
                    expected_optimized_unsets=2,
                    expected_draws=1,
                    expected_binds=1,
                    )


def test_group_no_parent(gl3_context):
    # Make sure parent state exists if a child changes it
    batch = pyglet.graphics.Batch()

    sprite = pyglet.sprite.Sprite(test_image, x=0, y=0, batch=batch)

    _validate_group(batch, [], [sprite._group],
                    expected_sets=5,
                    expected_unsets=2,
                    expected_optimized_sets=1,
                    expected_optimized_unsets=1,
                    expected_draws=1,
                    expected_binds=1,
                    )


def test_group_ordering(gl3_context):
    # Make sure groups are ordered by ordering number.
    pass


def test_group_consolidation(gl3_context):
    # Make sure the same groups consolidate.
    batch = pyglet.graphics.Batch()

    sprite = pyglet.sprite.Sprite(test_image, x=0, y=0, batch=batch)
    sprite2 = pyglet.sprite.Sprite(test_image, x=0, y=0, batch=batch)

    _validate_group(batch, [], [sprite._group, sprite2._group],
                    expected_sets=5,
                    expected_unsets=2,
                    expected_optimized_sets=1,
                    expected_optimized_unsets=1,
                    expected_draws=1,
                    expected_binds=1,
                    )


def test_group_comparison():
    # Make sure similar groups compare to eachother.
    pass


def test_group_deletion(gl3_context):
    # Make sure groups are freed from the domain and batch when removed.
    batch = pyglet.graphics.Batch()

    sprite = pyglet.sprite.Sprite(test_image, x=0, y=0, batch=batch)

    domain = sprite._vertex_list.domain
    group = sprite._group
    removed_vlist = sprite._vertex_list

    sprite.delete()

    assert sprite._vertex_list is None
    assert removed_vlist.bucket is None  # should have no bucket after removal.

    # Group should actually still exist, until the draw list is recreated.
    assert domain in list(batch._domain_registry.values())
    assert domain.has_bucket(group) == True
    assert group in domain._buckets

    batch._update_draw_list()

    # Ensure an empty domain is removed and the group is removed.
    assert group not in batch.top_groups
    assert domain not in batch._domain_registry
    assert domain.has_bucket(group) == False


def test_group_buildup():
    # Ensure group count in a domain does not exceed the total number of groups.
    pass
