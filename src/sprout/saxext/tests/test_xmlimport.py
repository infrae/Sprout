import unittest
import os.path

from sprout.saxext import xmlimport, xmlexport

_testdir = os.path.split(__file__)[0]

class Doc:
    def __init__(self):
        self._alpha = None

    def setAlpha(self, value):
        self._alpha = value

    def getAlpha(self):
        return self._alpha
    
class Alpha:
    def __init__(self):
        self._sub = []

    def appendSub(self, value):
        self._sub.append(value)

    def getSub(self):
        return self._sub
    
class Beta:
    def __init__(self, value):
        self._value = value

    def getValue(self):
        return self._value
    
class Gamma:
    def __init__(self, value):
        self._value = value

    def getValue(self):
        return self._value
    
class Delta:
    def __init__(self, value):
        self._value = value
        self._extra = None
        
    def setExtra(self, extra):
        self._extra = extra

    def getValue(self):
        return self._value

    def getExtra(self):
        return self._extra
    
class AlphaHandler(xmlimport.BaseHandler):
    def startElementNS(self, name, qname, attrs):
        self.setResult(Alpha())
        self.parent().setAlpha(self.result())

class AlphaProducer(xmlexport.BaseProducer):
    def sax(self):
        self.startElement('alpha')
        for obj in self.context.getSub():
            self.subsax(obj)
        self.endElement('alpha')
        
class BetaHandler(xmlimport.BaseHandler):
    def characters(self, data):
        self.setResult(Beta(data))
        self.parent().appendSub(self.result())

class BetaProducer(xmlexport.BaseProducer):
    def sax(self):
        self.startElement('beta')
        self.handler.characters(self.context.getValue())
        self.endElement('beta')
        
class GammaHandler(xmlimport.BaseHandler):
    def startElementNS(self, name, qname, attrs):
        self.setResult(Gamma(attrs[(None, 'value')]))
        self.parent().appendSub(self.result())

class GammaLocatingHandler(xmlimport.BaseHandler):
    def startElementNS(self, name, qname, attrs):
        locator = self.getDocumentLocator()
        self.setResult((locator.getLineNumber(),
            locator.getColumnNumber(),))
        self.parent().appendSub(self.result())

class GammaProducer(xmlexport.BaseProducer):
    def sax(self):
        self.startElement('gamma', {'value':self.context.getValue()})
        self.endElement('gamma')
        
class DeltaHandler(xmlimport.BaseHandler):
    def getOverrides(self):
        return { (None, 'beta') : SubBetaHandler }
    
    def startElementNS(self, name, qname, attrs):
        self.setResult(Delta(attrs[(None, 'attr')]))

    def endElementNS(self, name, qname):
        self.parent().appendSub(self.result())

class DeltaProducer(xmlexport.BaseProducer):
    def sax(self):
        self.startElement('delta', {'attr': self.context.getValue()})
        self.subsax(self.context.getExtra())
        self.endElement('delta')
        
class SubBetaHandler(xmlimport.BaseHandler):
    def characters(self, data):
        self.setResult(Beta(data))
        self.parent().setExtra(self.result())

class XMLImportTestCase(unittest.TestCase):
    def setUp(self):
        self._importer = xmlimport.Importer({
            (None, 'alpha'): AlphaHandler,
            (None, 'beta') : BetaHandler,
            (None, 'gamma') : GammaHandler,
            (None, 'delta') : DeltaHandler
            })

        self._locating_importer = xmlimport.Importer({
            (None, 'alpha'): AlphaHandler,
            (None, 'beta') : BetaHandler,
            (None, 'gamma') : GammaLocatingHandler,
            (None, 'delta') : DeltaHandler
            })

        self.xml = '''\
<alpha>
   <beta>One</beta>
   <gamma value="Two" />
   <beta>Three</beta>
   <gamma value="Four" />
   <delta attr="Five"><beta>Six</beta></delta>
</alpha>
'''

    def test_importFromString(self):
        result = Doc()
        self._importer.importFromString(self.xml, result=result)
        self.assert_(result.getAlpha() is not None)
        self.assertEquals(5, len(result.getAlpha().getSub()))
        sub = result.getAlpha().getSub()
        self.assertEquals('One', sub[0].getValue())
        self.assertEquals('Two', sub[1].getValue())
        self.assertEquals('Three', sub[2].getValue())
        self.assertEquals('Four', sub[3].getValue())
        self.assertEquals('Five', sub[4].getValue())
        self.assertEquals('Six', sub[4].getExtra().getValue())
        
    def test_importFromFileWithLocator(self):
        result = Doc()
        self._locating_importer.importFromFile(os.path.join(_testdir, 'alpha.xml'), result=result)
        sub = result.getAlpha().getSub()
        line_number, col_count = sub[3]
        self.assertEquals(line_number, 5)
        self.assertEquals(col_count, 3)

    def test_importFromStringWithLocator(self):
        result = Doc()
        self._locating_importer.importFromString(self.xml, result=result)
        sub = result.getAlpha().getSub()
        line_number, col_count = sub[3]
        self.assertEquals(line_number, 5)
        self.assertEquals(col_count, 3)

    def test_importWithFilterHandler(self):
        result = Doc()

        # a handler that replaces Foo with Bar
        from sprout.saxext.hookablehandler import HookableHandler        
        class FooBarHandler(HookableHandler):
            def characters_preprocess(self, data):
                if data == 'Foo':
                    return ['Bar']
                else:
                    return [data]
        settings = xmlimport.BaseSettings(import_filter_factory=FooBarHandler)
        self._importer.importFromString('<alpha><beta>Foo</beta></alpha>', 
            result=result, settings=settings)
        sub = result.getAlpha().getSub()
        # filter should replace any Foo with Bar
        self.assertEquals('Bar', sub[0].getValue())

        
    def test_resultIsResult(self):
        # check whether result from the function is the same as
        # result we pass int
        result = Doc()
        call_result = self._importer.importFromString(
            self.xml, result=result)
        self.assertEquals(result, call_result)
        
    
