# test XML exporter
import unittest
from sprout.saxext import xmlexport

class MyXMLSource(xmlexport.BaseXMLSource):
    pass

class Foo:
    def __init__(self, bars):
        self._bars = bars

class Bar:
    def __init__(self, data, attr):
        self._data = data
        self._attr = attr

class FooXMLSource(MyXMLSource):
    def sax(self):
        self.startElement('foo')
        for bar in self.context._bars:
            self.subsax(bar)
        self.endElement('foo')

class BarXMLSource(MyXMLSource):
    def sax(self):
        self.startElement('bar', {'myattr': self.context._attr})
        self.reader.characters(self.context._data)
        self.endElement('bar')
        
class XMLExportTestCase(unittest.TestCase):
    def setUp(self):
        registry = xmlexport.XMLSourceRegistry(
            'http://www.infrae.com/ns/test')
        registry.registerXMLSource(
            Foo, FooXMLSource)
        registry.registerXMLSource(
            Bar, BarXMLSource)
        self.registry = registry

    def test_export(self):
        tree = Foo([Bar('one', 'a'), Bar('two', 'b')])
        self.assertEquals(
            '<?xml version="1.0" encoding="utf-8"?>\n<foo xmlns="http://www.infrae.com/ns/test"><bar myattr="a">one</bar><bar myattr="b">two</bar></foo>',
            self.registry.xmlToString(tree))

class Baz:
    pass

class NSAttrSource(MyXMLSource):
    def sax(self):
        self.startElement(
            'hm',
            {('http://www.infrae.com/ns/test2', 'attr'): 'value'})
        self.endElement('hm')

class XMLExportNamespaceTestCase(unittest.TestCase):
    def setUp(self):
        registry = xmlexport.XMLSourceRegistry(
            'http://www.infrae.com/ns/test')
        registry.registerNamespace('test2',
                                   'http://www.infrae.com/ns/test2')
        registry.registerXMLSource(
            Foo, FooXMLSource)
        registry.registerXMLSource(
            Baz, NSAttrSource)
        self.registry = registry
        
    def test_namespaced_attribute(self):
        tree = Foo([Baz()])
        self.assertEquals(
            '<?xml version="1.0" encoding="utf-8"?>\n<foo xmlns="http://www.infrae.com/ns/test" xmlns:test2="http://www.infrae.com/ns/test2"><hm test2:attr="value"></hm></foo>',
            self.registry.xmlToString(tree))
        

class NoDefaultNamespaceTestCase(unittest.TestCase):
    def setUp(self):
        registry = xmlexport.XMLSourceRegistry(None)
        registry.registerXMLSource(
            Foo, FooXMLSource)
        registry.registerXMLSource(
            Bar, BarXMLSource)
        self.registry = registry
        
    def test_no_namespace_declaration(self):
        tree = Foo([])
        self.assertEquals(
            '<?xml version="1.0" encoding="utf-8"?>\n<foo></foo>',
            self.registry.xmlToString(tree))
        
if __name__ == '__main__':
    unittest.main()
    
