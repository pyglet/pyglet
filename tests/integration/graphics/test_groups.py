import ctypes
from dataclasses import dataclass
from typing import TypedDict

import pytest
import pyglet
import pyglet.graphics.draw as graphics_draw
from pyglet.enums import CompareOp, GeometryMode
from pyglet.graphics.draw import _DomainKey
from pyglet.graphics.state import State, Viewport


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
        self.set_state(UniqueState())


class GroupWithSimilarState(pyglet.graphics.Group):
    """This group has a state.

    The state is a dataclass and should match others.
    """
    def __init__(self):
        super().__init__()
        self.set_state(SameState())


@dataclass(frozen=True)
class OtherSameState(State):
    sets_state = True


@dataclass(frozen=True)
class CollidingState(State):
    value: int
    sets_state = True

    def __hash__(self):
        return 1


class IdentityHashGroup(pyglet.graphics.Group):
    def __eq__(self, other):
        return self is other

    def __hash__(self):
        return id(self)


class EagerReferenceGroup(pyglet.graphics.Group):
    """Reference implementation of the state-cache behavior before deferral."""

    def set_state(self, state):
        assert not self.batches
        self._state_names[type(state).__name__] = state  # noqa: SLF001
        group_states = self._state_names.values()  # noqa: SLF001
        self._expanded_states = graphics_draw._expand_states_in_order(group_states)  # noqa: SLF001
        if state.enforced_state:
            self._enforced_states.append(state)  # noqa: SLF001
        self._hashable_states = tuple({item for item in group_states if item.group_hash is True})  # noqa: SLF001
        self._hash = hash((self._order, self.parent, self._hashable_states))  # noqa: SLF001
        self._state_cache_dirty = False  # noqa: SLF001


@dataclass(frozen=True)
class TestEnforcedState(State):
    __test__ = False
    label: str
    sets_state = True
    unsets_state = True
    enforced_state = True


class _FakeBucket:
    is_empty = False


class _FakeDomain:
    def __init__(self, group_buckets):
        self.is_empty = False
        self._vertex_buckets = dict(group_buckets)

    def get_drawable_bucket(self, group):
        return self._vertex_buckets.get(group)

    def has_bucket(self, group):
        return group in self._vertex_buckets

    def bind_vao(self):
        return None

    def draw_buckets(self, _mode_func, _buckets):
        return None


def _get_group_state(group, state_type):
    return next(state for state in group.states if isinstance(state, state_type))


def _build_test_batch(*drawable_groups):
    batch = pyglet.graphics.Batch()
    for group in drawable_groups:
        if group not in batch.group_map:
            batch._add_group(group)  # noqa: SLF001

    domain = _FakeDomain({group: _FakeBucket() for group in drawable_groups})
    key = _DomainKey(indexed=False, instanced=False, mode=GeometryMode.TRIANGLES, attributes="test")
    batch._domain_registry[key] = domain  # noqa: SLF001
    return batch, domain


def _enforced_state_calls(calls):
    transitions = []
    for fn in calls:
        state = getattr(fn, "__self__", None)
        if isinstance(state, TestEnforcedState):
            transitions.append((state.label, fn.__name__))
    return transitions


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
    assert len(group.states) == count
    assert len(group._expanded_states) == expanded_count


def test_group_parent_no_state(test_window):
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


def test_group_parent_with_state(test_window):
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


def test_group_no_parent(test_window):
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

def test_group_ordering(test_window):
    # Make sure groups are ordered by ordering number.
    batch = pyglet.graphics.Batch()

    high_group = pyglet.graphics.Group(order=10)
    low_group = pyglet.graphics.Group(order=-10)

    # Add in reverse order to ensure sorting is applied.
    # Keep in list so no GC.
    sprites = [
        pyglet.sprite.Sprite(test_image, x=0, y=0, batch=batch, group=high_group),
        pyglet.sprite.Sprite(test_image, x=0, y=0, batch=batch, group=low_group)
    ]
    draw_list = batch._create_draw_list()  # noqa: SLF001
    set_groups = [group for (_domain, mode, group) in draw_list if mode == "set"]

    ordered = [group for group in set_groups if group in (low_group, high_group)]
    assert ordered == [low_group, high_group]


def test_group_consolidation(test_window):
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

def test_group_differing_textures(test_window):
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

def test_group_texture_same_region(test_window):
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
    viewport = Viewport(0, 0, 100, 100)

    group1 = pyglet.graphics.Group()
    group1.set_viewport(viewport)
    group1.set_depth_test(CompareOp.EQUAL)

    group2 = pyglet.graphics.Group()
    group2.set_viewport(viewport)
    group2.set_depth_test(CompareOp.EQUAL)

    assert group2 == group1
    assert group2 is not group1

def test_similar_group_equal_comparison_inherit():
    """Same as above, but groups that added their state within the group creation."""
    group1 = GroupWithSimilarState()
    group2 = GroupWithSimilarState()

    assert group2 == group1
    assert group2 is not group1


