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

class Subset:
    def __init__(self):
        pass

    def registerElement(self, name, required_attributes, optional_attributes,
                        text_allowed, subset):
        """Register an element for a subset.

        name - name of element
        required_attributes - sequence with names of required attributes
        optional_attributes - sequence with names of optional attributes
        text_allowed - whether element is allowed to contain any text
        subset - optional subset of elements that can be contained
        """
        pass

    def filterTags(self, text):
        """Given text, filter out unrecognized tags by quoting them literally.
        """
        
    def getParseableElementNames(self):
        """Get a list of all elements in this subset that can be parsed.

        Any elements which cannot be parsed is quoted literally in the output.
        """

    def getIgnoreOverrides(self):
        """Get an overrides dictionary with all elements that should be ignored.
        """
        result = {}
        allowed_element_names = self.getParseableElementNames()
        for name in self.getMainSubset().getParseableElementNames():
            if name in allowed_element_names:
                continue
            result[(None, name)] = IgnoreHandler
        return result
    
        
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

class BlockHandler(xmlimport.BaseHandler):
    def characters(self, data):
        node = self.parent()
        doc = node.ownerDocument
        node.appendChild(doc.createTextNode(data))

class MarkupTextHandler(xmlimport.BaseHandler):
    def startElementNS(self, name, qname, attrs):
        node = self.parent()
        child = node.ownerDocument.createElement(self.name)
        node.appendChild(child)
        self.setResult(child)
        
    def characters(self, data):
        node = self.result()
        node.appendChild(node.ownerDocument.createTextNode(data))

def markupTextHandlerClass(name):
    """Construct subclass able to handle element of name.
    """
    return type('%s_handler_class' % name, (MarkupTextHandler,),
                {'name': name})

class SubsetHandler(xmlimport.BaseHandler):
    """A handler that ignores any elements not in subset.
    """
    def getOverrides(self):
        return self.settings().getSubset(self.tagName).getIgnoreOverrides()
        
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
    def isElementAllowed(self, name):
        return False
    
    def startElementNS(self, name, qname, attrs):
        node = self.parent()
        child = node.ownerDocument.createElement('index')
        node.appendChild(child)
        self.setResult(child)

    def characters(self, data):
        node = self.result()
        node.setAttribute('name', data)

class BrHandler(xmlimport.BaseHandler):
    def isElementAllowed(self, name):
        return False
    
    def startElementNS(self, name, qname, attrs):
        node = self.parent()
        child = node.ownerDocument.createElement('br')
        node.appendChild(child)
        self.setResult(child)


def parse(html, importer, result):
    handler = importer.importHandler(xmlimport.IGNORE_SETTINGS, result)
    # any text has to between tags
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
        d[(None, parsed_name)] = markupTextHandlerClass(tree_name)
    d[(None, 'a')] = AHandler
    d[(None, 'index')] = IndexHandler
    d[(None, 'br')] = BrHandler
    return xmlimport.Importer(d)
