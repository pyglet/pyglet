import unittest

import pyglet
from pyglet.text import runlist
from pyglet.text.formats.attributed import AttributedTextDecoder


class TestStyleRuns(unittest.TestCase):

    def check_value(self, runs, value):
        for i, style in enumerate(value):
            self.assertTrue(runs[i] == style, repr(runs.runs))
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
            it = runs.get_run_iterator()
            for start in range(0, len(value), interval):
                end = min(start + interval, len(value))
                for s, e, style in it.ranges(start, end):
                    for v in value[s:e]:
                        self.assertTrue(v == style, (start, end, s, e, style))

    def check_empty(self, runs, value):
        start, end, style = next(iter(runs))
        self.assertTrue(start == 0)
        self.assertTrue(end == 0)
        self.assertTrue(style == value)

    def test_zero(self):
        runs = runlist.RunList(0, 'x')
        it = iter(runs)

        start, end, s = next(it)
        self.assertTrue(start == 0)
        self.assertTrue(end == 0)
        self.assertTrue(s == 'x')

        with self.assertRaises(StopIteration):
            next(it)
        self.check_optimal(runs)

    def test_initial(self):
        runs = runlist.RunList(10, 'x')
        it = iter(runs)

        start, end, s = next(it)
        self.assertTrue(start == 0)
        self.assertTrue(end == 10)
        self.assertTrue(s == 'x')

        with self.assertRaises(StopIteration):
            next(it)

        self.check_value(runs, 'x' * 10)

    def test_set1(self):
        runs = runlist.RunList(10, 'a')
        runs.set_run(2, 8, 'b')
        self.check_value(runs, 'aabbbbbbaa')

    def test_set1_start(self):
        runs = runlist.RunList(10, 'a')
        runs.set_run(0, 5, 'b')
        self.check_value(runs, 'bbbbbaaaaa')

    def test_set1_end(self):
        runs = runlist.RunList(10, 'a')
        runs.set_run(5, 10, 'b')
        self.check_value(runs, 'aaaaabbbbb')

    def test_set1_all(self):
        runs = runlist.RunList(10, 'a')
        runs.set_run(0, 10, 'b')
        self.check_value(runs, 'bbbbbbbbbb')

    def test_set1_1(self):
        runs = runlist.RunList(10, 'a')
        runs.set_run(1, 2, 'b')
        self.check_value(runs, 'abaaaaaaaa')

    def test_set_overlapped(self):
        runs = runlist.RunList(10, 'a')
        runs.set_run(0, 5, 'b')
        self.check_value(runs, 'bbbbbaaaaa')
        runs.set_run(5, 10, 'c')
        self.check_value(runs, 'bbbbbccccc')
        runs.set_run(3, 7, 'd')
        self.check_value(runs, 'bbbddddccc')
        runs.set_run(4, 6, 'e')
        self.check_value(runs, 'bbbdeedccc')
        runs.set_run(5, 9, 'f')
        self.check_value(runs, 'bbbdeffffc')
        runs.set_run(2, 3, 'g')
        self.check_value(runs, 'bbgdeffffc')
        runs.set_run(1, 3, 'h')
        self.check_value(runs, 'bhhdeffffc')
        runs.set_run(1, 9, 'i')
        self.check_value(runs, 'biiiiiiiic')
        runs.set_run(0, 10, 'j')
        self.check_value(runs, 'jjjjjjjjjj')

    def test_insert_empty(self):
        runs = runlist.RunList(0, 'a')
        runs.insert(0, 10)
        self.check_value(runs, 'aaaaaaaaaa')

    def test_insert_beginning(self):
        runs = runlist.RunList(5, 'a')
        runs.set_run(1, 4, 'b')
        self.check_value(runs, 'abbba')
        runs.insert(0, 3)
        self.check_value(runs, 'aaaabbba')

    def test_insert_beginning_1(self):
        runs = runlist.RunList(5, 'a')
        self.check_value(runs, 'aaaaa')
        runs.insert(0, 1)
        runs.set_run(0, 1, 'a')
        self.check_value(runs, 'aaaaaa')
        runs.insert(0, 1)
        runs.set_run(0, 1, 'a')
        self.check_value(runs, 'aaaaaaa')
        runs.insert(0, 1)
        runs.set_run(0, 1, 'a')
        self.check_value(runs, 'aaaaaaaa')

    def test_insert_beginning_2(self):
        runs = runlist.RunList(5, 'a')
        self.check_value(runs, 'aaaaa')
        runs.insert(0, 1)
        runs.set_run(0, 1, 'b')
        self.check_value(runs, 'baaaaa')
        runs.insert(0, 1)
        runs.set_run(0, 1, 'c')
        self.check_value(runs, 'cbaaaaa')
        runs.insert(0, 1)
        runs.set_run(0, 1, 'c')
        self.check_value(runs, 'ccbaaaaa')

    def test_insert_1(self):
        runs = runlist.RunList(5, 'a')
        runs.set_run(1, 4, 'b')
        self.check_value(runs, 'abbba')
        runs.insert(1, 3)
        self.check_value(runs, 'aaaabbba')

    def test_insert_2(self):
        runs = runlist.RunList(5, 'a')
        runs.set_run(1, 2, 'b')
        self.check_value(runs, 'abaaa')
        runs.insert(2, 3)
        self.check_value(runs, 'abbbbaaa')

    def test_insert_end(self):
        runs = runlist.RunList(5, 'a')
        runs.set_run(4, 5, 'b')
        self.check_value(runs, 'aaaab')
        runs.insert(5, 3)
        self.check_value(runs, 'aaaabbbb')

    def test_insert_almost_end(self):
        runs = runlist.RunList(5, 'a')
        runs.set_run(0, 3, 'b')
        runs.set_run(4, 5, 'c')
        self.check_value(runs, 'bbbac')
        runs.insert(4, 3)
        self.check_value(runs, 'bbbaaaac')

    def test_delete_1_beginning(self):
        runs = runlist.RunList(5, 'a')
        self.check_value(runs, 'aaaaa')
        runs.delete(0, 3)
        self.check_value(runs, 'aa')

    def test_delete_1_middle(self):
        runs = runlist.RunList(5, 'a')
        self.check_value(runs, 'aaaaa')
        runs.delete(1, 4)
        self.check_value(runs, 'aa')

    def test_delete_1_end(self):
        runs = runlist.RunList(5, 'a')
        self.check_value(runs, 'aaaaa')
        runs.delete(2, 5)
        self.check_value(runs, 'aa')

    def test_delete_1_all(self):
        runs = runlist.RunList(5, 'a')
        self.check_value(runs, 'aaaaa')
        runs.delete(0, 5)
        self.check_value(runs, '')
        self.check_empty(runs, 'a')

    def create_runs1(self):
        runs = runlist.RunList(10, 'a')
        runs.set_run(1, 10, 'b')
        runs.set_run(2, 10, 'c')
        runs.set_run(3, 10, 'd')
        runs.set_run(4, 10, 'e')
        runs.set_run(5, 10, 'f')
        runs.set_run(6, 10, 'g')
        runs.set_run(7, 10, 'h')
        runs.set_run(8, 10, 'i')
        runs.set_run(9, 10, 'j')
        self.check_value(runs, 'abcdefghij')
        return runs

    def create_runs2(self):
        runs = runlist.RunList(10, 'a')
        runs.set_run(4, 7, 'b')
        runs.set_run(7, 10, 'c')
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


