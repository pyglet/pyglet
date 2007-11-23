#!/usr/bin/python
# $Id:$

import random
import unittest

from graphics import allocation

class Region(object):
    def __init__(self, start, size):
        self.start = start
        self.size = size

    def __repr__(self):
        return 'Region(%r, %r)' % (self.start, self.size)

class RegionAllocator(object):
    def __init__(self, capacity):
        self.allocator = allocation.Allocator(capacity)
        self.regions = []

    def check_region(self, region):
        region_end = region.start + region.size
        for other in self.regions:
            if region is other:
                continue

            other_end = other.start + other.size
            if (other.start < region.start and other_end > region.start) or \
               (other.start < region_end and  other_end > region_end):
                fixture.fail('%r overlaps with %r' % (
                    region, other)) 

    def check_coverage(self):
        starts, sizes = self.allocator.get_allocated_regions()

        if len(starts) != len(sizes):
            fixture.fail('Length of starts (%d) does not match sizes (%d)' % \
                (len(starts), len(sizes)))
        
        if not starts and not self.regions:
            return

        self.regions.sort(key=lambda r: r.start)
        regions = iter(self.regions)
        
        blocks = iter(zip(starts, sizes))
        block_start, block_size = blocks.next()
        block_used = False
        try:
            while True:
                region = regions.next()
                block_used = True
                if region.start < block_start:
                    fixture.fail('Start of %r was not covered at %d' % (
                        region, block_start))
                elif region.start > block_start:
                    fixture.fail('Uncovered block from %d to %r' % (
                        block_start, region))
                block_start += region.size
                block_size -= region.size
                if block_size < 0:
                    fixture.fail('%r extended past end of block by %d' % \
                        (region, -block_size))
                elif block_size == 0:
                    block_start, block_size = blocks.next()
                    block_used = False
        except StopIteration:
            pass

        if not block_used:
            fixture.fail('Uncovered block(s) from %d' % block_start)
                
        try:
            block_start, block_size = blocks.next()
            fixture.fail('Uncovered block(s) from %d' % block_start)
        except StopIteration:
            pass

        try:
            region = regions.next()
            fixture.fail('%r was not covered')
        except StopIteration:
            pass

    def alloc(self, size):
        start = self.allocator.alloc(size)
        region = Region(start, size)
        self.check_region(region)
        self.regions.append(region)
        self.check_coverage()
        return region
        
    def dealloc(self, region):
        assert region in self.regions
        self.allocator.dealloc(region.start, region.size)
        self.regions.remove(region)
        self.check_coverage()

    def realloc(self, region, size):
        assert region in self.regions
        region.start = self.allocator.realloc(region.start, region.size, size)
        region.size = size
        self.check_region(region)
        self.check_coverage()

    def get_free_size(self):
        return self.allocator.get_free_size()

    capacity = property(lambda self: self.allocator.capacity)

