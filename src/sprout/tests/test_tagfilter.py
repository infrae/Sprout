import unittest
from sprout.tagfilter import TagFilter

class TagFilterTestCase(unittest.TestCase):
    def test_simple(self):
        f = TagFilter()
        f.registerElement('b')
        s = f.escapeNonElements('hallo <b>Bold stuff')
        self.assertEquals(
            'hallo <b>Bold stuff', s)

    def test_stray(self):
        f = TagFilter()
        f.registerElement('b')
        f.registerElement('i')
        s = f.escapeNonElements('hallo< <b>Bold stu>ff<b><b')
        self.assertEquals(
            'hallo&lt; <b>Bold stu&gt;ff<b>&lt;b',
            s)

    def test_stray2(self):
        f = TagFilter()
        f.registerElement('b')
        f.registerElement('i')
        s = f.escapeNonElements('hallo< <b>Bold stuff</b</b>>b')
        self.assertEquals(
            'hallo&lt; <b>Bold stuff&lt;/b</b>&gt;b',
            s)

    def test_attributes(self):
        f = TagFilter()
        f.registerElement('a', ['href'])
        s = f.escapeNonElements('<a href<a href="url">jkj><')
        self.assertEquals(
            '&lt;a href<a href="url">jkj&gt;&lt;',
            s)
        
    def test_attributes2(self):
        f = TagFilter()
        f.registerElement('b')
        # unrecognized attributes, so escape
        s = f.escapeNonElements('<b foo="bar">a<b>c</b>')
        self.assertEquals(
            '&lt;b foo="bar"&gt;a<b>c</b>',
            s)

    def test_attributes(self):
        f = TagFilter()
        f.registerElement('a', ['href'])
        # extra attributes, so escape
        s = f.escapeNonElements('<a href="url" foo="bar">')
        self.assertEquals(
            '&lt;a href="url" foo="bar"&gt;',
            s)

    def test_entities(self):
        f = TagFilter()
        f.registerElement('b')
        s = f.escapeNonElements('hoi &foo; dag &amp; iets &bar; nog wat')
        self.assertEquals(
            'hoi &amp;foo; dag &amp; iets &amp;bar; nog wat',
            s)

    def test_entities2(self):
        f = TagFilter()
        f.registerElement('b')
        s = f.escapeNonElements('hoi &lt;foo&gt; &bar;')
        self.assertEquals(
            'hoi &lt;foo&gt; &amp;bar;',
            s)

    def test_entities3(self):
        f = TagFilter(html_entities=True)
        f.registerElement('b')
        s = f.escapeNonElements('hoi &lt;foo&gt; &bar;')
        self.assertEquals(
            'hoi &lt;foo&gt; &amp;bar;',
            s)

    def test_entities4(self):
        f = TagFilter(html_entities=True)
        f.registerElement('b')
        s = f.escapeNonElements('hoi &alpha; &foo;')
        self.assertEquals(
            'hoi &alpha; &amp;foo;',
            s)
        
def test_suite():
    suite = unittest.TestSuite()
    for testcase in [TagFilterTestCase]:
        suite.addTest(unittest.makeSuite(testcase))
    return suite

if __name__ == '__main__':
    unittest.main()
    