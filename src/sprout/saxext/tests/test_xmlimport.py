import unittest

from sprout.saxext import xmlimport

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
        self.getParent().setAlpha(self.getResult())
        
class BetaHandler(xmlimport.BaseHandler):
    def characters(self, data):
        self.setResult(Beta(data))
        self.getParent().appendSub(self.getResult())
        
class GammaHandler(xmlimport.BaseHandler):
    def startElementNS(self, name, qname, attrs):
        self.setResult(Gamma(attrs[(None, 'value')]))
        self.getParent().appendSub(self.getResult())
        
class DeltaHandler(xmlimport.BaseHandler):
    def getOverrides(self):
        return { (None, 'beta') : SubBetaHandler }
    
    def startElementNS(self, name, qname, attrs):
        self.setResult(Delta(attrs[(None, 'attr')]))

    def endElementNS(self, name, qname):
        self.getParent().appendSub(self.getResult())
        
class SubBetaHandler(xmlimport.BaseHandler):
    def characters(self, data):
        self.setResult(Beta(data))
        self.getParent().setExtra(self.getResult())

class XMLImportTestCase(unittest.TestCase):
    def setUp(self):
        self._registry = registry = xmlimport.XMLOverridableElementRegistry()
        registry.addHandlerMap({
            (None, 'alpha'): AlphaHandler,
            (None, 'beta') : BetaHandler,
            (None, 'gamma') : GammaHandler,
            (None, 'delta') : DeltaHandler
            })
    
    def test_import(self):
        xml1 = '''\
<alpha>
   <beta>One</beta>
   <gamma value="Two" />
   <beta>Three</beta>
   <gamma value="Four" />
   <delta attr="Five"><beta>Six</beta></delta>
</alpha>
'''
        result = Doc()
        xmlimport.importFromString(xml1, self._registry, result)
        self.assert_(result.getAlpha() is not None)
        self.assertEquals(5, len(result.getAlpha().getSub()))
        sub = result.getAlpha().getSub()
        self.assertEquals('One', sub[0].getValue())
        self.assertEquals('Two', sub[1].getValue())
        self.assertEquals('Three', sub[2].getValue())
        self.assertEquals('Four', sub[3].getValue())
        self.assertEquals('Five', sub[4].getValue())
        self.assertEquals('Six', sub[4].getExtra().getValue())
        
if __name__ == '__main__':
    unittest.main()
    
