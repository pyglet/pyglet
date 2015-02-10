import unittest

from pyglet.text.formats.attributed import AttributedTextDecoder

class AttributedTextDecoderTests(unittest.TestCase):
    __noninteractive = True
    def testOneNewlineBecomesSpace(self):
        doc = AttributedTextDecoder().decode('one\ntwo')
        self.assertEqual(u'one two', doc.text)
        
    def testTwoNewlinesBecomesParagraph(self):
        from pyglet.text.formats.attributed import AttributedTextDecoder
        doc = AttributedTextDecoder().decode('one\n\ntwo')
        self.assertEqual(u'one\ntwo', doc.text)

if __name__ == '__main__':
    unittest.main()
