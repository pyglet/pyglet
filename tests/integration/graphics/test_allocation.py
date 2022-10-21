import random

from pyglet.graphics import allocation


class Region:
    def __init__(self, start, size):
        self.start = start
        self.size = size

    @property
    def end(self):
        return self.start + self.size

    def __repr__(self):
        return 'Region(%r, %r)' % (self.start, self.size)


class RegionAllocator:
    def __init__(self, capacity):
        self.allocator = allocation.Allocator(capacity)
        self.regions = []

    @property
    def capacity(self):
        return self.allocator.capacity

    def check_region(self, region):
        for other in self.regions:
            if other is region:
                continue

            if (other.start < region.start < other.end) or (other.start < region.end < other.end):
                raise Exception('%r overlaps with %r' % (region, other))

    def check_coverage(self):
        starts, sizes = self.allocator.get_allocated_regions()

        if len(starts) != len(sizes):
            raise Exception('Length of starts (%d) does not match sizes (%d)' % (len(starts), len(sizes)))

        if not starts and not self.regions:
            return

        self.regions.sort(key=lambda r: r.start)
        regions = iter(self.regions)

        blocks = iter(zip(starts, sizes))
        block_start, block_size = next(blocks)
        block_used = False
        try:
            while True:
                region = next(regions)
                block_used = True
                if region.start < block_start:
                    raise Exception(f'Start of {region!r} was not covered at {block_start}')
                # elif region.start > block_start:
                #     raise Exception(f'Uncovered block from {block_start} to {region!r}')
                block_start += region.size
                block_size -= region.size
                if block_size < 0:
                    raise Exception('%r extended past end of block by %d' % (region, -block_size))
                elif block_size == 0:
                    block_start, block_size = next(blocks)
                    block_used = False
        except StopIteration:
            pass

        if not block_used:
            raise Exception(f'Uncovered block(s) from {block_start}')

        try:
            block_start, block_size = next(blocks)
            raise Exception(f'Uncovered block(s) from {block_start}')
        except StopIteration:
            pass

        try:
            region = next(regions)
            raise Exception(f'{region!r} was not covered')
        except StopIteration:
            pass

    def check_redundancy(self):
        # Ensure there are no adjacent blocks (they should have been merged)
        starts, sizes = self.allocator.get_allocated_regions()

        last = -1
        for start, size in zip(starts, sizes):
            if start < last:
                raise Exception(f'Block at {start} is out of order')
            if start == last:
                raise Exception(f'Block at {start} is redundant')
            last = start + size

    def alloc(self, size):
        start = self.allocator.alloc(size)
        region = Region(start, size)
        self.check_region(region)
        self.regions.append(region)
        self.check_coverage()
        self.check_redundancy()
        return region

    def dealloc(self, region):
        assert region in self.regions
        self.allocator.dealloc(region.start, region.size)
        self.regions.remove(region)
        self.check_coverage()
        self.check_redundancy()

    def realloc(self, region, size):
        assert region in self.regions
        region.start = self.allocator.realloc(region.start, region.size, size)
        region.size = size
        self.check_region(region)
        self.check_coverage()
        self.check_redundancy()

    def force_alloc(self, size):
        try:
            return self.alloc(size)
        except allocation.AllocatorMemoryException as e:
            self.allocator.set_capacity(e.requested_capacity)
            return self.alloc(size)

    def force_realloc(self, region, size):
        try:
            self.realloc(region, size)
        except allocation.AllocatorMemoryException as e:
            self.allocator.set_capacity(e.requested_capacity)
            self.realloc(region, size)

    def get_free_size(self):
        return self.allocator.get_free_size()


def test_alloc1():
    capacity = 10
    allocator = RegionAllocator(capacity)
    for i in range(capacity):
        allocator.alloc(1)


