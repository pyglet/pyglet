"""Memory allocation algorithm for vertex arrays and buffers.

The region allocator is used to allocate vertex indices within a vertex
domain's  multiple buffers.  ("Buffer" refers to any abstract buffer presented
by :py:mod:`pyglet.graphics.vertexbuffer`.

The allocator will at times request more space from the buffers. The current
policy is to double the buffer size when there is not enough room to fulfil an
allocation.  The buffer is never resized smaller.

The allocator maintains references to free space only; it is the caller's
responsibility to maintain the allocated regions.
"""

# Common cases:
# -regions will be the same size (instances of same object, e.g. sprites)
# -regions will not usually be resized (only exception is text)
# -alignment of 4 vertices (glyphs, sprites, images, ...)
#
# Optimise for:
# -keeping regions adjacent, reduce the number of entries in glMultiDrawArrays
# -finding large blocks of allocated regions quickly (for drawing)
# -finding block of unallocated space is the _uncommon_ case!
#
# Decisions:
# -don't over-allocate regions to any alignment -- this would require more
#  work in finding the allocated spaces (for drawing) and would result in
#  more entries in glMultiDrawArrays
# -don't move blocks when they truncate themselves.  try not to allocate the
#  space they freed too soon (they will likely need grow back into it later,
#  and growing will usually require a reallocation).
# -allocator does not track individual allocated regions.  Trusts caller
#  to provide accurate (start, size) tuple, which completely describes
#  a region from the allocator's point of view.
# -this means that compacting is probably not feasible, or would be hideously
#  expensive
from __future__ import annotations


class AllocatorMemoryException(Exception):  # noqa: N818
    """The buffer is not large enough to fulfil an allocation.

    Raised by `Allocator` methods when the operation failed due to
    lack of buffer space.  The buffer should be increased to at least
    requested_capacity and then the operation retried (guaranteed to
    pass second time).
    """

    def __init__(self, requested_capacity: int) -> None:
        """Requested capacity failed to allocate."""
        self.requested_capacity = requested_capacity