def test_group_state_cache_is_built_once_on_first_hash(monkeypatch):
    calls = 0
    expand_states = graphics_draw._expand_states_in_order

    def counted_expand_states(states):
        nonlocal calls
        calls += 1
        return expand_states(states)

    monkeypatch.setattr(graphics_draw, "_expand_states_in_order", counted_expand_states)

    group = pyglet.graphics.Group()
    group.set_state(SameState())
    group.set_state(OtherSameState())
    group.set_state(SameState())

    assert calls == 0
    assert group._state_cache_dirty  # noqa: SLF001

    first_hash = hash(group)

    assert calls == 1
    assert not group._state_cache_dirty  # noqa: SLF001
    assert len(group._expanded_states) == 2  # noqa: SLF001
    assert hash(group) == first_hash
    assert calls == 1


def test_group_state_cache_finalizes_at_batch_assignment(test_window):
    group = pyglet.graphics.Group()
    group.set_state(SameState())
    group.set_state(OtherSameState())

    assert group._state_cache_dirty  # noqa: SLF001
    assert group._expanded_states == []  # noqa: SLF001

    batch = pyglet.graphics.Batch()
    batch._add_group(group)  # noqa: SLF001

    assert not group._state_cache_dirty  # noqa: SLF001
    assert len(group._expanded_states) == 2  # noqa: SLF001

    with pytest.raises(AssertionError, match="New states cannot be set once a group is in a batch."):
        group.set_state(SameState())


def test_deferred_cache_matches_eager_reference_representation():
    states = (SameState(), OtherSameState(), SameState())
    eager = EagerReferenceGroup()
    deferred = pyglet.graphics.Group()

    for state in states:
        eager.set_state(state)
        deferred.set_state(state)

    assert hash(deferred) == hash(eager)
    assert deferred._state_names == eager._state_names  # noqa: SLF001
    assert deferred._expanded_states == eager._expanded_states  # noqa: SLF001
    assert deferred._hashable_states == eager._hashable_states  # noqa: SLF001


def test_group_hash_collisions_preserve_consolidation_correctness():
    first = pyglet.graphics.Group()
    first.set_state(CollidingState(1))
    same_as_first = pyglet.graphics.Group()
    same_as_first.set_state(CollidingState(1))
    different = pyglet.graphics.Group()
    different.set_state(CollidingState(2))

    consolidated = dict.fromkeys((first, same_as_first, different))

    assert len(consolidated) == 2
    assert first == same_as_first
    assert first != different


def test_identity_hashed_group_finalizes_when_added_to_batch(test_window):
    group = IdentityHashGroup()
    state = SameState()
    group.set_state(state)

    assert group._state_cache_dirty  # noqa: SLF001

    batch, _domain = _build_test_batch(group)
    draw_list = batch._create_draw_list()  # noqa: SLF001
    optimized = batch._optimize_draw_list(draw_list)  # noqa: SLF001

    assert not group._state_cache_dirty  # noqa: SLF001
    assert state.set_state in optimized


def test_identity_hashed_parent_finalizes_when_added_recursively(test_window):
    parent = IdentityHashGroup()
    parent.set_state(SameState())
    child = pyglet.graphics.Group(parent=parent)

    _build_test_batch(child)

    assert not parent._state_cache_dirty  # noqa: SLF001
    assert len(parent._expanded_states) == 1  # noqa: SLF001


def test_direct_group_render_finalizes_state_cache():
    group = pyglet.graphics.Group()
    group.set_state(SameState())

    group.set_state_all(None)

    assert not group._state_cache_dirty  # noqa: SLF001
    assert len(group._expanded_states) == 1  # noqa: SLF001


def test_draw_list_optimizer_does_not_copy_list_tails(test_window):
    class NoSliceList(list):
        def __getitem__(self, item):
            if isinstance(item, slice):
                raise AssertionError("Draw-list tail was copied")
            return super().__getitem__(item)

    first = pyglet.graphics.Group()
    first.set_state(CollidingState(1))
    second = pyglet.graphics.Group()
    second.set_state(CollidingState(2))
    batch, _domain = _build_test_batch(first, second)
    draw_list = NoSliceList(batch._create_draw_list())  # noqa: SLF001

    optimized = batch._optimize_draw_list(draw_list)  # noqa: SLF001

    assert optimized


def test_different_group_equal_add_comparison():
    """Ensure groups that are different will not equal each other or rendering may break."""
    group1 = pyglet.graphics.Group()
    group1.set_viewport(Viewport(0, 0, 200, 200))

    group2 = pyglet.graphics.Group()
    group2.set_viewport(Viewport(0, 0, 100, 100))

    assert group2 != group1
    assert group2 is not group1

