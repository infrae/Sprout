import unittest
from sprout.saxext.collapser import CollapsingHandler
from sprout.saxext.generator import XMLGenerator
from StringIO import StringIO


class TestHandler:

    def __init__(self):
        self._last_characters = None

    def getLastCharacters(self):
        return self._last_characters

    def startElementNS(self, name, qname, attrs):
        pass

    def endElementNS(self, name, qname):
        pass

    def characters(self, content):
        self._last_characters = content


class CollapsingHandlerTestCase(unittest.TestCase):

    def test_pass_along(self):
        # does it actually produce correct output?
        f = StringIO()
        gen = XMLGenerator(f, None)
        handler = CollapsingHandler(gen)
        handler.startElementNS((None, 'b'), None, {})
        handler.characters('hoi')
        handler.characters('dag')
        handler.endElementNS((None, 'b'), None)
        s = f.getvalue()
        self.assertEquals(
            '<b>hoidag</b>',
            s)

    def test_single_event(self):
        handler = TestHandler()
        c = CollapsingHandler(handler)
        # we *have* to produce tags around this, or this
        # test will. Since a normal XML document will always
        # do this, this ought to be okay
        c.startElementNS((None, 'b'), None, {})
        c.characters('hoi')
        c.characters('dag')
        c.endElementNS((None, 'b'), None)
        self.assertEquals(
            'hoidag',
            handler.getLastCharacters())

    def test_empty(self):
        # should not flush empty strings
        handler = TestHandler()
        c = CollapsingHandler(handler)
        c.startElementNS((None, 'b'), None, {})
        self.assertEquals(None, handler.getLastCharacters())


def test_suite():
    suite = unittest.TestSuite()
    for testcase in [CollapsingHandlerTestCase]:
        suite.addTest(unittest.makeSuite(testcase))
    return suite

