import ctypes
from dataclasses import dataclass
from unittest.mock import MagicMock

import pyglet
from pyglet.enums import CompareOp
from pyglet.graphics.state import State


class UniqueState(State):
    sets_state = True

@dataclass(frozen=True)
class SameState(State):
    sets_state = True

class GroupNoState(pyglet.graphics.Group):
    """This group has no state to be set.

    It should be optimized out.
    """


class GroupWithUniqueState(pyglet.graphics.Group):
    """This group has a state.

    The state is unique and shouldn't match others.
    """
    def __init__(self):
        super().__init__()
        self.add_state(UniqueState())


class GroupWithSimilarState(pyglet.graphics.Group):
    """This group has a state.

    The state is a dataclass and should match others.
    """
    def __init__(self):
        super().__init__()
        self.add_state(SameState())


test_image = pyglet.image.ImageData(1, 1, 'RGBA', (ctypes.c_byte * 4)(0, 0, 0, 0))

def _validate_group(batch, expected_groups, expected_sets, expected_unsets, expected_binds, expected_draws):
    draw_list = batch._create_draw_list()  # noqa: SLF001

    batch._draw_list = draw_list

    original_function_names = [func.__name__ for func in draw_list]

    assert original_function_names.count("set_state") == expected_sets
    assert original_function_names.count("unset_state") == expected_unsets
    assert original_function_names.count("_bind_vao") == expected_binds
    assert original_function_names.count("_draw") == expected_draws


def test_group_parent_no_state(gl3_context):
    # Make sure a parent state is optimized out if it has no state.
    batch = pyglet.graphics.Batch()

    group = GroupNoState()

    sprite = pyglet.sprite.Sprite(test_image, x=0, y=0, group=group, batch=batch)

    _validate_group(batch, expected_groups=[sprite._group],
                    expected_sets=5,  # program, blend enable, blend mode, active texture, texture state
                    expected_unsets=2,
                    expected_draws=1,
                    expected_binds=1,
                    )

def test_group_parent_with_state(gl3_context):
    """State should be kept of parent."""
    batch = pyglet.graphics.Batch()

    group = GroupWithUniqueState()

    sprite = pyglet.sprite.Sprite(test_image, x=0, y=0, group=group, batch=batch)

    _validate_group(batch, [group],
                    expected_sets=6,  # Calls an empty state function.
                    expected_unsets=2,
                    expected_draws=1,
                    expected_binds=1,
                    )


def test_group_no_parent(gl3_context):
    """Make sure parent state exists if a child changes it."""
    batch = pyglet.graphics.Batch()

    sprite = pyglet.sprite.Sprite(test_image, x=0, y=0, batch=batch)

    _validate_group(batch, [sprite._group],
                    expected_sets=5,
                    expected_unsets=2,
                    expected_draws=1,
                    expected_binds=1,
                    )


def test_group_ordering(gl3_context):
    # Make sure groups are ordered by ordering number.
    pass


def test_group_consolidation(gl3_context):
    """Make sure the same groups consolidate properly."""
    batch = pyglet.graphics.Batch()

    sprite = pyglet.sprite.Sprite(test_image, x=0, y=0, batch=batch)
    sprite2 = pyglet.sprite.Sprite(test_image, x=0, y=0, batch=batch)

    _validate_group(batch, [sprite._group, sprite2._group],
                    expected_sets=5,
                    expected_unsets=2,
                    expected_draws=1,
                    expected_binds=1,
                    )

def test_similar_group_equal_comparison():
    """Ensure groups that are similar will equal each other or rendering may break."""
    group1 = pyglet.graphics.Group()
    group1.set_viewport(0, 0, 100, 100)
    group1.set_depth_test(CompareOp.EQUAL)

    group2 = pyglet.graphics.Group()
    group2.set_viewport(0, 0, 100, 100)
    group2.set_depth_test(CompareOp.EQUAL)

    assert group2 == group1
    assert group2 is not group1

def test_similar_group_equal_comparison_inherit():
    """Same as above, but groups that added their state within the group creation."""
    group1 = GroupWithSimilarState()
    group2 = GroupWithSimilarState()

    assert group2 == group1
    assert group2 is not group1

def test_different_group_equal_add_comparison():
    """Ensure groups that are different will not equal each other or rendering may break."""
    group1 = pyglet.graphics.Group()
    group1.set_viewport(0, 0, 200, 200)

    group2 = pyglet.graphics.Group()
    group2.set_viewport(0, 0, 100, 100)

    assert group2 != group1
    assert group2 is not group1

def test_group_custom_state_comparison():
    """Ensure states that aren't dataclasses will not equal each other or rendering may break."""
    group1 = GroupWithUniqueState()
    group2 = GroupWithUniqueState()

    assert group2 != group1
    assert group2 is not group1

def test_group_custom_state_dataclass_comparison():
    """Ensure states that are dataclasses will equal each other or rendering may break."""
    @dataclass(frozen=True)
    class MyState(State):
        sets_state = True

    custom_state = MyState()
    group1 = pyglet.graphics.Group()
    group1.add_state(custom_state)

    other_custom_state = MyState()
    group2 = pyglet.graphics.Group()
    group2.add_state(other_custom_state)

    assert group2 == group1
    assert group2 is not group1

def _test_sprite_deletion(sprite, batch):
    domain = sprite._vertex_list.domain
    group = sprite._group
    removed_vlist = sprite._vertex_list

    sprite.delete()

    assert sprite._vertex_list is None
    assert removed_vlist.bucket is None  # should have no bucket after removal.

    # Group should actually still exist, until the draw list is recreated.
    assert domain in list(batch._domain_registry.values())
    assert domain.has_bucket(group) == True
    assert group in domain._vertex_buckets

def test_single_group_deletion(gl3_context):
    """Make sure groups are freed from the domain and their buckets when removed."""
    batch = pyglet.graphics.Batch()

    sprite = pyglet.sprite.Sprite(test_image, x=0, y=0, batch=batch)

    domain = sprite._vertex_list.domain
    group = sprite._group

    _test_sprite_deletion(sprite, batch)

    # Recreate draw list after deletion.
    batch._update_draw_list()
    batch.delete_empty_domains()

    # Ensure an empty domain is removed and the group is removed.
    assert group not in batch.top_groups
    assert domain not in list(batch._domain_registry.values())
    assert domain.has_bucket(group) == False


def test_group_persistence_deletion(gl3_context):
    """Creates two sprites and deletes one to ensure resources still exist for the other."""
    batch = pyglet.graphics.Batch()

    sprite = pyglet.sprite.Sprite(test_image, x=0, y=0, batch=batch)
    group = sprite._group
    domain = sprite._vertex_list.domain

    sprite2 = pyglet.sprite.Sprite(test_image, x=0, y=0, batch=batch)

    batch._update_draw_list()

    # Ensure group bucket still exists because only one was removed.
    assert group in batch.top_groups
    assert domain in batch._domain_registry.values()
    assert domain.has_bucket(group) == True
