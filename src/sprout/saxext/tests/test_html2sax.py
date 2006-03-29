# -*- coding: UTF-8 -*-
import unittest
from sprout.saxext.generator import XMLGenerator
from StringIO import StringIO
from sprout.saxext import html2sax

def makeXML(html):
    f = StringIO()
    gen = XMLGenerator(f, None)
    html2sax.saxify(html, gen)
    return f.getvalue()
        
class HTML2SaxTestCase(unittest.TestCase):
    
    def test_simple(self):
        self.assertEquals(
            '<b>Bold</b>',
            makeXML('<b>Bold</b>'))
    
    def test_never_closed(self):
        self.assertEquals(
            '<b>Bold</b>',
            makeXML('<b>Bold'))

    def test_weirdly_nested(self):
        self.assertEquals(
            '<b><i>Italic</i></b>Some more',
            makeXML('<b><i>Italic</b>Some more</i>'))

    def test_two_never_closed(self):
        self.assertEquals(
            '<b><i>Italic and bold</i></b>',
            makeXML('<b><i>Italic and bold'))

    def test_entities(self):
        self.assertEquals(
            '<b>&amp;</b>',
            makeXML('<b>&amp;</b>'))

    def test_extended_entities(self):
        self.assertEquals(
            u'<b>é</b>',
            makeXML('<b>&eacute;</b>'))

    def test_unicode_entities(self):
        self.assertEquals(
            u'<b>é</b>',
            makeXML('<b>&#233;</b>'))

    def test_unicode_entities_hex(self):
        self.assertEquals(
            u'<b>é</b>',
            makeXML('<b>&#xe9;</b>'))

    def test_unknown_entities(self):
        self.assertEquals(
            '<b> </b>',
            makeXML('<b>&foo;</b>'))

    def test_just_text(self):
        self.assertEquals(
            'just text',
            makeXML('just text'))

    def test_br(self):
        # br closes right away
        self.assertEquals(
            '<br/>',
            makeXML('<br>'))

    def test_br2(self):
        self.assertEquals(
            '<br/>',
            makeXML('<br></br>'))

    def test_mandatory_closing_tags(self):
        self.assertEquals(
            '<textarea> </textarea>',
            makeXML('<textarea></textarea>'))

    def test_empty_attribute(self):
        self.assertEquals(
            '<option selected="selected">foo</option>',
            makeXML('<option selected>foo</option>'))
        
def test_suite():
    suite = unittest.TestSuite()
    for testcase in [HTML2SaxTestCase]:
        suite.addTest(unittest.makeSuite(testcase))
    return suite

if __name__ == '__main__':
    unittest.main()
    

    
