"""Particular HTMLish subsets as used by Silva.
"""

from sprout import htmlsubset
from sprout.saxext import xmlimport

MARKUP_BASE = ['i', 'sup', 'sub']
MARKUP_LINK = ['a', 'index']
MARKUP_TEXT = MARKUP_BASE + ['b', 'u']
MARKUP_TEXT_BR = MARKUP_TEXT + ['br']
MARKUP = MARKUP_TEXT_BR + MARKUP_LINK
MARKUP_HEADING = MARKUP_BASE + MARKUP_LINK

MARKUP_TEXT_TRANSLATION = {
    'i': 'em',
    'sup': 'super',
    'sub': 'sub',
    'b': 'strong',    
    'u' : 'underline',
    }

def createParagraphSubset():
    subset = htmlsubset.Subset()
    for name in MARKUP_TEXT:
        handler = markupTextHandlerClass(name, MARKUP_TEXT_TRANSLATION[name])
        element = htmlsubset.Element(name, [], [], MARKUP_TEXT_BR, handler)
        subset.registerElement(element)
    subset.registerElement(
        htmlsubset.Element('a', ['href'], [], MARKUP_TEXT_BR, AHandler))
    subset.registerElement(
        htmlsubset.Element('index', [], [], [], IndexHandler))
    subset.registerElement(
        htmlsubset.Element('br', [], [], [], BrHandler))
    # 'block' tag is used to produce fake surrounding tag, real one will
    # be 'p'. Need to register allowed elements for it
    subset.registerElement(
        htmlsubset.Element('block', [], [], MARKUP,
                           htmlsubset.BlockHandler))
    return subset

class MarkupTextHandler(htmlsubset.SubsetHandler):
    def startElementNS(self, name, qname, attrs):
        node = self.parent()
        child = node.ownerDocument.createElement(self.tree_name)
        node.appendChild(child)
        self.setResult(child)
        
    def characters(self, data):
        node = self.result()
        node.appendChild(node.ownerDocument.createTextNode(data))

def markupTextHandlerClass(parsed_name, tree_name):
    """Construct subclass able to handle element of name.
    """
    return type('%s_handler_class' % parsed_name, (MarkupTextHandler,),
                {'tree_name': tree_name, 'parsed_name': parsed_name})

class AHandler(htmlsubset.SubsetHandler):
    parsed_name = 'a'
    
    def startElementNS(self, name, qname, attrs):
        node = self.parent()
        child = node.ownerDocument.createElement('link')
        child.setAttribute('url', attrs[(None, 'href')])
        node.appendChild(child)
        self.setResult(child)

    def characters(self, data):
        node = self.result()
        node.appendChild(node.ownerDocument.createTextNode(data))

class IndexHandler(htmlsubset.SubsetHandler):
    parsed_name = 'index'
    
    def __init__(self, parent, parent_handler,
                 settings=xmlimport.NULL_SETTINGS, info=None):
        super(IndexHandler, self).__init__(parent, parent_handler,
                                           settings, info)
        self._data = []
    
    def startElementNS(self, name, qname, attrs):
        node = self.parent()
        child = node.ownerDocument.createElement('index')
        node.appendChild(child)
        self.setResult(child)

    def characters(self, data):
        self._data.append(data)
        
    def endElementNS(self, name, qname):
        self.result().setAttribute('name', ''.join(self._data))
        
class BrHandler(htmlsubset.SubsetHandler):
    parsed_name = 'br'
    
    def startElementNS(self, name, qname, attrs):
        node = self.parent()
        child = node.ownerDocument.createElement('br')
        node.appendChild(child)
        self.setResult(child)

PARAGRAPH_SUBSET = createParagraphSubset()
