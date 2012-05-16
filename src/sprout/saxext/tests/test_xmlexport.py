# test XML exporter
import unittest

from zope import component
from zope.interface import Interface
from zope.testing.cleanup import cleanUp

from sprout.saxext import xmlexport
from sprout.saxext.interfaces import IXMLProducer
from sprout.saxext.xmlexport import XMLExportError
from sprout.saxext.generator import XMLGenerator


class Foo:
    def __init__(self, bars):
        self._bars = bars


class Bar:

    def __init__(self, data, attr):
        self._data = data
        self._attr = attr

class Moo:

    def __init__(self, data, attrs):
        self._data = data
        self._attrs = attrs


class Parent(object):

    def __init__(self, sub):
        self.sub = sub


class Sub(object):
    pass


class FooProducer(xmlexport.BaseProducer):

    def sax(self):
        self.startElement('foo')
        for bar in self.context._bars:
            self.subsax(bar)
        self.endElement('foo')


class BarProducer(xmlexport.BaseProducer):

    def sax(self):
        self.startElement('bar', {'myattr': self.context._attr})
        self.handler.characters(self.context._data)
        self.endElement('bar')


class MooProducer(xmlexport.BaseProducer):

    def sax(self):
        self.startElement('moo', self.context._attrs)
        self.handler.characters(self.context._data)
        self.endElement('moo')


class GooProducer(xmlexport.BaseProducer):

    def sax(self):
        self.startElement('goo')
        self.handler.characters('An unregistered class.')
        self.endElement('goo')


class BazProducer(xmlexport.BaseProducer):

    def sax(self):
        self.startElement('parent')
        self.subsax(self.context.sub, baz=self.context)
        self.endElement('parent')


class SubProducer(xmlexport.BaseProducer):

    def sax(self, baz):
        self.startElement('sub', dict(up=str(id(baz))))
        self.endElement('sub')


class XMLExportTestCase(unittest.TestCase):
    """Test old school xml exporter registration.
    """

    def setUp(self):
        exporter = xmlexport.Exporter(
            'http://www.infrae.com/ns/test')
        exporter.registerProducer(
            Foo, FooProducer)
        exporter.registerProducer(
            Bar, BarProducer)
        self.exporter = exporter

    def test_export(self):
        tree = Foo([Bar('one', 'a'), Bar('two', 'b')])
        self.assertEquals(
            '<?xml version="1.0" encoding="utf-8"?>\n<foo xmlns="http://www.infrae.com/ns/test"><bar myattr="a">one</bar><bar myattr="b">two</bar></foo>',
            self.exporter.exportToString(tree))

    def test_exceptions(self):
        unsupported_type = 'not supported'
        self.assertRaises(
            XMLExportError, self.exporter.exportToString, unsupported_type)


class XMLExportAdaptedTestCase(unittest.TestCase):
    """Test adapter xml exporter registration.
    """

    def setUp(self):
        self.exporter = xmlexport.Exporter(
            'http://www.infrae.com/ns/test')
        component.provideAdapter(FooProducer, (Foo, Interface), IXMLProducer)
        component.provideAdapter(BarProducer, (Bar, Interface), IXMLProducer)
        component.provideAdapter(BazProducer, (Parent, Interface), IXMLProducer)
        component.provideAdapter(SubProducer, (Sub, Interface), IXMLProducer)

    def tearDown(self):
        cleanUp()

    def test_export(self):
        tree = Foo([Bar('one', 'a'), Bar('two', 'b')])
        self.assertEquals(
            '<?xml version="1.0" encoding="utf-8"?>\n<foo xmlns="http://www.infrae.com/ns/test"><bar myattr="a">one</bar><bar myattr="b">two</bar></foo>',
            self.exporter.exportToString(tree))

    def test_sax_with_kw(self):
        parent = Parent(Sub())
        tree = Foo([parent])
        self.assertEquals(
            '<?xml version="1.0" encoding="utf-8"?>\n<foo xmlns="http://www.infrae.com/ns/test"><parent><sub up="%s"/></parent></foo>' % id(parent),
            self.exporter.exportToString(tree))

class Baz:
    pass


class NSAttrProducer(xmlexport.BaseProducer):

    def sax(self):
        self.startElement(
            'hm',
            {('http://www.infrae.com/ns/test2', 'attr'): 'value'})
        self.endElement('hm')


class XMLExportNamespaceTestCase(unittest.TestCase):

    def setUp(self):
        exporter = xmlexport.Exporter(
            'http://www.infrae.com/ns/test')
        exporter.registerNamespace('test2',
                                   'http://www.infrae.com/ns/test2')
        exporter.registerProducer(
            Foo, FooProducer)
        exporter.registerProducer(
            Baz, NSAttrProducer)
        self.exporter = exporter

    def test_namespaced_attribute(self):
        tree = Foo([Baz()])
        self.assertEquals(
            '<?xml version="1.0" encoding="utf-8"?>\n<foo xmlns="http://www.infrae.com/ns/test" xmlns:test2="http://www.infrae.com/ns/test2"><hm test2:attr="value"/></foo>',
            self.exporter.exportToString(tree))


class NoDefaultNamespaceTestCase(unittest.TestCase):

    def setUp(self):
        exporter = xmlexport.Exporter(None)
        exporter.registerProducer(
            Foo, FooProducer)
        self.exporter = exporter

    def test_no_namespace_declaration(self):
        tree = Foo([])
        self.assertEquals(
            '<?xml version="1.0" encoding="utf-8"?>\n<foo/>',
            self.exporter.exportToString(tree))


class CustomXMLGenerator(XMLGenerator):

    def startElementNS(self, name, qname, attrs):
        XMLGenerator.startElementNS(self, (None, 'hey'), None, {})
        XMLGenerator.endElementNS(self, (None, 'hey'), None)
        XMLGenerator.startElementNS(self, name, qname, attrs)


class XMLGeneratorTest(unittest.TestCase):

    def setUp(self):
        exporter = xmlexport.Exporter(None, CustomXMLGenerator)
        exporter.registerProducer(
            Foo, FooProducer)
        self.exporter = exporter

    def test_custom_generator(self):
        tree = Foo([])
        self.assertEquals(
            '<?xml version="1.0" encoding="utf-8"?>\n<hey/><foo/>',
            self.exporter.exportToString(tree))


class FallbackTest(unittest.TestCase):

    def setUp(self):
        exporter = xmlexport.Exporter(None, CustomXMLGenerator)
        exporter.registerProducer(
            Foo, FooProducer)
        exporter.registerFallbackProducer(GooProducer)
        self.exporter = exporter

    def test_fallback_producer(self):
        tree = Foo([Baz()])
        self.assertEquals(
            '<?xml version="1.0" encoding="utf-8"?>\n<hey/><foo><hey/><goo>An unregistered class.</goo></foo>',
            self.exporter.exportToString(tree))


def test_suite():
    suite = unittest.TestSuite()
    for testcase in [XMLExportTestCase, XMLExportAdaptedTestCase,
                     XMLExportNamespaceTestCase, NoDefaultNamespaceTestCase,
                     XMLGeneratorTest, FallbackTest]:
        suite.addTest(unittest.makeSuite(testcase))
    return suite

if __name__ == '__main__':
    unittest.main()


