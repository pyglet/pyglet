#!/usr/bin/python
# $Id:$

class AllocatorException(Exception):
    pass

class Strip(object):
    def __init__(self, y, max_height):
        self.x = 0
        self.y = y
        self.max_height = max_height
        self.y2 = y

    def add(self, width, height):
        assert width > 0 and height > 0
        assert height <= self.max_height

        x, y = self.x, self.y
        self.x += width
        self.y2 = max(self.y + height, self.y2)
        return x, y

    def compact(self):
        self.max_height = self.y2 - self.y

class RectAllocator(object):
    def __init__(self, width, height):
        assert width > 0 and height > 0
        self.width = width
        self.height = height
        self.strips = [Strip(0, height)]
        self.used_area = 0

    def alloc(self, width, height):
        for strip in self.strips:
            if self.width - strip.x >= width and strip.max_height >= height:
                self.used_area += width * height
                return strip.add(width, height)

        if self.width >= width and self.height - strip.y2 >= height:
            self.used_area += width * height
            strip.compact()
            newstrip = Strip(strip.y2, self.height - strip.y2)
            self.strips.append(newstrip)
            return newstrip.add(width, height)

        raise AllocatorException('No more space in %r for box %dx%d' % (
                self, width, height))

    def get_usage(self):
        return self.used_area / float(self.width * self.height)
            
    def get_fragmentation(self):
        if not self.strips:
            return 0.
        possible_area = self.strips[-1].y2 * width
        return 1.0 - self.used_area / float(possible_area)
