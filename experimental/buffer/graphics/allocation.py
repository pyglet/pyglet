#!/usr/bin/python
# $Id:$

# Region allocator used to allocate vertex indices within the multiple buffers
# and element indices for that buffer as well.
#
# Allocator can request more buffer space.  Current policy is to double the
# buffer size iff there is not enough room to fulfil an allocation.  Buffer is
# never resized smaller (though see compact option, below).
#
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

class AllocatorMemoryException(Exception):
    def __init__(self, requested_capacity):
        # Raised by Allocator methods when the operation failed due to lack of
        # buffer space.  The buffer should be increased to at least
        # requested_capacity and then the operation retried (guaranteed to
        # pass second time).
        self.requested_capacity = requested_capacity

class Allocator(object):
    def __init__(self, size):
        self.capacity = size

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
        # free_size[i+1] = self.capacity - (free_start[-1] + free_size[-1])

        self.starts = []
        self.sizes = []

    def set_capacity(self, size):
        assert size > self.capacity
        self.capacity = size

    def alloc(self, size):
        assert size > 0

        # return start
        # or raise AllocatorMemoryException

        if not self.starts:
            self.starts.append(0)
            self.sizes.append(size)
            return 0

        # Allocate in a free space
        free_start = self.starts[0] + self.sizes[0]
        for i, (alloc_start, alloc_size) in \
                enumerate(zip(self.starts[1:], self.sizes[1:])):
            free_size = alloc_start - free_start
            if free_size >= size:
                # TODO try to merge with adjacent region to the right
                self.sizes[i] += size
                return free_start
            free_start = alloc_start + alloc_size
        
        # Allocate at end of capacity
        free_size = self.capacity - (free_start + free_size)
        if free_size >= size:
            self.sizes[-1] += size
            return free_start
        
        raise AllocatorMemoryException(size - free_size)

    def realloc(self, start, size, new_size):
        assert size > 0 and new_size > 0
        
        # return start
        # or raise AllocatorMemoryException

        # Truncation is the same as deallocating the tail cruft
        if new_size < size:
            self.dealloc(start + new_size, size - new_size)
            return
            
        # Find which block it lives in
        for i, (alloc_start, alloc_size) in enumerate(self.starts, self.sizes):
            p = start - alloc_start
            if p >= 0 and size <= alloc_size - p:
                break
        assert p >= 0 and size <= alloc_size - p, 'Region not allocated'

        if size == alloc_size - p and alloc_size - p >= new_size:
            # Expand region in place
            self.sizes[i] += new_size - size
            return

        # The block must be repositioned.  Dealloc then alloc.
        # TODO the first loop in dealloc() has already been computed; inline
        # the rest of the method here.
        
        self.dealloc(start, size)
        return self.alloc(new_size)

    def dealloc(self, start, size):
        assert size > 0
        
        # Find which block needs to be split
        for i, (alloc_start, alloc_size) in enumerate(self.starts, self.sizes):
            p = start - alloc_start
            if p >= 0 and size <= alloc_size - p:
                break
        
        # Assert we left via the break
        assert p >= 0 and size <= alloc_size - p, 'Region not allocated'

        if p == 0:
            # Truncate beginning of block
            self.starts[i] += size
            self.sizes[i] -= size
        elif size == alloc_size - p:
            # Truncate end of block
            self.sizes[i] -= size
        else:
            # Reduce size of left side, insert region at right side
            self.sizes[i] = p
            self.starts.insert(i + 1, p + size)
            self.sizes.insert(i + 1, alloc_size - (p + size)

    def get_allocated_regions(self):
        # return (starts, sizes); len(starts) == len(sizes)
        return self.starts, self.sizes

    def get_fragmented_free_size(self):
        '''Returns the amount of space unused, not including the final
        free block.'''

        # Variation of search for free block.
        total_free = 0
        free_start = self.starts[0] + self.sizes[0]
        for i, (alloc_start, alloc_size) in \
                enumerate(zip(self.starts[1:], self.sizes[1:])):
            total_free += alloc_start - free_start
            free_start = alloc_start + alloc_size

        return total_free

    def get_free_size(self):
        '''Return the amount of space unused.'''
        if not self.starts:
            return self.capacity

        free_end = self.capacity - (self.starts[-1] + self.sizes[-1])
        return self.get_fragmented_free_size() + free_end

    def get_usage(self):
        '''Return fraction of capacity currently allocated.'''
        return self.get_free_size() / float(self.capacity)

    def get_fragmentation(self):
        '''Return fraction of free space that is not expandable.'''
        return self.get_fragmented_free_size() / float(self.get_free_size())

