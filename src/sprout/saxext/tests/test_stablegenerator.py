import unittest
from sprout.saxext.stablegenerator import StableXMLGenerator
from StringIO import StringIO

class TestCase(unittest.TestCase):

    def test_immediateClose(self):
        f = StringIO()
        g = StableXMLGenerator(f)
        g.startElementNS((None, 'foo'), None, {})
        g.endElementNS((None, 'foo'), None)
        out = f.getvalue()
        self.assertEquals('<foo/>', out)

    def test_notclose_characters(self):
        f = StringIO()
        g = StableXMLGenerator(f)
        g.startElementNS((None, 'foo'), None, {})
        g.characters('some characters')
        g.endElementNS((None, 'foo'), None)
        out = f.getvalue()
        self.assertEquals('<foo>some characters</foo>', out)

    def test_notclose_ignorableWhitespace(self):
        f = StringIO()
        g = StableXMLGenerator(f)
        g.startElementNS((None, 'foo'), None, {})
        g.ignorableWhitespace(' ')
        g.endElementNS((None, 'foo'), None)
        out = f.getvalue()
        self.assertEquals('<foo> </foo>', out)

    def test_notclose_processingInstruction(self):
        f = StringIO()
        g = StableXMLGenerator(f)
        g.startElementNS((None, 'foo'), None, {})
        g.processingInstruction('bar', 'baz')
        g.endElementNS((None, 'foo'), None)
        out = f.getvalue()
        self.assertEquals('<foo><?bar baz?></foo>', out)

    def test_notclose_element(self):
        f = StringIO()
        g = StableXMLGenerator(f)
        g.startElementNS((None, 'foo'), None, {})
        g.startElementNS((None, 'bar'), None, {})
        g.endElementNS((None, 'bar'), None)
        g.endElementNS((None, 'foo'), None)
        out = f.getvalue()
        self.assertEquals('<foo><bar/></foo>', out)

    def test_notclose_element2(self):
        f = StringIO()
        g = StableXMLGenerator(f)
        g.startElementNS((None, 'foo'), None, {})
        g.startElementNS((None, 'bar'), None, {})
        g.characters('text')
        g.endElementNS((None, 'bar'), None)
        g.endElementNS((None, 'foo'), None)
        out = f.getvalue()
        self.assertEquals('<foo><bar>text</bar></foo>', out)

    
def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([unittest.makeSuite(TestCase)])
    return suite

if __name__ == '__main__':
    unittest.main()
    