def test_alloc2():
    capacity = 10
    allocator = RegionAllocator(capacity)
    for i in range(capacity // 2):
        allocator.alloc(2)


def test_alloc3():
    capacity = 10
    allocator = RegionAllocator(capacity)
    for i in range(capacity // 3):
        allocator.alloc(3)


def test_alloc_mix1_2():
    allocs = [1, 2] * 5
    capacity = sum(allocs)
    allocator = RegionAllocator(capacity)
    for alloc in allocs:
        allocator.alloc(alloc)


def test_alloc_mix5_3_7():
    allocs = [5, 3, 7] * 5
    capacity = sum(allocs)
    allocator = RegionAllocator(capacity)
    for alloc in allocs:
        allocator.alloc(alloc)


def test_dealloc_1_order_all():
    capacity = 10
    allocator = RegionAllocator(capacity)
    regions = []
    for i in range(capacity):
        regions.append(allocator.alloc(1))
    for region in regions:
        allocator.dealloc(region)
    assert allocator.get_free_size() == allocator.capacity


def test_dealloc_1_order():
    capacity = 15
    allocator = RegionAllocator(capacity)
    regions = []
    for i in range(10):
        regions.append(allocator.alloc(1))
    for region in regions:
        allocator.dealloc(region)


def test_dealloc_1_reverse_all():
    capacity = 10
    allocator = RegionAllocator(capacity)
    regions = []
    for i in range(capacity):
        regions.append(allocator.alloc(1))
    for region in regions[::-1]:
        allocator.dealloc(region)
    assert allocator.get_free_size() == allocator.capacity


def test_dealloc_1_reverse():
    capacity = 15
    allocator = RegionAllocator(capacity)
    regions = []
    for i in range(10):
        regions.append(allocator.alloc(1))
    for region in regions[::-1]:
        allocator.dealloc(region)


def test_dealloc_mix1_2_order():
    allocs = [1, 2] * 5
    capacity = sum(allocs)
    allocator = RegionAllocator(capacity)
    regions = []
    for alloc in allocs:
        regions.append(allocator.alloc(alloc))
    for region in regions:
        allocator.dealloc(region)
    assert allocator.get_free_size() == allocator.capacity


def test_dealloc_mix5_3_7_order():
    allocs = [5, 3, 7] * 5
    capacity = sum(allocs)
    allocator = RegionAllocator(capacity)
    regions = []
    for alloc in allocs:
        regions.append(allocator.alloc(alloc))
    for region in regions:
        allocator.dealloc(region)
    assert allocator.get_free_size() == allocator.capacity


def test_dealloc_1_outoforder():
    random.seed(1)
    capacity = 15
    allocator = RegionAllocator(capacity)
    regions = []
    for i in range(capacity):
        regions.append(allocator.alloc(1))
    random.shuffle(regions)
    for region in regions:
        allocator.dealloc(region)
    assert allocator.get_free_size() == allocator.capacity


def test_dealloc_mix1_2_outoforder():
    random.seed(1)
    allocs = [1, 2] * 5
    capacity = sum(allocs)
    allocator = RegionAllocator(capacity)
    regions = []
    for alloc in allocs:
        regions.append(allocator.alloc(alloc))
    random.shuffle(regions)
    for region in regions:
        allocator.dealloc(region)
    assert allocator.get_free_size() == allocator.capacity


def test_dealloc_mix5_3_7_outoforder():
    random.seed(1)
    allocs = [5, 3, 7] * 5
    capacity = sum(allocs)
    allocator = RegionAllocator(capacity)
    regions = []
    for alloc in allocs:
        regions.append(allocator.alloc(alloc))
    random.shuffle(regions)
    for region in regions:
        allocator.dealloc(region)
    assert allocator.get_free_size() == allocator.capacity


def mixed_alloc_dealloc_list(choices, count=10, seed=1):
    random.seed(seed)
    allocs = []
    live = []
    j = 0
    for i in range(count):
        if live:
            if random.random() < .5:
                allocs.append(random.choice(choices))
                live.append(j)
                j += 1
            else:
                k = random.choice(live)
                live.remove(k)
                allocs.append(-k)
        else:
            allocs.append(random.choice(choices))
            live.append(j)
            j += 1
    for j in live:
        allocs.append(-j)
    return allocs


def test_mix_alloc_dealloc1():
    allocs = mixed_alloc_dealloc_list([1])

    capacity = sum([a for a in allocs if a > 0])
    allocator = RegionAllocator(capacity)
    regions = []
    for alloc in allocs:
        if alloc > 0:
            regions.append(allocator.alloc(alloc))
        else:
            region = regions[abs(alloc)]
            allocator.dealloc(region)
    assert allocator.get_free_size() == allocator.capacity


def test_mix_alloc_dealloc5_3_7():
    allocs = mixed_alloc_dealloc_list([5, 3, 7], count=50)

    capacity = sum([a for a in allocs if a > 0])
    allocator = RegionAllocator(capacity)
    regions = []
    for alloc in allocs:
        if alloc > 0:
            regions.append(allocator.alloc(alloc))
        else:
            region = regions[abs(alloc)]
            allocator.dealloc(region)
    assert allocator.get_free_size() == allocator.capacity


def test_realloc1_2():
    allocator = RegionAllocator(30)
    regions = []
    for i in range(10):
        regions.append(allocator.alloc(1))
    for region in regions:
        allocator.realloc(region, 2)
    for region in regions:
        allocator.dealloc(region)


def test_realloc2_1():
    allocator = RegionAllocator(20)
    regions = []
    for i in range(10):
        regions.append(allocator.alloc(2))
    for region in regions:
        allocator.realloc(region, 1)
    for region in regions:
        allocator.dealloc(region)
    assert allocator.get_free_size() == allocator.capacity


def test_realloc_2_1_2():
    allocator = RegionAllocator(30)
    regions = []
    for i in range(10):
        regions.append(allocator.alloc(2))
    for region in regions:
        allocator.realloc(region, 1)
    for region in regions:
        allocator.realloc(region, 2)
    for region in regions:
        allocator.dealloc(region)
    assert allocator.get_free_size() == allocator.capacity


def test_realloc_3_1_5_4_6():
    allocator = RegionAllocator(1000)
    regions = []
    for i in range(10):
        regions.append(allocator.alloc(3))
    for region in regions:
        allocator.realloc(region, 1)
    for region in regions:
        allocator.realloc(region, 5)
    for region in regions:
        allocator.realloc(region, 4)
    for region in regions:
        allocator.realloc(region, 6)
    for region in regions:
        allocator.dealloc(region)
    assert allocator.get_free_size() == allocator.capacity


def test_realloc_3_1_5_4_6_sequential():
    allocator = RegionAllocator(1000)
    regions = []
    for i in range(10):
        regions.append(allocator.alloc(3))
    for region in regions:
        allocator.realloc(region, 1)
        allocator.realloc(region, 5)
        allocator.realloc(region, 4)
        allocator.realloc(region, 6)
    for region in regions:
        allocator.dealloc(region)
    assert allocator.get_free_size() == allocator.capacity


def test_resize1():
    allocator = RegionAllocator(1)
    regions = []
    for i in range(10):
        regions.append(allocator.force_alloc(3))
    for region in regions:
        allocator.dealloc(region)
    assert allocator.get_free_size() == allocator.capacity


def test_mix_resize():
    # Try a bunch of stuff.  There is not much method to this madness.
    allocator = RegionAllocator(1)
    regions = []
    for i in range(10):
        regions.append(allocator.force_alloc(3))
    for region in regions[:5]:
        # import pdb; pdb.set_trace()
        allocator.force_realloc(region, 8)
    for i in range(10):
        regions.append(allocator.force_alloc(i + 1))
    for region in regions[5:15]:
        allocator.force_realloc(region, 5)
    for region in regions[3:18:2]:
        allocator.dealloc(region)
        regions.remove(region)
    for i in range(5):
        regions.append(allocator.force_alloc(3))
    for region in regions[-10:]:
        allocator.force_realloc(region, 6)
    for region in regions:
        allocator.dealloc(region)
    assert allocator.get_free_size() == allocator.capacity
