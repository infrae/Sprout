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

class MyXMLSource(xmlexport.BaseXMLSource):
    ns_default = 'http://www.infrae.com/ns/test'
    
class FooXMLSource(MyXMLSource):

    def _sax(self):
        self._startElement('foo')
        for bar in self.context._bars:
            self.getXMLSource(bar)._sax()
        self._endElement('foo')

class BarXMLSource(MyXMLSource):
    def _sax(self):
        self._startElement('bar', {'myattr': self.context._attr})
        self._reader.characters(self.context._data)
        self._endElement('bar')
        
class XMLExportTestCase(unittest.TestCase):
    def setUp(self):
        
        registry = xmlexport.XMLSourceRegistry()
        registry.registerXMLSource(
            Foo, FooXMLSource)
        registry.registerXMLSource(
            Bar, BarXMLSource)
        self.registry = registry
        
    def test_export(self):
        tree = Foo([Bar('one', 'a'), Bar('two', 'b')])
        self.assertEquals(
            '<foo xmlns="http://www.infrae.com/ns/test"><bar myattr="a">one</bar><bar myattr="b">two</bar></foo>',
            self.registry.xmlToString(tree))
        
if __name__ == '__main__':
    unittest.main()
    
