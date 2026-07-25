from __future__ import annotations

import weakref
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Sequence

if TYPE_CHECKING:
    from pyglet.graphics.vertexdomain import InstanceStream, VertexArrayBinding, InstanceVertexList, InstanceIndexedVertexList
    from _weakref import ReferenceType
    from pyglet.customtypes import DataTypes


class InstanceAllocator:
    """Allocator for instances within a bucket."""
    count: int
    slot_to_handle: dict[int, VertexInstance]
    inst_to_slot: dict[VertexInstance, int]

    def __init__(self) -> None:  # noqa: D107
        self.count = 0
        self.inst_to_slot = {}
        self.slot_to_inst = {}

    def clear(self) -> None:
        self.inst_to_slot.clear()
        self.slot_to_inst.clear()
        self.count = 0

    def add(self, inst: VertexInstance) -> int:
        slot = self.count
        self.count += 1
        self.inst_to_slot[inst] = slot
        self.slot_to_inst[slot] = inst
        return slot

    def remove(self, inst: VertexInstance) -> tuple[int, int, VertexInstance] | None:
        slot = self.inst_to_slot.pop(inst)
        last = self.count - 1
        if slot != last:
            moved = self.slot_to_inst[last]
            self.slot_to_inst[slot] = moved
            self.inst_to_slot[moved] = slot
            self.slot_to_inst.pop(last, None)
            self.count -= 1
            return slot, last, moved

        self.slot_to_inst.pop(last, None)
        self.count -= 1
        return None

class VertexInstance:
    """Base class for VertexInstance instances."""
    _bucket_ref: ReferenceType[InstanceBucket]
    slot: int

    __slots__ = ("_bucket_ref", "slot")

    def __init__(self, bucket_ref: ReferenceType[InstanceBucket], slot: int = -1) -> None:  # noqa: D107
        self._bucket_ref = bucket_ref
        self.slot = slot

    @property
    def bucket(self) -> InstanceBucket:
        b = self._bucket_ref()
        if b is None:
            raise RuntimeError("Bucket no longer exists")
        return b

    def set(self, **attrs: Any) -> None:
        """Partial row update (by attribute name)."""
        self.bucket.stream.set_region(self.slot, 1, attrs)

    def get(self, name: str) -> list[int]:
        return self.bucket.stream.attrib_name_buffers[name].get_region(self.slot, 1)

    def delete(self) -> None:
        self.bucket.delete_instance(self)
        self.slot = -1

def _make_inst_attr_prop(attr_name: str):
    def _get(self):
        buf = self.bucket.stream.attrib_name_buffers[attr_name]
        return buf.get_region(self.slot, 1)

    def _set(self, data):
        buf = self.bucket.stream.attrib_name_buffers[attr_name]
        buf.set_region(self.slot, 1, data)

    return property(_get, _set)