class TestIssues(unittest.TestCase):

    def test_issue471(self):
        doc = pyglet.text.document.FormattedDocument()
        layout = pyglet.text.layout.IncrementalTextLayout(doc, 100, 100)
        doc.insert_text(0, "hello", {'bold': True})
        doc.text = ""

    def test_issue471_comment2(self):
        doc2 = pyglet.text.decode_attributed('{bold True}a')
        layout = pyglet.text.layout.IncrementalTextLayout(doc2, 100, 10)
        layout.document.delete_text(0, len(layout.document.text))

    def test_issue241_comment4a(self):
        document = pyglet.text.document.FormattedDocument("")
        layout = pyglet.text.layout.IncrementalTextLayout(document, 50, 50)
        document.set_style(0, len(document.text), {"font_name": "Arial"})

    def test_issue241_comment4b(self):
        document = pyglet.text.document.FormattedDocument("test")
        layout = pyglet.text.layout.IncrementalTextLayout(document, 50, 50)
        document.set_style(0, len(document.text), {"font_name": "Arial"})
        document.delete_text(0, len(document.text))

    def test_issue241_comment5(self):
        document = pyglet.text.document.FormattedDocument('A')
        document.set_style(0, 1, dict(bold=True))
        layout = pyglet.text.layout.IncrementalTextLayout(document, 100, 100)
        document.delete_text(0, 1)

    def test_issue429_comment4a(self):
        doc = pyglet.text.decode_attributed(
            '{bold True}Hello{bold False}\n\n\n\n')
        doc2 = pyglet.text.decode_attributed(
            '{bold True}Goodbye{bold False}\n\n\n\n')
        layout = pyglet.text.layout.IncrementalTextLayout(doc, 100, 10)
        layout.document = doc2
        layout.document.delete_text(0, len(layout.document.text))

    def test_issue429_comment4b(self):
        doc2 = pyglet.text.decode_attributed('{bold True}a{bold False}b')
        layout = pyglet.text.layout.IncrementalTextLayout(doc2, 100, 10)
        layout.document.delete_text(0, len(layout.document.text))


class AttributedTextDecoderTests(unittest.TestCase):

    def testOneNewlineBecomesSpace(self):
        doc = AttributedTextDecoder().decode('one\ntwo')
        self.assertEqual('one two', doc.text)

    def testTwoNewlinesBecomesParagraph(self):
        from pyglet.text.formats.attributed import AttributedTextDecoder

        doc = AttributedTextDecoder().decode('one\n\ntwo')
        self.assertEqual('one\ntwo', doc.text)
