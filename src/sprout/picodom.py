"""
A simplistic, tiny DOM subset.

Useful mostly when unit testing code that needs to run against a wider
DOM, but probably only compatible with ParsedXML as that is the aim.

It should have just enough API to build a simple DOM tree, which can then
be displayed as XML using 'toXML'.
"""

from xml.sax.saxutils import escape, quoteattr


class DOMImplementation:

    def createDocument(self, namespaceURI, qualifiedName):
        doc = Document()
        doc.documentElement = doc.createElement(qualifiedName)
        return doc


def getDOMImplementation():
    return DOMImplementation()


class Document:

    def __init__(self):
        self.documentElement = None
        self.ownerDocument = None

    def createElement(self, name):
        return ElementNode(name, self)

    def createTextNode(self, data):
        return TextNode(data, self)

    def toXML(self):
        return self.documentElement.toXML()


class ElementNode:

    def __init__(self, name, ownerDocument):
        self.nodeName = name
        self.ownerDocument = ownerDocument
        self.childNodes = []
        self.attributes = {}

    def setAttribute(self, name, value):
        self.attributes[name] = value

    def appendChild(self, child):
        self.childNodes.append(child)
        return child

    def toXML(self):
        contents = []
        attrs = []
        keys = self.attributes.keys()
        keys.sort()
        for key in keys:
            value = self.attributes[key]
            attrs.append("%s=%s" % (key, quoteattr(value)))
        for childNode in self.childNodes:
            contents.append(childNode.toXML())
        tag = '<%s' % self.nodeName
        if attrs:
            tag += ' '
            tag += ' '.join(attrs)
            tag += '>'
        else:
            tag += '>'
        return '%s%s</%s>' % (
            tag, ''.join(contents), self.nodeName)


class TextNode:

    def __init__(self, data, ownerDocument):
        self.data = data
        self.ownerDocument = ownerDocument

    def toXML(self):
        return escape(self.data)