class Allocator:
    """Buffer space allocation implementation."""
    sizes: list[int]
    starts: list[int]

    __slots__ = 'capacity', 'starts', 'sizes'

    def __init__(self, capacity: int) -> None:
        """Create an allocator for a buffer of the specified maximum capacity size."""
        self.capacity = capacity

        # Allocated blocks.  Start index and size in parallel lists.
        #
        # # = allocated, - = free
        #
        #  0  3 5        15   20  24                    40
        # |###--##########-----####----------------------|
        #
        # starts = [0, 5, 20]
        # sizes = [3, 10, 4]
        #
        # To calculate free blocks:
        # for i in range(0, len(starts)):
        #   free_start[i] = starts[i] + sizes[i]
        #   free_size[i] =  starts[i+1] - free_start[i]
        # free_size[i+1] = self.capacity - free_start[-1]

        self.starts = []
        self.sizes = []

    def set_capacity(self, size: int) -> None:
        """Resize the maximum buffer size.

        The capacity cannot be reduced.
        """
        assert size > self.capacity
        self.capacity = size

    def alloc(self, size: int) -> int:
        """Allocate memory in the buffer.

        Raises `AllocatorMemoryException` if the allocation cannot be
        fulfilled.

        Args:
            size:
                Size of region to allocate.

        Returns:
            Starting index of the allocated region.
        """
        assert size >= 0

        if size == 0:
            return 0

        # Return start, or raise AllocatorMemoryException
        if not self.starts:
            if size <= self.capacity:
                self.starts.append(0)
                self.sizes.append(size)
                return 0

            raise AllocatorMemoryException(size)

        # Restart from zero if space exists
        if self.starts[0] > size:
            self.starts.insert(0, 0)
            self.sizes.insert(0, size)
            return 0

        # Allocate in a free space
        free_start = self.starts[0] + self.sizes[0]
        for i, (alloc_start, alloc_size) in enumerate(zip(self.starts[1:], self.sizes[1:])):
            # Danger!
            # i is actually index - 1 because of slicing above...
            # starts[i]   points to the block before this free space
            # starts[i+1] points to the block after this free space, and is always valid.
            free_size = alloc_start - free_start
            if free_size == size:
                # Merge previous block with this one (removing this free space)
                self.sizes[i] += free_size + alloc_size
                del self.starts[i + 1]
                del self.sizes[i + 1]
                return free_start
            elif free_size > size:  # noqa: RET505
                # Increase size of previous block to intrude into this free
                # space.
                self.sizes[i] += size
                return free_start
            free_start = alloc_start + alloc_size

        # Allocate at end of capacity
        free_size = self.capacity - free_start
        if free_size >= size:
            self.sizes[-1] += size
            return free_start

        raise AllocatorMemoryException(self.capacity + size - free_size)

    def realloc(self, start: int, size: int, new_size: int) -> int:
        """Reallocate a region of the buffer.

        This is more efficient than separate `dealloc` and `alloc` calls, as
        the region can often be resized in-place.

        Raises `AllocatorMemoryException` if the allocation cannot be
        fulfilled.

        Args:
            start:
                Current starting index of the region.
            size:
                Current size of the region.
            new_size: int
                New size of the region.

        Returns:
            Starting index of the re-allocated region.
        """
        assert size >= 0 and new_size >= 0  # noqa: PT018

        if new_size == 0:
            if size != 0:
                self.dealloc(start, size)
            return 0
        if size == 0:
            return self.alloc(new_size)

        # return start, or raise AllocatorMemoryException

        # Truncation is the same as deallocating the tail cruft
        if new_size < size:
            self.dealloc(start + new_size, size - new_size)
            return start

        # Find which block it lives in
        for i, (alloc_start, alloc_size) in enumerate(zip(*(self.starts, self.sizes))):
            p = start - alloc_start
            if p >= 0 and size <= alloc_size - p:
                break
        if not (p >= 0 and size <= alloc_size - p):
            print(list(zip(self.starts, self.sizes)))
            print(start, size, new_size)
            print(p, alloc_start, alloc_size)
        assert p >= 0 and size <= alloc_size - p, 'Region not allocated'  # noqa: PT018

        if size == alloc_size - p:
            # Region is at end of block. Find how much free space is after it.
            is_final_block = i == len(self.starts) - 1
            if not is_final_block:
                free_size = self.starts[i + 1] - (start + size)
            else:
                free_size = self.capacity - (start + size)

            # TODO If region is an entire block being an island in free space,
            # can possibly extend in both directions.

            if free_size == new_size - size and not is_final_block:
                # Merge block with next (region is expanded in place to
                # exactly fill the free space)
                self.sizes[i] += free_size + self.sizes[i + 1]
                del self.starts[i + 1]
                del self.sizes[i + 1]
                return start

            if free_size > new_size - size:
                # Expand region in place
                self.sizes[i] += new_size - size
                return start

        # The block must be repositioned.  Dealloc then alloc.

        # But don't do this!  If alloc fails, we've already silently dealloc'd
        # the original block.
        #   self.dealloc(start, size)
        #   return self.alloc(new_size)

        # It must be alloc'd first.  We're not missing an optimisation
        # here, because if freeing the block would've allowed for the block to
        # be placed in the resulting free space, one of the above in-place
        # checks would've found it.
        result = self.alloc(new_size)
        self.dealloc(start, size)
        return result

    def dealloc(self, start: int, size: int) -> None:
        """Free a region of the buffer.

        Args:
            start:
                Starting index of the region.
            size:
                Size of the region.

        """
        assert size >= 0

        if size == 0:
            return

        assert self.starts

        # Find which block needs to be split
        for i, (alloc_start, alloc_size) in enumerate(zip(*(self.starts, self.sizes))):
            p = start - alloc_start
            if p >= 0 and size <= alloc_size - p:
                break

        # Assert we left via the break
        assert p >= 0 and size <= alloc_size - p, 'Region not allocated'  # noqa: PT018

        if p == 0 and size == alloc_size:
            # Remove entire block
            del self.starts[i]
            del self.sizes[i]
        elif p == 0:
            # Truncate beginning of block
            self.starts[i] += size
            self.sizes[i] -= size
        elif size == alloc_size - p:
            # Truncate end of block
            self.sizes[i] -= size
        else:
            # Reduce size of left side, insert block at right side
            #   $ = dealloc'd block, # = alloc'd region from same block
            #
            #   <------8------>
            #   <-5-><-6-><-7->
            #   1    2    3    4
            #   #####$$$$$#####
            #
            #   1 = alloc_start
            #   2 = start
            #   3 = start + size
            #   4 = alloc_start + alloc_size
            #   5 = start - alloc_start = p
            #   6 = size
            #   7 = {8} - ({5} + {6}) = alloc_size - (p + size)
            #   8 = alloc_size
            #
            self.sizes[i] = p
            self.starts.insert(i + 1, start + size)
            self.sizes.insert(i + 1, alloc_size - (p + size))

    def get_allocated_regions(self) -> tuple[list, list]:
        """Get a list of (aggregate) allocated regions.

        The result of this method is ``(starts, sizes)``, where ``starts`` is
        a list of starting indices of the regions and ``sizes`` their
        corresponding lengths.
        """
        return self.starts, self.sizes

    def get_fragmented_free_size(self) -> int:
        """Returns the amount of space unused, not including the final free block."""
        if not self.starts:
            return 0

        # Variation of search for free block.
        total_free = 0
        free_start = self.starts[0] + self.sizes[0]
        for i, (alloc_start, alloc_size) in enumerate(zip(self.starts[1:], self.sizes[1:])):
            total_free += alloc_start - free_start
            free_start = alloc_start + alloc_size

        return total_free

    def get_free_size(self) -> int:
        """Return the amount of space unused."""
        if not self.starts:
            return self.capacity

        free_end = self.capacity - (self.starts[-1] + self.sizes[-1])
        return self.get_fragmented_free_size() + free_end

    def get_usage(self) -> float:
        """Return fraction of capacity currently allocated."""
        return 1. - self.get_free_size() / float(self.capacity)

    def get_fragmentation(self) -> float:
        """Return fraction of free space that is not expandable."""
        free_size = self.get_free_size()
        if free_size == 0:
            return 0.
        return self.get_fragmented_free_size() / float(self.get_free_size())

    def __str__(self) -> str:
        return 'allocs=' + repr(list(zip(self.starts, self.sizes)))

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} {self!s}>'
