# -*- coding: UTF-8 -*-
import unittest
import parser
from sprout.picodom import Document

class ParserTestCase(unittest.TestCase):
    def setUp(self):
        self._importer = parser.createImporter()
    
    def parse(self, text):        
        document = Document()
        document.documentElement = document.createElement('p')
        p = parser.parse(text, self._importer, document.documentElement)
        return p.toXML()
    
    def test_simple_em(self):
        self.assertEquals('<p><em>Foo</em></p>', self.parse('<i>Foo</i>'))
        
    def test_close_em(self):
        self.assertEquals('<p><em>Foo</em></p>', self.parse('<i>Foo'))

    def test_euml_em(self):
        self.assertEquals(u'<p><em>Foo ë</em></p>',
                          self.parse('<i>Foo &euml;</i>'))

    def test_nomarkup(self):
        self.assertEquals('<p>This is simple</p>',
                          self.parse("This is simple"))
            

    def test_bold_i_markup(self):
        self.assertEquals(
            '<p>This is <strong>Bold</strong> and this is <em>Italic</em></p>',
            self.parse('This is <b>Bold</b> and this is <i>Italic</i>'))

    def test_lots_markup(self):
        self.assertEquals(
            '<p><em>i</em><strong>b</strong><underline>u</underline><sub>sub</sub><super>sup</super></p>',
            self.parse('<i>i</i><b>b</b><u>u</u><sub>sub</sub><sup>sup</sup>'))

    def test_mixed_markup(self):
        self.assertEquals(
            '<p><em><strong>bold italic</strong></em></p>',
            self.parse('<i><b>bold italic</b></i>'))

    def test_link(self):
        self.assertEquals(
            '<p><link url="http://www.infrae.com">Infrae</link></p>',
            self.parse('<a href="http://www.infrae.com">Infrae</a>'))

    def test_index(self):
        self.assertEquals(
            '<p><index name="Foo"></index></p>',
            self.parse('<index>Foo</index>'))

    def test_br(self):
        # can't collapse element to <br /> due to limited XML outputter
        # in tests
        self.assertEquals(
            "<p>Foo<br></br>Bar</p>",
            self.parse('Foo<br/>Bar'))

    def test_br_evil(self):
        self.assertEquals(
            '<p>Foo<br></br>Bar</p>',
            self.parse('Foo<br>hey</br>Bar'))

    def test_br_evil2(self):
        self.assertEquals(
            '<p>Foo<br></br>Bar</p>',
            self.parse('Foo<br><i>Hoi</i></br>Bar'))

    def test_br_evil3(self):
        self.assertEquals(
            '<p>Foo<br></br>Bar</p>',
            self.parse('Foo<br><i>Hoi<b>Baz</b></i></br>Bar'))

# XXX these tests are currently not yet activated
def test_suite():
     pass

if __name__ == '__main__':
    unittest.main()
    
