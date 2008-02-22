"""Particular HTMLish subsets as used by Silva.
"""

from sprout import htmlsubset
from sprout.saxext import xmlimport

MARKUP_BASE = ['i', 'sup', 'sub']
MARKUP_LINK = ['a', 'index']
MARKUP_TEXT = MARKUP_BASE + ['b', 'u', 'abbr', 'acronym']
MARKUP_TEXT_BR = MARKUP_TEXT + ['br']
MARKUP = MARKUP_TEXT_BR + MARKUP_LINK
MARKUP_HEADING = MARKUP_BASE + MARKUP_LINK

MARKUP_TEXT_TRANSLATION = {
    'i': 'em',
    'sup': 'super',
    'sub': 'sub',
    'b': 'strong',    
    'u' : 'underline',
    'abbr' : 'abbreviation',
    'acronym' : 'acronym',
    }

class SilvaParagraphSubset(htmlsubset.Subset):
    """A subset consists of known elements.
    """
    def filteredParse(self, html, result):
        html = html.replace('\r\n', '<br/>')
        html = html.replace('\n', '<br/>')
        return htmlsubset.Subset.filteredParse(self, html, result)
        
def createParagraphSubset():
    subset = SilvaParagraphSubset()
    for name in MARKUP_TEXT:
        handler = markupTextHandlerClass(name, MARKUP_TEXT_TRANSLATION[name])
        element = htmlsubset.Element(name, [], [], MARKUP, handler)
        subset.registerElement(element)
    subset.registerElement(
        htmlsubset.Element('a', ['href'], ['target','title'],
                           MARKUP_TEXT_BR, AHandler))
    subset.registerElement(
        htmlsubset.Element('abbr', [], ['title'],
                           MARKUP_TEXT_BR, AbbrHandler))
    subset.registerElement(
        htmlsubset.Element('acronym', [], ['title'],
                           MARKUP_TEXT_BR, AcronymHandler))
    subset.registerElement(
        htmlsubset.Element('index', ['name'], ['title'], [], IndexHandler))
    subset.registerElement(
        htmlsubset.Element('br', [], [], [], BrHandler))
    # 'block' tag is used to produce fake surrounding tag, real one will
    # be 'p'. Need to register allowed elements for it
    subset.registerElement(
        htmlsubset.Element('block', [], [], MARKUP,
                           htmlsubset.BlockHandler))
    return subset

def createHeadingSubset():
    subset = htmlsubset.Subset()
    for name in MARKUP_BASE:
        handler = markupTextHandlerClass(name, MARKUP_TEXT_TRANSLATION[name])
        element = htmlsubset.Element(name, [], [], MARKUP_HEADING, handler)
        subset.registerElement(element)
    subset.registerElement(
        htmlsubset.Element('a', ['href'], ['target','title'],
                           MARKUP_BASE, AHandler))
    subset.registerElement(
        htmlsubset.Element('index', [], [], [], IndexHandler))
    subset.registerElement(
        htmlsubset.Element('block', [], [], MARKUP_HEADING,
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
        if attrs.has_key((None, 'target')):
            child.setAttribute('target', attrs[(None, 'target')])
        node.appendChild(child)
        self.setResult(child)

    def characters(self, data):
        node = self.result()
        node.appendChild(node.ownerDocument.createTextNode(data))

class AbbrHandler(htmlsubset.SubsetHandler):
    parsed_name = 'abbr'

    def startElementNS(self, name, qname, attrs):
        node = self.parent()
        child = node.ownerDocument.createElement('abbr')
        if attrs.has_key((None, 'title')):
            child.setAttribute('title', attrs[(None, 'title')])
        node.appendChild(child)
        self.setResult(child)

    def characters(self, data):
        node = self.result()
        node.appendChild(node.ownerDocument.createTextNode(data))

class AcronymHandler(htmlsubset.SubsetHandler):
    parsed_name = 'acronym'

    def startElementNS(self, name, qname, attrs):
        node = self.parent()
        child = node.ownerDocument.createElement('acronym')
        if attrs.has_key((None, 'title')):
            child.setAttribute('title', attrs[(None, 'title')])
        node.appendChild(child)
        self.setResult(child)

    def characters(self, data):
        node = self.result()
        node.appendChild(node.ownerDocument.createTextNode(data))

class IndexHandler(htmlsubset.SubsetHandler):
    parsed_name = 'index'
    
    def startElementNS(self, name, qname, attrs):
        node = self.parent()
        child = node.ownerDocument.createElement('index')
        child.setAttribute('name', attrs[(None, 'name')])
        if attrs.has_key((None, 'title')):
            child.setAttribute('title', attrs[(None, 'title')])
        node.appendChild(child)
        self.setResult(child)
        
class BrHandler(htmlsubset.SubsetHandler):
    parsed_name = 'br'
    
    def startElementNS(self, name, qname, attrs):
        node = self.parent()
        child = node.ownerDocument.createElement('br')
        node.appendChild(child)
        self.setResult(child)

PARAGRAPH_SUBSET = createParagraphSubset()
HEADING_SUBSET = createHeadingSubset()
