# test XML exporter
import unittest
from sprout.saxext import xmlexport

class Foo:
    def __init__(self, bars):
        self._bars = bars

class Bar:
    def __init__(self, data, attr):
        self._data = data
        self._attr = attr

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
        
class XMLExportTestCase(unittest.TestCase):
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
            '<?xml version="1.0" encoding="utf-8"?>\n<foo xmlns="http://www.infrae.com/ns/test" xmlns:test2="http://www.infrae.com/ns/test2"><hm test2:attr="value"></hm></foo>',
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
            '<?xml version="1.0" encoding="utf-8"?>\n<foo></foo>',
            self.exporter.exportToString(tree))
        
if __name__ == '__main__':
    unittest.main()
    