class TestAllocation(unittest.TestCase):
    def setUp(self):
        global fixture
        fixture = self

    def test_alloc1(self):
        capacity = 10
        allocator = RegionAllocator(capacity)
        for i in range(capacity):
            allocator.alloc(1)
    
    def test_alloc2(self):
        capacity = 10
        allocator = RegionAllocator(capacity)
        for i in range(capacity//2):
            allocator.alloc(2)

    def test_alloc3(self):
        capacity = 10
        allocator = RegionAllocator(capacity)
        for i in range(capacity//3):
            allocator.alloc(3)

    def test_alloc_mix1_2(self):
        allocs = [1, 2] * 5
        capacity = sum(allocs)
        allocator = RegionAllocator(capacity)
        for alloc in allocs:
            allocator.alloc(alloc)

    def test_alloc_mix5_3_7(self):
        allocs = [5, 3, 7] * 5
        capacity = sum(allocs)
        allocator = RegionAllocator(capacity)
        for alloc in allocs:
            allocator.alloc(alloc)

    def test_dealloc_1_order_all(self):
        capacity = 10
        allocator = RegionAllocator(capacity)
        regions = []
        for i in range(capacity):
            regions.append(allocator.alloc(1))
        for region in regions:
            allocator.dealloc(region)
        self.assertTrue(allocator.get_free_size() == allocator.capacity)

    def test_dealloc_1_order(self):
        capacity = 15
        allocator = RegionAllocator(capacity)
        regions = []
        for i in range(10):
            regions.append(allocator.alloc(1))
        for region in regions:
            allocator.dealloc(region)

    def test_dealloc_1_reverse_all(self):
        capacity = 10
        allocator = RegionAllocator(capacity)
        regions = []
        for i in range(capacity):
            regions.append(allocator.alloc(1))
        for region in regions[::-1]:
            allocator.dealloc(region)
        self.assertTrue(allocator.get_free_size() == allocator.capacity) 
 
    def test_dealloc_1_reverse(self):
        capacity = 15
        allocator = RegionAllocator(capacity)
        regions = []
        for i in range(10):
            regions.append(allocator.alloc(1))
        for region in regions[::-1]:
            allocator.dealloc(region)

    def test_dealloc_mix1_2_order(self):
        allocs = [1, 2] * 5
        capacity = sum(allocs)
        allocator = RegionAllocator(capacity)
        regions = []
        for alloc in allocs:
            regions.append(allocator.alloc(alloc))
        for region in regions:
            allocator.dealloc(region)
        self.assertTrue(allocator.get_free_size() == allocator.capacity)

    def test_dealloc_mix5_3_7_order(self):
        allocs = [5, 3, 7] * 5
        capacity = sum(allocs)
        allocator = RegionAllocator(capacity)
        regions = []
        for alloc in allocs:
            regions.append(allocator.alloc(alloc))
        for region in regions:
            allocator.dealloc(region)
        self.assertTrue(allocator.get_free_size() == allocator.capacity)

    def test_dealloc_1_outoforder(self):
        random.seed(1)
        capacity = 15
        allocator = RegionAllocator(capacity)
        regions = []
        for i in range(capacity):
            regions.append(allocator.alloc(1))
        random.shuffle(regions)
        for region in regions:
            allocator.dealloc(region)
        self.assertTrue(allocator.get_free_size() == allocator.capacity)

    def test_dealloc_mix1_2_outoforder(self):
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
        self.assertTrue(allocator.get_free_size() == allocator.capacity)
 
    def test_dealloc_mix5_3_7_outoforder(self):
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
        self.assertTrue(allocator.get_free_size() == allocator.capacity)

    def mixed_alloc_dealloc_list(self, choices, count=10, seed=1):
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

    def test_mix_alloc_dealloc1(self):
        allocs = self.mixed_alloc_dealloc_list([1])

        capacity = sum([a for a in allocs if a > 0])
        allocator=  RegionAllocator(capacity)
        regions = []
        for alloc in allocs:
            if alloc > 0:
                regions.append(allocator.alloc(alloc))
            else:
                region = regions[abs(alloc)]
                allocator.dealloc(region)
        self.assertTrue(allocator.get_free_size() == allocator.capacity)

    def test_mix_alloc_dealloc5_3_7(self):
        allocs = self.mixed_alloc_dealloc_list([5, 3, 7], count=50)

        capacity = sum([a for a in allocs if a > 0])
        allocator=  RegionAllocator(capacity)
        regions = []
        for alloc in allocs:
            if alloc > 0:
                regions.append(allocator.alloc(alloc))
            else:
                region = regions[abs(alloc)]
                allocator.dealloc(region)
        self.assertTrue(allocator.get_free_size() == allocator.capacity)

    def test_realloc1_2(self):
        allocator = RegionAllocator(30)
        regions = []
        for i in range(10):
            regions.append(allocator.alloc(1))
        for region in regions:
            allocator.realloc(region, 2)
        for region in regions:
            allocator.dealloc(region)

    def test_realloc2_1(self):
        allocator = RegionAllocator(20)
        regions = []
        for i in range(10):
            regions.append(allocator.alloc(2))
        for region in regions:
            allocator.realloc(region, 1)
        for region in regions:
            allocator.dealloc(region) 

    def test_realloc_2_1_2(self):
        allocator = RegionAllocator(20)
        regions = []
        for i in range(10):
            regions.append(allocator.alloc(2))
        for region in regions:
            allocator.realloc(region, 1)
        for region in regions:
            allocator.realloc(region, 2)
        for region in regions:
            allocator.dealloc(region) 

if __name__ == '__main__':
    unittest.main()
