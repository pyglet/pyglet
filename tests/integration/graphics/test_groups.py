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

def _validate_group(batch, no_state_groups, state_groups, expected_sets, expected_unsets, expected_optimized_sets,
                    expected_optimized_unsets, expected_binds, expected_draws):
    draw_list, _ = batch._create_draw_list()  # noqa: SLF001

    assert len([domain for domain, mode, draw_group in draw_list if mode == 'set']) == expected_sets
    assert len([domain for domain, mode, draw_group in draw_list if mode == 'unset']) == expected_unsets

    draw_list_groups = [draw_group for domain, mode, draw_group in draw_list]

    optimized = batch._optimize_draw_list(draw_list)  # noqa: SLF001

    optimized_bound_instances = [func.__self__ for func in optimized if hasattr(func, '__self__')]

    for nsg in no_state_groups:
        assert nsg in draw_list_groups  # Group exists in original draw list.
        assert nsg not in optimized_bound_instances  # No state, no set.

    for sg in state_groups:
        assert sg in draw_list_groups  # Group exists in original draw list.
        assert sg in optimized_bound_instances  # State set, should be found.

    # set_state, bind, <lambda>, and unset_state
    function_names = [func.__name__ for func in optimized]

    assert function_names.count("set_state") == expected_optimized_sets
    assert function_names.count("unset_state") == expected_optimized_unsets
    assert function_names.count("bind") == expected_binds
    assert function_names.count("<lambda>") == expected_draws


def test_group_parent_no_state():
    # Make sure a parent state is optimized out if it has no state. 
    batch = pyglet.experimental.graphics.Batch()

    group = GroupNoState()

    sprite = pyglet.sprite.Sprite(test_image, x=0, y=0, group=group, batch=batch)

    _validate_group(batch, [group], [sprite._group],
                    expected_sets=2,
                    expected_unsets=2,
                    expected_optimized_sets=1,
                    expected_optimized_unsets=1,
                    expected_draws=1,
                    expected_binds=1,
                    )

def test_group_parent_with_state():
    """State should be kept of parent."""
    batch = pyglet.experimental.graphics.Batch()

    group = GroupWithUniqueGLState()

    sprite = pyglet.sprite.Sprite(test_image, x=0, y=0, group=group, batch=batch)

    _validate_group(batch, [], [group, sprite._group],
                    expected_sets=2,
                    expected_unsets=2,
                    expected_optimized_sets=2,
                    expected_optimized_unsets=2,
                    expected_draws=1,
                    expected_binds=1,
                    )


def test_group_no_parent():
    # Make sure parent state exists if a child changes it
    batch = pyglet.experimental.graphics.Batch()

    sprite = pyglet.sprite.Sprite(test_image, x=0, y=0, batch=batch)

    _validate_group(batch, [], [sprite._group],
                    expected_sets=1,
                    expected_unsets=1,
                    expected_optimized_sets=1,
                    expected_optimized_unsets=1,
                    expected_draws=1,
                    expected_binds=1,
                    )


def test_group_ordering():
    # Make sure groups are ordered by ordering number.
    pass


def test_group_consolidation():
    # Make sure the same groups consolidate.
    batch = pyglet.experimental.graphics.Batch()

    sprite = pyglet.sprite.Sprite(test_image, x=0, y=0, batch=batch)
    sprite2 = pyglet.sprite.Sprite(test_image, x=0, y=0, batch=batch)

    _validate_group(batch, [], [sprite._group, sprite2._group],
                    expected_sets=1,
                    expected_unsets=1,
                    expected_optimized_sets=1,
                    expected_optimized_unsets=1,
                    expected_draws=1,
                    expected_binds=1,
                    )


def test_group_comparison():
    # Make sure similar groups compare to eachother.
    pass


def test_group_deletion():
    # Make sure groups are freed from the domain and batch when removed.
    batch = pyglet.experimental.graphics.Batch()

    sprite = pyglet.sprite.Sprite(test_image, x=0, y=0, batch=batch)
    
    domain = sprite._vertex_list.domain
    group = sprite._group
    
    sprite.delete()
    
    assert group not in domain.group_vertex_ranges
    assert group not in domain.group_index_ranges
    
    # Domain should actually still exist, until the draw list is recreated.
    assert domain in list(batch.domain_map.values())
    
    batch._update_draw_list()
    
    # Ensure an empty domain is removed and the group is removed.
    assert domain not in list(batch.domain_map.values())
    assert group not in batch.top_groups


def test_group_buildup():
    # Ensure group count in a domain does not exceed the total number of groups.
    pass
