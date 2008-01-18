#!/usr/bin/python
# $Id:$

from pyglet.text import style

import unittest

__noninteractive = True

class TestStyleRuns(unittest.TestCase):
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

    def check_iter(self, runs, value):
        for start, end, style in runs:
            for v in value[start:end]:
                self.assertTrue(v == style)

    def check_iter_range(self, runs, value):
        for interval in range(1, len(value)):
            it = runs.get_range_iterator()
            for start in range(0, len(value), interval):
                end = min(start + interval, len(value))
                for s, e, style in it.iter_range(start, end):
                    for v in value[s:e]:
                        self.assertTrue(v == style, (start, end, s, e, style))

    def check_empty(self, runs, value):
        start, end, style = iter(runs).next()
        self.assertTrue(start == 0)
        self.assertTrue(end == 0)
        self.assertTrue(style == value)

    def test_zero(self):
        runs = style.StyleRuns(0, 'x')
        it = iter(runs)
        
        start, end, s = it.next()
        self.assertTrue(start == 0)
        self.assertTrue(end == 0)
        self.assertTrue(s == 'x')

        self.assertRaises(StopIteration, it.next)
        self.check_optimal(runs)

    def test_initial(self):
        runs = style.StyleRuns(10, 'x')
        it = iter(runs)

        start, end, s = it.next()
        self.assertTrue(start == 0)
        self.assertTrue(end == 10)
        self.assertTrue(s == 'x')

        self.assertRaises(StopIteration, it.next)

        self.check_value(runs, 'x' * 10)

    def test_set1(self):
        runs = style.StyleRuns(10, 'a')
        runs.set_style(2, 8, 'b')
        self.check_value(runs, 'aabbbbbbaa')

    def test_set1_start(self):
        runs = style.StyleRuns(10, 'a')
        runs.set_style(0, 5, 'b')
        self.check_value(runs, 'bbbbbaaaaa')

    def test_set1_end(self):
        runs = style.StyleRuns(10, 'a')
        runs.set_style(5, 10, 'b')
        self.check_value(runs, 'aaaaabbbbb')

    def test_set1_all(self):
        runs = style.StyleRuns(10, 'a')
        runs.set_style(0, 10, 'b')
        self.check_value(runs, 'bbbbbbbbbb')

    def test_set1_1(self):
        runs = style.StyleRuns(10, 'a')
        runs.set_style(1, 2, 'b')
        self.check_value(runs, 'abaaaaaaaa')
    
    def test_set_overlapped(self):
        runs = style.StyleRuns(10, 'a')
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

    def test_insert_empty(self):
        runs = style.StyleRuns(0, 'a')
        runs.insert(0, 10)
        self.check_value(runs, 'aaaaaaaaaa')

    def test_insert_beginning(self):
        runs = style.StyleRuns(5, 'a')
        runs.set_style(1, 4, 'b')
        self.check_value(runs, 'abbba')
        runs.insert(0, 3)
        self.check_value(runs, 'aaaabbba')

    def test_insert_beginning_1(self):
        runs = style.StyleRuns(5, 'a')
        self.check_value(runs, 'aaaaa')
        runs.insert(0, 1)
        runs.set_style(0, 1, 'a')
        self.check_value(runs, 'aaaaaa')
        runs.insert(0, 1)
        runs.set_style(0, 1, 'a')
        self.check_value(runs, 'aaaaaaa')
        runs.insert(0, 1)
        runs.set_style(0, 1, 'a')
        self.check_value(runs, 'aaaaaaaa')

    def test_insert_beginning_2(self):
        runs = style.StyleRuns(5, 'a')
        self.check_value(runs, 'aaaaa')
        runs.insert(0, 1)
        runs.set_style(0, 1, 'b')
        self.check_value(runs, 'baaaaa')
        runs.insert(0, 1)
        runs.set_style(0, 1, 'c')
        self.check_value(runs, 'cbaaaaa')
        runs.insert(0, 1)
        runs.set_style(0, 1, 'c')
        self.check_value(runs, 'ccbaaaaa')

    def test_insert_1(self):
        runs = style.StyleRuns(5, 'a')
        runs.set_style(1, 4, 'b')
        self.check_value(runs, 'abbba')
        runs.insert(1, 3)
        self.check_value(runs, 'aaaabbba')

    def test_insert_2(self):
        runs = style.StyleRuns(5, 'a')
        runs.set_style(1, 2, 'b')
        self.check_value(runs, 'abaaa')
        runs.insert(2, 3)
        self.check_value(runs, 'abbbbaaa')

    def test_insert_end(self):
        runs = style.StyleRuns(5, 'a')
        runs.set_style(4, 5, 'b')
        self.check_value(runs, 'aaaab')
        runs.insert(5, 3)
        self.check_value(runs, 'aaaabbbb')

    def test_insert_almost_end(self):
        runs = style.StyleRuns(5, 'a')
        runs.set_style(0, 3, 'b')
        runs.set_style(4, 5, 'c')
        self.check_value(runs, 'bbbac')
        runs.insert(4, 3)
        self.check_value(runs, 'bbbaaaac') 

    def test_delete_1_beginning(self):
        runs = style.StyleRuns(5, 'a')
        self.check_value(runs, 'aaaaa') 
        runs.delete(0, 3)
        self.check_value(runs, 'aa') 

    def test_delete_1_middle(self):
        runs = style.StyleRuns(5, 'a')
        self.check_value(runs, 'aaaaa') 
        runs.delete(1, 4)
        self.check_value(runs, 'aa') 
         
    def test_delete_1_end(self):
        runs = style.StyleRuns(5, 'a')
        self.check_value(runs, 'aaaaa') 
        runs.delete(2, 5)
        self.check_value(runs, 'aa') 

    def test_delete_1_all(self):
        runs = style.StyleRuns(5, 'a')
        self.check_value(runs, 'aaaaa') 
        runs.delete(0, 5)
        self.check_value(runs, '') 
        self.check_empty(runs, 'a')

    def create_runs1(self):
        runs = style.StyleRuns(10, 'a')
        runs.set_style(1, 10, 'b')
        runs.set_style(2, 10, 'c')
        runs.set_style(3, 10, 'd')
        runs.set_style(4, 10, 'e')
        runs.set_style(5, 10, 'f')
        runs.set_style(6, 10, 'g')
        runs.set_style(7, 10, 'h')
        runs.set_style(8, 10, 'i')
        runs.set_style(9, 10, 'j')
        self.check_value(runs, 'abcdefghij')
        return runs

    def create_runs2(self):
        runs = style.StyleRuns(10, 'a')
        runs.set_style(4, 7, 'b')
        runs.set_style(7, 10, 'c')
        self.check_value(runs, 'aaaabbbccc')
        return runs

    def test_delete2(self):
        runs = self.create_runs1()
        runs.delete(0, 5)
        self.check_value(runs, 'fghij')

    def test_delete3(self):
        runs = self.create_runs1()
        runs.delete(2, 8)
        self.check_value(runs, 'abij')

    def test_delete4(self):
        runs = self.create_runs2()
        runs.delete(0, 5)
        self.check_value(runs, 'bbccc')
       
    def test_delete5(self):
        runs = self.create_runs2()
        runs.delete(5, 10)
        self.check_value(runs, 'aaaab') 

    def test_delete6(self):
        runs = self.create_runs2()
        runs.delete(0, 8)
        self.check_value(runs, 'cc') 

    def test_delete7(self):
        runs = self.create_runs2()
        runs.delete(2, 10)
        self.check_value(runs, 'aa') 

    def test_delete8(self):
        runs = self.create_runs2()
        runs.delete(3, 8)
        self.check_value(runs, 'aaacc')

    def test_delete9(self):
        runs = self.create_runs2()
        runs.delete(7, 8)
        self.check_value(runs, 'aaaabbbcc')

    def test_delete10(self):
        runs = self.create_runs2()
        runs.delete(8, 9) 
        self.check_value(runs, 'aaaabbbcc')

    def test_delete11(self):
        runs = self.create_runs2()
        runs.delete(9, 10)
        self.check_value(runs, 'aaaabbbcc')

    def test_delete12(self):
        runs = self.create_runs2()
        runs.delete(4, 5)
        self.check_value(runs, 'aaaabbccc')

    def test_delete13(self):
        runs = self.create_runs2()
        runs.delete(5, 6)
        self.check_value(runs, 'aaaabbccc')

    def test_delete14(self):
        runs = self.create_runs2()
        runs.delete(6, 7)
        self.check_value(runs, 'aaaabbccc')

if __name__ == '__main__':
    unittest.main()
