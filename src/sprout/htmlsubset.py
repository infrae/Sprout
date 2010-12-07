"""
This module is intended for parsing chaotic HTML-ish user input into a
sane DOM tree. It can be used to define subsets of HTML (or subsets
with expansions) that can be used in comment features of websites or,
in particular, the Silva forms based editor.

It is expected the user can make mistakes like not properly matching
tags, not opening or closing a tag, or malformed tags. The parser in
that case 'does its best' to produce a sane DOM tree.
"""

from sprout import tagfilter
from sprout.saxext import xmlimport, html2sax, collapser
try:
    set
except NameError:
    from sets import Set as set


class Subset:
    """A subset consists of known elements.
    """
    def __init__(self):
        self._elements = {}
        self._tagfilter = tagfilter.TagFilter(html_entities=True)
        self._importer_dict = {}

    def registerElement(self, element):
        self._elements[element.getName()] = element
        self._tagfilter.registerElement(
            element.getName(),
            element.getRequiredAttributes(),
            element.getOptionalAttributes())
        self._importer_dict[(None, element.getName())] = element.getHandler()

    def getImporter(self):
        return xmlimport.Importer(self._importer_dict)

    def isAllowed(self, container_name, name):
        element = self._elements.get(container_name)
        if element is None:
            return False
        return element.isAllowed(name)

    def filteredParse(self, html, result):
        html = self._tagfilter.escapeNonElements(html)
        return self.parse(html, result)

    def parse(self, html, result):
        importer = self.getImporter()
        handler = importer.importHandler(SubsetSettings(self), result)
        collapsing_handler = collapser.CollapsingHandler(handler)
        collapsing_handler.startElementNS((None, 'block'), None, {})
        html2sax.saxify(html, collapsing_handler)
        collapsing_handler.endElementNS((None, 'block'), None)
        return handler.result()

class Element:
    """A single element in a subset.
    """

    def __init__(self, name, required_attributes, optional_attributes,
                 subelements, handler):
        self._name = name
        self._required_attributes = required_attributes
        self._optional_attributes = optional_attributes
        self._subelements = set(subelements)
        self._handler = handler

    def getName(self):
        return self._name

    def getRequiredAttributes(self):
        return self._required_attributes

    def getOptionalAttributes(self):
        return self._optional_attributes

    def getHandler(self):
        return self._handler

    def isAllowed(self, name):
        return name in self._subelements

class SubsetSettings(xmlimport.BaseSettings):
    def __init__(self, subset):
        super(SubsetSettings, self).__init__(ignore_not_allowed=True)
        self._subset = subset

    def isElementAllowed(self, container_name, name):
        return self._subset.isAllowed(container_name, name)

class SubsetHandler(xmlimport.BaseHandler):
    """A handler that ignores any elements not in subset.
    """
    def isElementAllowed(self, name):
        return self.settings().isElementAllowed(self.parsed_name, name[1])

class BlockHandler(SubsetHandler):
    parsed_name = 'block'

    def characters(self, data):
        node = self.parent()
        doc = node.ownerDocument
        node.appendChild(doc.createTextNode(data))
