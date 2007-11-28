#!/usr/bin/python
# $Id:$

import text

import unittest

class TestStyleRuns(unittest.TestCase):
    def test_zero(self):
        runs = text.StyleRuns(0, 'x')
        it = iter(runs)
        
        start, end, style = it.next()
        self.assertTrue(start == 0)
        self.assertTrue(end == 0)
        self.assertTrue(style == 'x')

        self.assertRaises(StopIteration, it.next)
        self.check_optimal(runs)

    def test_initial(self):
        runs = text.StyleRuns(10, 'x')
        it = iter(runs)

        start, end, style = it.next()
        self.assertTrue(start == 0)
        self.assertTrue(end == 10)
        self.assertTrue(style == 'x')

        self.assertRaises(StopIteration, it.next)

        self.check_value(runs, 'x' * 10)

    def check_value(self, runs, value):
        for i, style in enumerate(value):
            self.assertTrue(runs.get_style_at(i) == style, repr(runs.runs))
        self.check_optimal(runs)
        self.check_continuous(runs)
        self.check_iter(runs, value)
        self.check_iter_range(runs, value)

    def check_optimal(self, runs):
        last_style = None
        for _, _, style in runs:
            self.assertTrue(style != last_style)
            last_style = style

    def check_continuous(self, runs):
        next_start = 0
        for start, end, _ in runs:
            self.assertTrue(start == next_start)
            next_start = end
        self.assertTrue(next_start == runs.size)

    def check_iter(self, runs, value):
        for start, end, style in runs:
            for v in value[start:end]:
                self.assertTrue(v == style)

    def check_iter_range(self, runs, value):
        for start in range(0, runs.size):
            for end in range(start, runs.size):
                for s, e, style in runs.iter_range(start, end):
                    for v in value[s:e]:
                        self.assertTrue(v == style, (start, end, s, e, style))

    def test_set1(self):
        runs = text.StyleRuns(10, 'a')
        runs.set_style(2, 8, 'b')
        self.check_value(runs, 'aabbbbbbaa')

    def test_set1_start(self):
        runs = text.StyleRuns(10, 'a')
        runs.set_style(0, 5, 'b')
        self.check_value(runs, 'bbbbbaaaaa')

    def test_set1_end(self):
        runs = text.StyleRuns(10, 'a')
        runs.set_style(5, 10, 'b')
        self.check_value(runs, 'aaaaabbbbb')

    def test_set1_all(self):
        runs = text.StyleRuns(10, 'a')
        runs.set_style(0, 10, 'b')
        self.check_value(runs, 'bbbbbbbbbb')

    def test_set1_1(self):
        runs = text.StyleRuns(10, 'a')
        runs.set_style(1, 2, 'b')
        self.check_value(runs, 'abaaaaaaaa')
    
    def test_set_overlapped(self):
        runs = text.StyleRuns(10, 'a')
        runs.set_style(0, 5, 'b')
        self.check_value(runs, 'bbbbbaaaaa')
        runs.set_style(5, 10, 'c')
        self.check_value(runs, 'bbbbbccccc')
        runs.set_style(3, 7, 'd')
        self.check_value(runs, 'bbbddddccc')
        runs.set_style(4, 6, 'e')
        self.check_value(runs, 'bbbdeedccc')
        runs.set_style(5, 9, 'f')
        self.check_value(runs, 'bbbdeffffc')
        runs.set_style(2, 3, 'g')
        self.check_value(runs, 'bbgdeffffc')
        runs.set_style(1, 3, 'h')
        self.check_value(runs, 'bhhdeffffc')
        runs.set_style(1, 9, 'i')
        self.check_value(runs, 'biiiiiiiic')
        runs.set_style(0, 10, 'j')
        self.check_value(runs, 'jjjjjjjjjj')

if __name__ == '__main__':
    unittest.main()