class NoStartObjectAlphaHandler(xmlimport.BaseHandler):
    def startElementNS(self, name, qname, attrs):
        self.setResult(Alpha())
       
class NoStartObjectImportTestCase(unittest.TestCase):
    
    def setUp(self):
        self._importer = xmlimport.Importer({
            (None, 'alpha'): NoStartObjectAlphaHandler,
            (None, 'beta') : BetaHandler,
            (None, 'gamma') : GammaHandler,
            (None, 'delta') : DeltaHandler
            })
    
    def test_import(self):
        xml = '''\
<alpha>
   <beta>One</beta>
   <gamma value="Two" />
   <beta>Three</beta>
   <gamma value="Four" />
   <delta attr="Five"><beta>Six</beta></delta>
</alpha>
'''
        result = self._importer.importFromString(xml)
        self.assertEquals(5, len(result.getSub()))
        sub = result.getSub()
        self.assertEquals('One', sub[0].getValue())
        self.assertEquals('Two', sub[1].getValue())
        self.assertEquals('Three', sub[2].getValue())
        self.assertEquals('Four', sub[3].getValue())
        self.assertEquals('Five', sub[4].getValue())
        self.assertEquals('Six', sub[4].getExtra().getValue())

class ImportExportTestCase(unittest.TestCase):
    def setUp(self):
        self._importer = xmlimport.Importer({
            (None, 'alpha'): NoStartObjectAlphaHandler,
            (None, 'beta') : BetaHandler,
            (None, 'gamma') : GammaHandler,
            (None, 'delta') : DeltaHandler
            })
        
        self._exporter = xmlexport.Exporter(None)
        self._exporter.registerProducer(
            Alpha, AlphaProducer)
        self._exporter.registerProducer(
            Beta, BetaProducer)
        self._exporter.registerProducer(
            Gamma, GammaProducer)
        self._exporter.registerProducer(
            Delta, DeltaProducer)
        
        self._xml = '''\
<alpha>
   <beta>One</beta>
   <gamma value="Two" />
   <beta>Three</beta>
   <gamma value="Four" />
   <delta attr="Five"><beta>Six</beta></delta>
</alpha>
'''

    def test_import_export_text(self):
        result = self._importer.importFromString(self._xml)
        first_xml = self._exporter.exportToString(result)
        result = self._importer.importFromString(first_xml)
        second_xml = self._exporter.exportToString(result)
        self.assertEquals(first_xml, second_xml)

    def test_import_export_direct(self):
        # directly send producer to handler

        # first do import
        tree = self._importer.importFromString(self._xml)
        # get normalized XML
        first_xml = self._exporter.exportToString(tree)
        # now export, immediately reimporting again
        handler = self._importer.importHandler()
        self._exporter.exportToSax(tree, handler)
        # we should have result in handler now
        new_tree = handler.result()
        # create XML for it so we can compare it
        second_xml = self._exporter.exportToString(new_tree)
        self.assertEquals(first_xml, second_xml)

class Container(object):
    def __init__(self):
        self.children = []
        
class A(object):
    def __init__(self, name):
        self.name = name
        self.children = []

class B(object):
    def __init__(self):
        self.children = []
        self.text = []
        