class InstanceBucket:
    """Manages the relationship between the instance buffer data and the instance objects."""
    def __init__(self, instance_stream: InstanceStream, vao: VertexArrayBinding) -> None:
        self.stream = instance_stream
        self.vao = vao
        self.allocator = InstanceAllocator()

        # Build a VertexInstance class with properties for each instanced attribute:
        props = {name: _make_inst_attr_prop(name) for name in self.stream.attrib_name_buffers.keys()}
        props["__slots__"] = ("_bucket_ref", "slot")
        self._InstanceCls = type("VertexInstance", (VertexInstance,), props)

    def create_instance(self, **attributes: Any) -> VertexInstance:
        v_instance = self._InstanceCls(weakref.ref(self), slot=-1)
        slot = self.allocator.add(v_instance)
        v_instance.slot = slot

        # Still need to allocate the stream to allow expanding buffers.
        self.stream.alloc(1)
        if attributes:
            self.stream.set_region(slot, 1, attributes)
        return v_instance

    def get_instance_by_index(self, index: int) -> VertexInstance | None:
        """Return the instance currently stored at ``index`` or ``None``."""
        return self.allocator.slot_to_inst.get(index)

    def get_instance_index(self, instance: VertexInstance) -> int | None:
        """Return the active slot index for ``instance`` or ``None``."""
        return self.allocator.inst_to_slot.get(instance)

    def _get_required_slot(self, instance: VertexInstance) -> int:
        slot = self.allocator.inst_to_slot.get(instance)
        if slot is None:
            msg = "Instance does not belong to this vertex list."
            raise ValueError(msg)
        return slot

    def _swap_slots(self, first_slot: int, second_slot: int) -> None:
        if first_slot == second_slot:
            return

        first_instance = self.allocator.slot_to_inst[first_slot]
        second_instance = self.allocator.slot_to_inst[second_slot]

        for buffer in self.stream.attrib_name_buffers.values():
            # Tuple to make a copy otherwise it's the actual memory.
            first_data = tuple(buffer.get_region(first_slot, 1))
            second_data = tuple(buffer.get_region(second_slot, 1))
            buffer.set_region(first_slot, 1, second_data)
            buffer.set_region(second_slot, 1, first_data)

        self.allocator.slot_to_inst[first_slot] = second_instance
        self.allocator.slot_to_inst[second_slot] = first_instance
        self.allocator.inst_to_slot[first_instance] = second_slot
        self.allocator.inst_to_slot[second_instance] = first_slot
        first_instance.slot = second_slot
        second_instance.slot = first_slot

    def swap_instances(self, first: VertexInstance, second: VertexInstance) -> None:
        """Swap two instances in-place.

        This operation updates per-instance attribute rows for both slots.

        Args:
            first:
                The first instance to swap.
            second:
                The second instance to swap.
        """
        first_slot = self._get_required_slot(first)
        second_slot = self._get_required_slot(second)
        self._swap_slots(first_slot, second_slot)

    def move_instance_to_index(self, instance: VertexInstance, index: int) -> None:
        """Move ``instance`` to an absolute slot index.

        The moved instance ends up at ``index``. Other instances shift to keep
        a contiguous slot layout.
        This may be expensive when moving across many slots.

        Args:
            instance:
                The instance to move.
            index:
                Target slot index in ``[0, instance_count - 1]``.
        """
        count = self.instance_count
        if index < 0 or index >= count:
            msg = f"Index out of range: {index} (instance_count={count})"
            raise IndexError(msg)

        current_slot = self._get_required_slot(instance)
        if current_slot == index:
            return

        if current_slot > index:
            for slot in range(current_slot, index, -1):
                self._swap_slots(slot, slot - 1)
        else:
            for slot in range(current_slot, index):
                self._swap_slots(slot, slot + 1)

    def set_instance_order(self, order: Sequence[VertexInstance]) -> None:
        """Set the exact full order of all active instances.

        This can be expensive for large lists because many slot swaps may be
        required.

        Args:
            order:
                Sequence containing every active instance exactly once.
        """
        count = self.instance_count
        if len(order) != count:
            msg = f"Order length mismatch. Expected {count}, got {len(order)}."
            raise ValueError(msg)

        if len(set(order)) != count:
            msg = "Order contains duplicate instances."
            raise ValueError(msg)

        active = set(self.allocator.inst_to_slot.keys())
        requested = set(order)
        if requested != active:
            msg = "Order must contain every active instance exactly once."
            raise ValueError(msg)

        for target_slot, instance in enumerate(order):
            current_slot = self.allocator.inst_to_slot[instance]
            if current_slot != target_slot:
                self._swap_slots(current_slot, target_slot)

    def move_to_back(self, instances: Sequence[VertexInstance]) -> None:
        """Move the provided instances to the back in the given order.

        "Back" means lower indices (drawn earlier). Instances not listed remain
        after the moved prefix, preserving their relative order.
        This may be expensive when moving many instances.

        Args:
            instances:
                Instances to move to back slots ``[0..len(instances)-1]``.
        """
        if len(set(instances)) != len(instances):
            msg = "Instances to move contain duplicates."
            raise ValueError(msg)

        for instance in instances:
            self._get_required_slot(instance)

        for target_slot, instance in enumerate(instances):
            self.move_instance_to_index(instance, target_slot)

    def move_to_top(self, instances: Sequence[VertexInstance]) -> None:
        """Move the provided instances to the top in the given order.

        "Top" means higher indices (drawn later). Instances not listed remain
        before the moved suffix, preserving their relative order.
        This may be expensive when moving many instances.

        Args:
            instances:
                Instances to move to the ending slots in the given order.
        """
        if len(set(instances)) != len(instances):
            msg = "Instances to move contain duplicates."
            raise ValueError(msg)

        for instance in instances:
            self._get_required_slot(instance)

        top_start = self.instance_count - len(instances)
        for offset in range(len(instances) - 1, -1, -1):
            self.move_instance_to_index(instances[offset], top_start + offset)

    def delete_instance(self, vi: VertexInstance) -> None:
        # When removing an instance, take the last slot and move to the removed slot to maintain contiguous allocation.
        swap = self.allocator.remove(vi)
        if swap:
            dst, src, moved = swap
            self.stream.copy_data(dst, self.stream, src, count=1)
            moved.slot = dst

    @property
    def instance_count(self) -> int:
        return self.allocator.count