def test_group_viewport_state_uses_mutable_provider():
    """Ensure viewport state reads updated values from its provider."""
    viewport = Viewport(0, 0, 100, 100)
    group = pyglet.graphics.Group()
    group.set_viewport(viewport)

    state = group.states[0]
    group_hash = hash(group)
    state_hash = hash(state)
    assert state.area == (0, 0, 100, 100)

    viewport.set(12, 24, 320, 180)

    assert hash(group) == group_hash
    assert hash(state) == state_hash
    assert state.area == (12, 24, 320, 180)
    assert (state.x, state.y, state.width, state.height) == (12, 24, 320, 180)

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
    group1.set_state(custom_state)

    other_custom_state = MyState()
    group2 = pyglet.graphics.Group()
    group2.set_state(other_custom_state)

    assert group2 == group1
    assert group2 is not group1


def test_group_shader_uniforms_snapshot_after_batching(test_window) -> None:
    """Changing the state after the group exists in a batch will make the hash unstable."""
    batch = pyglet.graphics.Batch()
    group = pyglet.graphics.Group()
    program = object()
    uniforms = {"model": "initial"}

    group.set_shader_uniforms(program, uniforms)
    batch._add_group(group)  # noqa: SLF001

    with pytest.raises(AssertionError, match="New states cannot be set once a group is in a batch."):
        group.set_shader_uniforms(program, {"model": "updated"})


def test_enforced_state_inheritance_is_static_after_child_creation():
    root = pyglet.graphics.Group()
    root.set_state(TestEnforcedState("root_v1"))

    child = pyglet.graphics.Group(parent=root)
    assert _get_group_state(child, TestEnforcedState).label == "root_v1"

    root.set_state(TestEnforcedState("root_v2"))
    late_child = pyglet.graphics.Group(parent=root)

    assert _get_group_state(root, TestEnforcedState).label == "root_v2"
    assert _get_group_state(child, TestEnforcedState).label == "root_v1"
    assert _get_group_state(late_child, TestEnforcedState).label == "root_v2"


def test_enforced_state_child_override_does_not_affect_siblings():
    root = pyglet.graphics.Group()
    root.set_state(TestEnforcedState("root"))

    sibling_a = pyglet.graphics.Group(parent=root)
    override_child = pyglet.graphics.Group(parent=root)
    override_child.set_state(TestEnforcedState("override"))
    sibling_b = pyglet.graphics.Group(parent=root)
    override_grandchild = pyglet.graphics.Group(parent=override_child)

    assert _get_group_state(sibling_a, TestEnforcedState).label == "root"
    assert _get_group_state(sibling_b, TestEnforcedState).label == "root"
    assert _get_group_state(override_child, TestEnforcedState).label == "override"
    assert _get_group_state(override_grandchild, TestEnforcedState).label == "override"


def test_enforced_state_draw_list_reapplies_parent_after_override(test_window):
    root_group = pyglet.graphics.Group()
    root_group.set_state(TestEnforcedState("root"))

    outer_group = pyglet.graphics.Group(parent=root_group)
    outer_group.set_state(TestEnforcedState("outer"))
    sibling_group = pyglet.graphics.Group(parent=root_group)

    batch, domain = _build_test_batch(outer_group, sibling_group)
    draw_list = batch._create_draw_list()  # noqa: SLF001

    assert draw_list == [
        (None, "set", root_group),
        (None, "set", outer_group),
        (domain, GeometryMode.TRIANGLES, outer_group),
        (None, "unset", outer_group),
        (None, "set", sibling_group),
        (domain, GeometryMode.TRIANGLES, sibling_group),
        (None, "unset", sibling_group),
        (None, "unset", root_group),
    ]

    optimized = batch._optimize_draw_list(draw_list)  # noqa: SLF001
    assert _enforced_state_calls(optimized) == [
        ("root", "set_state"),
        ("root", "unset_state"),
        ("outer", "set_state"),
        ("outer", "unset_state"),
        ("root", "set_state"),
        ("root", "unset_state"),
    ]

    function_names = [func.__name__ for func in optimized]
    assert function_names.count("_bind_vao") == 1
    assert function_names.count("_draw") == 2


def test_enforced_state_optimizer_keeps_shared_parent_state_active(test_window):
    root_group = pyglet.graphics.Group()
    root_group.set_state(TestEnforcedState("root"))

    left_child = pyglet.graphics.Group(parent=root_group)
    right_child = pyglet.graphics.Group(parent=root_group)
    left_child.add_comparison("left")
    right_child.add_comparison("right")

    batch, domain = _build_test_batch(left_child, right_child)
    draw_list = batch._create_draw_list()  # noqa: SLF001

    assert draw_list == [
        (None, "set", root_group),
        (None, "set", left_child),
        (domain, GeometryMode.TRIANGLES, left_child),
        (None, "unset", left_child),
        (None, "set", right_child),
        (domain, GeometryMode.TRIANGLES, right_child),
        (None, "unset", right_child),
        (None, "unset", root_group),
    ]

    optimized = batch._optimize_draw_list(draw_list)  # noqa: SLF001
    assert _enforced_state_calls(optimized) == [
        ("root", "set_state"),
        ("root", "unset_state"),
    ]

    function_names = [func.__name__ for func in optimized]
    assert function_names.count("_bind_vao") == 1
    assert function_names.count("_draw") == 1


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

def test_single_group_deletion(test_window):
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


def test_group_persistence_deletion(test_window):
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
