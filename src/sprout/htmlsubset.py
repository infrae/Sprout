"""
This module is intended for parsing chaotic HTML-ish user input into a
sane DOM tree. It can be used to define subsets of HTML (or subsets
with expansions) that can be used in comment features of websites or,
in particular, the Silva forms based editor.

It is expected the user can make mistakes like not properly matching
tags, not opening or closing a tag, or malformed tags. The parser in
that case 'does its best' to produce a sane DOM tree.
"""

from sprout.saxext import xmlimport, html2sax, collapser
import sets

class Element:
    def __init__(self, name, required_attributes, optional_attributes,
                 subelements):
        self._name = name
        self._required_attributes = required_attributes
        self._optional_attributes = optional_attributes
        self._subelements = sets.Set(subelements)

    def getName(self):
        return self._name
    
    def isAllowed(self, name):
        return name in self._subelements

def createTagFilter(elements):
    tf = tagfilter.TagFilter(html_entities=True)
    for element in elements:
        tf.registerElement(
            element.getName(),
            element.getRequiredAttributes(),
            element.getOptionalAttributes())
    return tf

def createParagraphImporter(elements):
    

    for parsed_name, tree_name in MARKUP_TEXT_TRANSLATION.items():
        d[(None, parsed_name)] = markupTextHandlerClass(parsed_name, tree_name)
    d[(None, 'a')] = AHandler
    d[(None, 'index')] = IndexHandler
    d[(None, 'br')] = BrHandler
    return xmlimport.Importer(d)

def getParagraphElements():
    elements = []
    for name in MARKUP_TEXT:
        name = MARKUP_TEXT_TRANSLATION_REVERSED[name]
        elements.append(Element(name, [], [], MARKUP_TEXT_BR_REVERSED))
    elements.append(Element('a', ['href'], [], MARKUP_TEXT_BR_REVERSED))
    elements.append(Element('index', [], [], []))
    elements.append(Element('br', [], [], []))
    return elements

MARKUP_BASE = ['em', 'super', 'sub']
MARKUP_LINK = ['link', 'index']
MARKUP_TEXT = MARKUP_BASE + ['strong', 'underline']
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

MARKUP_TEXT_TRANSLATION_REVERSED = {}
for key, value in MARKUP_TEXT_TRANSLATION.items():
    MARKUP_TEXT_TRANSLATION_REVERSED[value] = key

MARKUP_TEXT_BR_REVERSED = []
for name in MARKUP_TEXT:
    MARKUP_TEXT_BR_REVERSED.append(MARKUP_TEXT_TRANSLATION_REVERSED[name])

class SubsetSettings(xmlimport.BaseSettings):
    def __init__(self, elements):
        super(SubsetSettings, self).__init__(ignore_not_allowed=True)
        elements_dict = {}
        for element in elements:
            elements_dict[element.getName()] = element
        self._elements = elements_dict

    def isElementAllowed(self, name):
        subset = self._elements.get(name)
        if subset is None:
            return False
        return subset.isAllowed(name)
    
class BlockHandler(xmlimport.BaseHandler):
    def characters(self, data):
        node = self.parent()
        doc = node.ownerDocument
        node.appendChild(doc.createTextNode(data))

class SubsetHandler(xmlimport.BaseHandler):
    """A handler that ignores any elements not in subset.
    """
    def isElementAllowed(self, name):
        return self.settings().isElementAllowed(name[1])
    
class MarkupTextHandler(SubsetHandler):
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

class AHandler(xmlimport.BaseHandler):
    def isElementAllowed(self, name):
        try:
            return MARKUP_TEXT_TRANSLATION[name[1]] in MARKUP_TEXT_BR
        except KeyError:
            return False
        
    def startElementNS(self, name, qname, attrs):
        node = self.parent()
        child = node.ownerDocument.createElement('link')
        child.setAttribute('url', attrs[(None, 'href')])
        node.appendChild(child)
        self.setResult(child)

    def characters(self, data):
        node = self.result()
        node.appendChild(node.ownerDocument.createTextNode(data))

class IndexHandler(xmlimport.BaseHandler):
    def __init__(self, parent, parent_handler,
                 settings=xmlimport.NULL_SETTINGS, info=None):
        super(IndexHandler, self).__init__(parent, parent_handler,
                                           settings, info)
        self._data = []
        
    def isElementAllowed(self, name):
        return False
    
    def startElementNS(self, name, qname, attrs):
        node = self.parent()
        child = node.ownerDocument.createElement('index')
        node.appendChild(child)
        self.setResult(child)

    def characters(self, data):
        self._data.append(data)
        
    def endElementNS(self, name, qname):
        self.result().setAttribute('name', ''.join(self._data))
        
class BrHandler(xmlimport.BaseHandler):
    def isElementAllowed(self, name):
        return False
    
    def startElementNS(self, name, qname, attrs):
        node = self.parent()
        child = node.ownerDocument.createElement('br')
        node.appendChild(child)
        self.setResult(child)


def parse(html, importer, result):
    d = getParagraphElements()
    handler = importer.importHandler(SubsetSettings(d), result)
    collapsing_handler = collapser.CollapsingHandler(handler)
    collapsing_handler.startElementNS((None, 'block'), None, {})
    html2sax.saxify(html, collapsing_handler)
    collapsing_handler.endElementNS((None, 'block'), None)
    return handler.result()

def createImporter():
    # XXX 'block' tag is only needed to provide fake element events
    # XXX but it could be misused in the text now..
    d = {(None, 'block'): BlockHandler}
    for parsed_name, tree_name in MARKUP_TEXT_TRANSLATION.items():
        d[(None, parsed_name)] = markupTextHandlerClass(parsed_name, tree_name)
    d[(None, 'a')] = AHandler
    d[(None, 'index')] = IndexHandler
    d[(None, 'br')] = BrHandler
    return xmlimport.Importer(d)

