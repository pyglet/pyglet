import ctypes
from dataclasses import dataclass
from typing import TypedDict

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


pixels = 4
test_image = pyglet.image.ImageData(2, 2, 'RGBA', (ctypes.c_byte * (pixels * 4))(*[0, 0, 0, 0] * pixels))
test_image2 = pyglet.image.ImageData(1, 1, 'RGBA', (ctypes.c_byte * 4)(0, 0, 0, 0))

class DrawListValidation(TypedDict):
    sets: int
    unsets: int
    binds: int
    groups: int
    opt_sets: int
    opt_unsets: int
    opt_binds: int
    opt_draws: int

def validate_draw_list(batch: pyglet.graphics.Batch) -> DrawListValidation:
    """Doing it this way otherwise pytest will error and stop at validate_draw_list in the test.

    When it does this, you cannot determine which of the comparisons actually failed.
    """
    draw_list = batch._create_draw_list()  # noqa: SLF001

    sets = 0
    unsets = 0
    domains = set()
    groups = set()

    for (domain, mode_or_set, group) in draw_list:
        if mode_or_set == "set":
            sets += 1
        elif mode_or_set == "unset":
            unsets += 1

        if domain is not None:
            domains.add(domain)
        if group is not None:
            groups.add(group)

    # Contains actual functions.
    optimized_list = batch._optimize_draw_list(draw_list)
    original_function_names = [func.__name__ for func in optimized_list]

    return {
        "sets": sets,
        "unsets": unsets,
        "binds": len(domains),
        "groups": len(groups),
        "opt_sets": original_function_names.count("set_state"),
        "opt_unsets": original_function_names.count("unset_state"),
        "opt_binds": original_function_names.count("_bind_vao"),
        "opt_draws": original_function_names.count("_draw"),
    }

# Test texture regions to match .

def _validate_state_count(group, *, count: int, expanded_count: int):
    """Makes sure the added state count matches the expected count.
    """
    assert len(group._states) == count
    assert len(group._expanded_states) == expanded_count


def test_group_parent_no_state(gl3_context):
    # Make sure a parent state is optimized out if it has no state.
    batch = pyglet.graphics.Batch()

    group = GroupNoState()

    sprite = pyglet.sprite.Sprite(test_image, x=0, y=0, group=group, batch=batch)

    _validate_state_count(group, count=0, expanded_count=0)
    _validate_state_count(sprite._group, count=3, expanded_count=5)

    vdl = validate_draw_list(batch)

    assert vdl["sets"] == 2
    assert vdl["unsets"] == 2
    assert vdl["groups"] == 2
    assert vdl["binds"] == 1

    assert vdl["opt_sets"] == 5
    assert vdl["opt_unsets"] == 1
    assert vdl["opt_draws"] == 1
    assert vdl["opt_binds"] == 1


def test_group_parent_with_state(gl3_context):
    """State should be kept of parent."""
    batch = pyglet.graphics.Batch()

    group = GroupWithUniqueState()

    sprite = pyglet.sprite.Sprite(test_image, x=0, y=0, group=group, batch=batch)

    _validate_state_count(group, count=1, expanded_count=1)
    _validate_state_count(sprite._group, count=3, expanded_count=5)

    vdl = validate_draw_list(batch)

    assert vdl["sets"] == 2
    assert vdl["unsets"] == 2
    assert vdl["groups"] == 2
    assert vdl["binds"] == 1

    assert vdl["opt_sets"] == 6
    assert vdl["opt_unsets"] == 1
    assert vdl["opt_draws"] == 1
    assert vdl["opt_binds"] == 1


def test_group_no_parent(gl3_context):
    """Make sure parent state exists if a child changes it."""
    batch = pyglet.graphics.Batch()

    sprite = pyglet.sprite.Sprite(test_image, x=0, y=0, batch=batch)

    _validate_state_count(sprite._group, count=3, expanded_count=5)

    vdl = validate_draw_list(batch)

    assert vdl["sets"] == 1
    assert vdl["unsets"] == 1
    assert vdl["groups"] == 1
    assert vdl["binds"] == 1

    assert vdl["opt_sets"] == 5
    assert vdl["opt_unsets"] == 1
    assert vdl["opt_draws"] == 1
    assert vdl["opt_binds"] == 1

def test_group_ordering(gl3_context):
    # Make sure groups are ordered by ordering number.
    pass


def test_group_consolidation(gl3_context):
    """Make sure the same groups consolidate properly."""
    batch = pyglet.graphics.Batch()

    sprite = pyglet.sprite.Sprite(test_image, x=0, y=0, batch=batch)
    sprite2 = pyglet.sprite.Sprite(test_image, x=0, y=0, batch=batch)

    _validate_state_count(sprite._group, count=3, expanded_count=5)
    _validate_state_count(sprite2._group, count=3, expanded_count=5)

    vdl = validate_draw_list(batch)

    assert vdl["sets"] == 1
    assert vdl["unsets"] == 1
    assert vdl["groups"] == 1
    assert vdl["binds"] == 1

    assert vdl["opt_sets"] == 5
    assert vdl["opt_unsets"] == 1
    assert vdl["opt_draws"] == 1
    assert vdl["opt_binds"] == 1

def test_group_differing_textures(gl3_context):
    batch = pyglet.graphics.Batch()

    sprite = pyglet.sprite.Sprite(test_image, x=0, y=0, batch=batch)
    
    sprite2 = pyglet.sprite.Sprite(test_image2, x=0, y=0, batch=batch)

    _validate_state_count(sprite._group, count=3, expanded_count=5)
    _validate_state_count(sprite2._group, count=3, expanded_count=5)

    vdl = validate_draw_list(batch)

    assert vdl["sets"] == 2
    assert vdl["unsets"] == 2
    assert vdl["groups"] == 2
    assert vdl["binds"] == 1

    assert vdl["opt_sets"] == 6
    assert vdl["opt_unsets"] == 1
    assert vdl["opt_draws"] == 2
    assert vdl["opt_binds"] == 1

def test_group_texture_same_region(gl3_context):
    batch = pyglet.graphics.Batch()

    texture = test_image.get_texture()
    sprite = pyglet.sprite.Sprite(texture, x=0, y=0, batch=batch)

    sprite2 = pyglet.sprite.Sprite(texture.get_region(0, 0, 1, 1), x=0, y=0, batch=batch)

    _validate_state_count(sprite._group, count=3, expanded_count=5)
    _validate_state_count(sprite2._group, count=3, expanded_count=5)

    vdl = validate_draw_list(batch)

    assert vdl["sets"] == 1
    assert vdl["unsets"] == 1
    assert vdl["groups"] == 1
    assert vdl["binds"] == 1

    assert vdl["opt_sets"] == 5
    assert vdl["opt_unsets"] == 1
    assert vdl["opt_draws"] == 1  # Same draw, different texture.
    assert vdl["opt_binds"] == 1

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