class C(object):
    def __init__(self):
        self.children = []

class AHandler(xmlimport.BaseHandler):
    def startElementNS(self, name, qname, attrs):
        a = A(name)
        self.parent().children.append(a)
        self.setResult(a)
        
class BHandler(xmlimport.BaseHandler):
    def startElementNS(self, name, qname, attrs):
        b = B()
        self.parent().children.append(b)
        self.setResult(b)
        
    def characters(self, chrs):
        self.result().text.append(chrs)
        
class CHandler(xmlimport.BaseHandler):
    def startElementNS(self, name, qname, attrs):
        c = C()
        self.parent().children.append(c)
        self.setResult(c)
        
class RAHandler(AHandler):
    def isElementAllowed(self, name):
        return name[1] not in ('c', 'd')
        
class RBHandler(BHandler):
    def isTextAllowed(self, chrs):
        return chrs != 'foo'
        
class RCHandler(CHandler):
    pass

class NotAllowedTestCase(unittest.TestCase):
    def setUp(self):
        self._importer = xmlimport.Importer({
            (None, 'a'): AHandler,
            (None, 'b'): BHandler,
            (None, 'c'): CHandler,
            })

        self._rimporter = xmlimport.Importer({
            (None, 'a'): RAHandler,
            (None, 'b'): RBHandler,
            (None, 'c'): RCHandler,
            })
        
    def test_accepted(self):
        result = self._importer.importFromString('<a><b><c>foo</c></b></a>',
                                                 result=Container())
        # should not raise an error
        rresult = self._rimporter.importFromString('<a><b><c>foo</c></b></a>',
                                                   result=Container())

        # check tree that's built
        for r in [result, rresult]:
            self.assertEquals(A, type(r.children[0]))
            self.assertEquals(B, type(r.children[0].children[0]))
            self.assertEquals(C, type(r.children[0].children[0].children[0]))
    
    def test_element_not_allowed(self):
        self.assertRaises(xmlimport.ElementNotAllowedError,
                          self._rimporter.importFromString, '<a><c></c></a>',
                          result=Container())

    def test_element_not_allowed_no_subhandler(self):
        self.assertRaises(xmlimport.ElementNotAllowedError,
                          self._rimporter.importFromString, '<a><d></d></a>',
                          result=Container())

    def test_element_not_allowed_ignore(self):
        result = self._rimporter.importFromString(
            '<a><c></c></a>',
            settings=xmlimport.IGNORE_SETTINGS,
            result=Container())
        self.assertEquals(0, len(result.children[0].children))

    def test_element_not_allowed_ignore2(self):
        result = self._rimporter.importFromString(
            '<a><c><b></b></c><b/></a>',
            settings=xmlimport.IGNORE_SETTINGS,
            result=Container())
        self.assertEquals(1, len(result.children[0].children))
        self.assertEquals(B, type(result.children[0].children[0]))

    def test_structure(self):
        result = self._importer.importFromString(
            '<a><a><c/></a><b><c/></b></a>',
            result=Container())
        self.assertEquals(2, len(result.children[0].children))
        # in a sub element we can find a c
        self.assertEquals(1, len(result.children[0].children[0].children))
        self.assertEquals(C, type(result.children[0].children[0].children[0]))
        # in b sub element we can find a c
        self.assertEquals(1, len(result.children[0].children[1].children))
        self.assertEquals(C, type(result.children[0].children[1].children[0]))
        
    def test_element_not_allowed_ignore3(self):
        result = self._rimporter.importFromString(
            '<a><a><c/></a><b><c/></b></a>',
            settings=xmlimport.IGNORE_SETTINGS,
            result=Container())
        self.assertEquals(2, len(result.children[0].children))
        # in a sub element we can find nothing
        self.assertEquals(0, len(result.children[0].children[0].children))
        # in b sub element we can find a c
        self.assertEquals(1, len(result.children[0].children[1].children))
        self.assertEquals(C, type(result.children[0].children[1].children[0]))

    def test_element_not_allowed_ignore4(self):
        result = self._rimporter.importFromString(
            '<a><c><hoi/><dag/><a><b></b></a></c></a>',
            settings=xmlimport.IGNORE_SETTINGS,
            result=Container())
        self.assertEquals(0, len(result.children[0].children))
        
def test_suite():
    suite = unittest.TestSuite()
    for testcase in [XMLImportTestCase, NoStartObjectImportTestCase,
                     ImportExportTestCase, NotAllowedTestCase]:
        suite.addTest(unittest.makeSuite(testcase))
    return suite

if __name__ == '__main__':
    unittest.main()
    
