import unittest
from sprout.saxext.generator import XMLGenerator
from StringIO import StringIO

class TestCase(unittest.TestCase):

    def test_immediateClose(self):
        f = StringIO()
        g = XMLGenerator(f)
        g.startElementNS((None, 'foo'), None, {})
        g.endElementNS((None, 'foo'), None)
        out = f.getvalue()
        self.assertEquals('<foo/>', out)

    def test_close_empty_characters(self):
        f = StringIO()
        g = XMLGenerator(f)
        g.startElementNS((None, 'foo'), None, {})
        g.characters('')
        g.endElementNS((None, 'foo'), None)
        out = f.getvalue()
        self.assertEquals('<foo/>', out)
        
    def test_close_empty_whitespace(self):
        f = StringIO()
        g = XMLGenerator(f)
        g.startElementNS((None, 'foo'), None, {})
        g.ignorableWhitespace('')
        g.endElementNS((None, 'foo'), None)
        out = f.getvalue()
        self.assertEquals('<foo/>', out)

    def test_notclose_characters(self):
        f = StringIO()
        g = XMLGenerator(f)
        g.startElementNS((None, 'foo'), None, {})
        g.characters('some characters')
        g.endElementNS((None, 'foo'), None)
        out = f.getvalue()
        self.assertEquals('<foo>some characters</foo>', out)

    def test_notclose_ignorableWhitespace(self):
        f = StringIO()
        g = XMLGenerator(f)
        g.startElementNS((None, 'foo'), None, {})
        g.ignorableWhitespace(' ')
        g.endElementNS((None, 'foo'), None)
        out = f.getvalue()
        self.assertEquals('<foo> </foo>', out)

    def test_notclose_processingInstruction(self):
        f = StringIO()
        g = XMLGenerator(f)
        g.startElementNS((None, 'foo'), None, {})
        g.processingInstruction('bar', 'baz')
        g.endElementNS((None, 'foo'), None)
        out = f.getvalue()
        self.assertEquals('<foo><?bar baz?></foo>', out)

    def test_notclose_element(self):
        f = StringIO()
        g = XMLGenerator(f)
        g.startElementNS((None, 'foo'), None, {})
        g.startElementNS((None, 'bar'), None, {})
        g.endElementNS((None, 'bar'), None)
        g.endElementNS((None, 'foo'), None)
        out = f.getvalue()
        self.assertEquals('<foo><bar/></foo>', out)

    def test_notclose_element2(self):
        f = StringIO()
        g = XMLGenerator(f)
        g.startElementNS((None, 'foo'), None, {})
        g.startElementNS((None, 'bar'), None, {})
        g.characters('text')
        g.endElementNS((None, 'bar'), None)
        g.endElementNS((None, 'foo'), None)
        out = f.getvalue()
        self.assertEquals('<foo><bar>text</bar></foo>', out)        

    def test_namespace_close(self):
        f = StringIO()
        g = XMLGenerator(f)
        uri = 'http://ns.infrae.com/test'
        g.startPrefixMapping('test', uri)
        g.startElementNS((uri, 'foo'), None, {})
        g.endElementNS((uri, 'foo'), None)
        g.endPrefixMapping('test')
        out = f.getvalue()
        self.assertEquals('<test:foo xmlns:test="http://ns.infrae.com/test"/>',
                          out)

    def test_namespace_sorting(self):
        f = StringIO()
        g = XMLGenerator(f)
        uri_a = 'http://a'
        uri_b = 'http://b'
        uri_c = 'http://c'
        g.startPrefixMapping('b', uri_b)
        g.startPrefixMapping('a', uri_a)
        g.startPrefixMapping('c', uri_c)
        g.startPrefixMapping(None, 'http://n')
        g.startElementNS((None, 'foo'), None, {})
        g.endElementNS((None, 'foo'), None)
        out = f.getvalue()
        self.assertEquals(
            '<foo xmlns="http://n" xmlns:a="http://a" xmlns:b="http://b" xmlns:c="http://c"/>',
            out)
                       
    def test_attr_sorting(self):
        f = StringIO()
        g = XMLGenerator(f)
        d = {
            (None, 'a'): 'A',
            (None, 'b'): 'B',
            (None, 'c'): 'C',
            (None, 'd'): 'D',
            }
        g.startElementNS((None, 'foo'), None, d)
        g.endElementNS((None, 'foo'), None)
        out = f.getvalue()
        self.assertEquals('<foo a="A" b="B" c="C" d="D"/>', out)
        
    def test_attr_sorting2(self):
        f = StringIO()
        g = XMLGenerator(f)
        
        d = {
            'name03':'Clara01',
            'name09':'Clara02',
            'name04':'Clara03',
            'name06':'Clara04',
            'name01':'Clara05',
            'name05':'Clara06',
            'name08':'Clara07',
            'name02':'Clara08',
            'name10':'Clara09',
            'name07':'Clara10',
            }

        nd = {}
        for key, value in d.items():
            nd[(None, key)] = value
        d = nd
        g.startDocument()
        g.startElementNS((None, 'moo'), None, d)
        g.endElementNS((None, 'moo'), None)
        g.endDocument()
        out = f.getvalue()
        
        self.assertEquals(
            '<?xml version="1.0" encoding="UTF-8"?>\n<moo name01="Clara05" name02="Clara08" name03="Clara01" name04="Clara03" name05="Clara06" name06="Clara04" name07="Clara10" name08="Clara07" name09="Clara02" name10="Clara09"/>',
            out)

    def test_unicode(self):
        f = StringIO()
        g = XMLGenerator(f, encoding=None)

        g.startDocument()
        g.startElementNS((None, 'foo'), None, {})
        g.characters(u'Text')
        g.endElementNS((None, 'foo'), None)
        g.endDocument()
        
        out = f.getvalue()
        self.assertEquals('<?xml version="1.0"?>\n<foo>Text</foo>', out)
        self.assert_(isinstance(out, unicode))

    def test_namespace(self):
        f = StringIO()
        g = XMLGenerator(f)
        uri = 'http://www.test.com/ns'
        g.startPrefixMapping('ns', uri)
        g.startElementNS((uri, 'foo'), None, {})
        g.endElementNS((uri, 'foo'), None)
        g.endPrefixMapping('ns')
        self.assertEquals('<ns:foo xmlns:ns="http://www.test.com/ns"/>',
                          f.getvalue())

    def test_default_namespace(self):
        f = StringIO()
        g = XMLGenerator(f)
        uri = 'http://www.test.com/ns'
        g.startPrefixMapping(None, uri)
        g.startElementNS((uri, 'foo'), None, {})
        g.endElementNS((uri, 'foo'), None)
        g.endPrefixMapping(None)
        self.assertEquals('<foo xmlns="http://www.test.com/ns"/>',
                          f.getvalue())

    def test_unknown_namespace(self):
        f = StringIO()
        g = XMLGenerator(f)
        uri ='http://www.test.com/ns'
        self.assertRaises(KeyError, g.startElementNS, (uri, 'foo'), None, {})

    def test_unknown_attr_namespace(self):
        f = StringIO()
        g = XMLGenerator(f)
        uri = 'http://www.test.com/ns'
        attrs = {
            (uri, 'bar') : 'Baz',
            }
        g.startPrefixMapping(None, uri)
        self.assertRaises(KeyError, g.startElementNS, (None, 'foo'), None,
                          attrs)
        
def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([unittest.makeSuite(TestCase)])
    return suite

if __name__ == '__main__':
    unittest.main()