class InstanceDomain(ABC):
    """Base class for managing instance domains and the buckets associated with each."""
    _geom: dict[InstanceBucket, tuple[Any, ...]]
    _buckets: dict[tuple, InstanceBucket]

    def __init__(self, domain: Any, initial_instances: int) -> None:
        self._domain = weakref.proxy(domain)
        self._initial = initial_instances
        self._buckets = {}
        self._geom = {}

    def move_all(self, src_bucket: InstanceBucket, dst_bucket: InstanceBucket) -> None:
        assert src_bucket in self._buckets.values(), "Bucket does not belong to this instance domain."
        if dst_bucket is src_bucket:
            return
        n = src_bucket.allocator.count
        if n == 0:
            # Nothing to move.
            return

        handles = [src_bucket.allocator.slot_to_inst[i] for i in range(n)]
        start_dst = dst_bucket.allocator.count
        for i, h in enumerate(handles):
            dst_bucket.allocator.add(h)
            h._bucket_ref = weakref.ref(dst_bucket)
            h.slot = start_dst + i

        dst_bucket.stream.alloc(n)
        src_bucket.stream.copy_data(dst_slot=start_dst, dst_stream=dst_bucket.stream, src_slot=0, count=n)

        src_bucket.allocator.clear()

    def get_arrays_bucket(self, *, mode: int, first_vertex: int, vertex_count: int) -> InstanceBucket:
        key = ("arrays", mode, first_vertex, vertex_count)
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = self._create_bucket_arrays()
            self._buckets[key] = bucket
            self._geom[bucket] = (first_vertex, vertex_count)
        return bucket

    def get_elements_bucket(self, *, mode: int,
                            first_index: int, index_count: int,
                            index_type: DataTypes, base_vertex: int = 0) -> InstanceBucket:
        key = ("elements", mode, first_index, index_count, index_type, base_vertex)
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = self._create_bucket_elements()
            self._buckets[key] = bucket
            self._geom[bucket] = (first_index, index_count, index_type, base_vertex)
        return bucket

    @abstractmethod
    def _create_bucket_arrays(self) -> InstanceBucket: ...
    @abstractmethod
    def _create_bucket_elements(self) -> InstanceBucket: ...
    @abstractmethod
    def draw(self, mode: Any) -> None: ...
    @abstractmethod
    def draw_subset(self, mode: Any, vertex_list: InstanceVertexList | InstanceIndexedVertexList) -> None: ...
