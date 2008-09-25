# -*- coding: utf-8 -*-
import unittest
from sprout import htmlsubset, silvasubset
from sprout.picodom import getDOMImplementation

class ParagraphSubsetTestCase(unittest.TestCase):
    def setUp(self):
        self._subset = silvasubset.createParagraphSubset()
        
    def parse(self, text):        
        document = getDOMImplementation().createDocument(None, 'p')
        p = self._subset.parse(text, document.documentElement)
        return p.toXML()

    def filteredParse(self, text):
        document = getDOMImplementation().createDocument(None, 'p')
        p = self._subset.filteredParse(text, document.documentElement)
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

    def test_link_markup(self):
        self.assertEquals(
            '<p><link url="http://www.infrae.com">The <strong>Infrae</strong> way</link></p>',
            self.parse('<a href="http://www.infrae.com">The <b>Infrae</b> way</a>'))

    def test_link_markup2(self):
        self.assertEquals(
            '<p><link url="http://www.infrae.com">Foo</link></p>',
            self.parse('<a href="http://www.infrae.com">Foo<a href="foo">Bar</a></a>'))

    def test_link_markup3(self):
        self.assertEquals(
            '<p><link url="http://www.infrae.com">Foo</link></p>',
            self.parse('<a href="http://www.infrae.com">Foo<hoi>Bar</hoi></a>'))
        
    def test_index(self):
        self.assertEquals(
            '<p><index name="Foo"></index></p>',
            self.parse('<index name="Foo">Foo</index>'))

    def test_index2(self):
        self.assertEquals(
            '<p><index name="Foo"></index></p>',
            self.parse('<index name="Foo">Fo<b>h</b>o</index>'))
        
    def test_br(self):
        # can't collapse element to <br /> due to limited XML outputter
        # in tests
        self.assertEquals(
            "<p>Foo<br></br>Bar</p>",
            self.parse('Foo<br/>Bar'))

    def test_br_evil(self):
        self.assertEquals(
            '<p>Foo<br></br>heyBar</p>',
            self.parse('Foo<br>hey</br>Bar'))

    def test_br_evil2(self):
        self.assertEquals(
            '<p>Foo<br></br><em>Hoi</em>Bar</p>',
            self.parse('Foo<br><i>Hoi</i></br>Bar'))

    def test_br_evil3(self):
        self.assertEquals(
            '<p>Foo<br></br><em>Hoi<strong>Baz</strong></em>Bar</p>',
            self.parse('Foo<br><i>Hoi<b>Baz</b></i></br>Bar'))

    def test_br_evil4(self):
        self.assertEquals(
            '<p>Foo<br></br>HoiBar</p>',
            self.parse('Foo<br>Hoi</br>Bar'))

    def test_br_immediate_close(self):
        self.assertEquals(
            '<p>Foo<br></br>Bar</p>',
            self.parse('Foo<br/>Bar'))
        
    def test_unknown_tag(self):
        self.assertEquals(
            '<p>FooBar</p>',
            self.parse('Foo<hoi>Hoi</hoi>Bar'))

    # filtered parse tests
    def test_unknown_tag_filtered(self):
        self.assertEquals(
            '<p>Foo&lt;hoi&gt;Hoi&lt;/hoi&gt;Bar</p>',
            self.filteredParse('Foo<hoi>Hoi</hoi>Bar'))

    def test_unknown_attributes_filtered(self):
        self.assertEquals(
            '<p>&lt;a href="http://www.foo.com" hoi="bar"&gt;testThe end</p>',
            self.filteredParse('<a href="http://www.foo.com" hoi="bar">test</a>The end'))

    def test_br_immediate_close_filtered(self):
        self.assertEquals(
            '<p>Hoi<br></br>Dag</p>',
            self.filteredParse('Hoi<br/>Dag'))

    def test_immediate_close_whitespace_filtered(self):
        self.assertEquals(
            '<p>Hoi<link url="Foo"> </link></p>',
            self.filteredParse('Hoi<a href="Foo" />'))

    def test_target_filtered(self):
        self.assertEquals(
            '<p><link target="Bar" url="Foo">Test</link></p>',
            self.filteredParse('<a href="Foo" target="Bar">Test</a>'))

    def test_trivial_filtered(self):
        self.assertEquals(
            '<p>Trivial</p>',
            self.filteredParse('Trivial'))

    # multiline tests
    def test_multiline(self):
        text = '''\
Foo
Bar'''
        
        self.assertEquals(
            '<p>Foo<br></br>Bar</p>',
            self.filteredParse(text))

    def test_multiline2(self):
        text = '''\
Foo
Bar
Baz'''
        self.assertEquals(
            '<p>Foo<br></br>Bar<br></br>Baz</p>',
            self.filteredParse(text))

    
    def test_can_place_a_in_i(self):
        # should be able to place a element inside i tag
        text = '<i><a href="http://www.infrae.com">Foo</a></i>'
        self.assertEquals(
            '<p><em><link url="http://www.infrae.com">Foo</link></em></p>',
            self.filteredParse(text))

    def test_can_place_i_in_i(self):
        # XXX is this the right thing to do? perhaps clean up inner em
        # and retain text would be better.
        text = '<i>Foo<i>Bar</i>Baz</i>'
        self.assertEquals(
            '<p><em>Foo<em>Bar</em>Baz</em></p>',
            self.filteredParse(text))
        
class HeadingSubsetTestCase(unittest.TestCase):
    def setUp(self):
        self._subset = silvasubset.createHeadingSubset()
        
    def parse(self, text):        
        document = getDOMImplementation().createDocument(None, 'heading')
        p = self._subset.parse(text, document.documentElement)
        return p.toXML()

    def filteredParse(self, text):
        document = getDOMImplementation().createDocument(None, 'heading')
        p = self._subset.filteredParse(text, document.documentElement)
        return p.toXML()
    
    def test_heading1(self):
        self.assertEquals(
            '<heading>Foo</heading>',
            self.filteredParse('Foo'))

    def test_heading_bold_not_allowed(self):
        self.assertEquals(
            '<heading>Foo</heading>',
            self.parse('Foo<b>bold</b>'))

    def test_heading_bold_not_allowed_filtered(self):
        self.assertEquals(
            '<heading>Foo&lt;b&gt;bold&lt;/b&gt;</heading>',
            self.filteredParse('Foo<b>bold</b>'))
        
def test_suite():
    suite = unittest.TestSuite()
    for testcase in [ParagraphSubsetTestCase, HeadingSubsetTestCase]:
        suite.addTest(unittest.makeSuite(testcase))
    return suite

if __name__ == '__main__':
    unittest.main()
    
