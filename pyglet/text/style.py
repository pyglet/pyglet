#!/usr/bin/python
# $Id:$

class StyleRun(object):
    def __init__(self, style, count):
        self.style = style
        self.count = count

    def __repr__(self):
        return 'StyleRun(%r, %d)' % (self.style, self.count)

class StyleRuns(object):
    def __init__(self, size, initial):
        self.runs = [StyleRun(initial, size)]

    def insert(self, pos, length):
        i = 0
        for run in self.runs:
            if i <= pos <= i + run.count:
                run.count += length
            i += run.count

    def delete(self, start, end):
        i = 0
        for run in self.runs:
            if end - start == 0:
                break
            if i <= start <= i + run.count:
                trim = min(end - start, i + run.count - start)
                run.count -= trim
                end -= trim
            i += run.count
        self.runs = [r for r in self.runs if r.count > 0]

        # Don't leave an empty list
        if not self.runs:
            self.runs = [StyleRun(run.style, 0)]

    def set_style(self, start, end, style):
        if end - start <= 0:
            return
        
        # Find runs that need to be split
        i = 0
        start_i = None
        start_trim = 0
        end_i = None
        end_trim = 0
        for run_i, run in enumerate(self.runs):
            count = run.count
            if i < start < i + count:
                start_i = run_i
                start_trim = start - i
            if i < end < i + count:
                end_i = run_i
                end_trim = end - i
            i += count
        
        # Split runs
        if start_i is not None:
            run = self.runs[start_i]
            self.runs.insert(start_i, StyleRun(run.style, start_trim))
            run.count -= start_trim
            if end_i is not None:
                if end_i == start_i:
                    end_trim -= start_trim
                end_i += 1
        if end_i is not None:
            run = self.runs[end_i]
            self.runs.insert(end_i, StyleRun(run.style, end_trim))
            run.count -= end_trim
                
        # Set new style on runs
        i = 0
        for run in self.runs:
            if start <= i and i + run.count <= end: 
                run.style = style
            i += run.count 

        # Merge adjacent runs
        last_run = self.runs[0]
        for run in self.runs[1:]:
            if run.style == last_run.style:
                run.count += last_run.count
                last_run.count = 0
            last_run = run

        # Delete collapsed runs
        self.runs = [r for r in self.runs if r.count > 0]

    def __iter__(self):
        i = 0
        for run in self.runs:
            yield i, i + run.count, run.style
            i += run.count

    def get_range_iterator(self):
        return StyleRunsRangeIterator(self)
    
    def get_style_at(self, index):
        i = 0
        for run in self.runs:
            if i <= index < i + run.count:
                return run.style
            i += run.count

        # If runs are empty, first position still returns default style
        if index == 0 and self.runs[0].count == 0:
            return self.runs[0].style

        assert False, 'Index not in range'

    def __repr__(self):
        return str(list(self))

class StyleRunsRangeIterator(object):
    '''Perform sequential range iterations over a StyleRuns.'''
    def __init__(self, style_runs):
        self.iter = iter(style_runs)
        self.curr_start, self.curr_end, self.curr_style = self.iter.next()
    
    def iter_range(self, start, end):
        '''Iterate over range [start:end].  The range must be sequential from
        the previous `iter_range` call.'''
        while start >= self.curr_end:
            self.curr_start, self.curr_end, self.curr_style = self.iter.next()
        yield start, min(self.curr_end, end), self.curr_style
        while end > self.curr_end:
            self.curr_start, self.curr_end, self.curr_style = self.iter.next()
            yield self.curr_start, min(self.curr_end, end), self.curr_style

    def get_style_at(self, index):
        while index >= self.curr_end:
            self.curr_start, self.curr_end, self.curr_style = self.iter.next()
        return self.curr_style

class OverriddenStyleRunsRangeIterator(object):
    def __init__(self, base_iterator, start, end, style):
        self.iter = base_iterator
        self.override_start = start
        self.override_end = end
        self.override_style = style

    def iter_range(self, start, end):
        if end <= self.override_start or start >= self.override_end:
            # No overlap
            for r in self.iter.iter_range(start, end):
                yield r
        else:
            # Overlap: before, override, after
            if start < self.override_start < end:
                for r in self.iter.iter_range(start, self.override_start):
                    yield r
            yield (max(self.override_start, start),
                   min(self.override_end, end),
                   self.override_style)
            if start < self.override_end < end:
                for r in self.iter.iter_range(self.override_end, end):
                    yield r
        
    def get_style_at(self, index):
        if self.override_start <= index < self.override_end:
            return self.override_style
        else:
            return self.iter.get_style_at(index)

class ZipStyleRunsRangeIterator(object):
    def __init__(self, range_iterators):
        self.range_iterators = range_iterators

    def iter_range(self, start, end):
        iterators = [i.iter_range(start, end) for i in self.range_iterators]
        starts, ends, styles = zip([i.next() for i in iterators])
        while start < end:
            end = min(ends)
            yield start, end, styles
            start = end
            for i in range(iterators):
                if ends[i] == end:
                    starts[i], ends[i], styles[i] = iterators[i].next()

    def get_style_at(self, index):
        return [i.get_style_at(index) for i in self.range_iterators]

