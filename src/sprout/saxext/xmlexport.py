"""
An XML exporter based on SAX events.
"""
from StringIO import StringIO
from xml.sax import saxutils

class XMLSourceRegistry:
    """Registers Content Types to XML Sources that generate Sax-events.
    """
    def __init__(self, default_namespace):
        self._mapping = {}
        self._fallback = None
        self._default_namespace = default_namespace
        self._namespaces = {}
        
    def registerXMLSource(self, klass, xml_source):
        self._mapping[klass] = xml_source

    def registerNamespace(self, prefix, uri):
        self._namespaces[prefix] = uri
        
    def getXMLSource(self, context, reader, settings):
        class_ = context.__class__
        xmlsource = self._mapping.get(class_, None)
        if xmlsource is None:
            raise XMLExportError, "Cannot find source for: %s" % class_
        return xmlsource(context, self, reader, settings)

    def xmlToString(self, context, settings=None):
        f = StringIO()
        self.xmlToFile(f, context, settings)
        result = f.getvalue()
        f.close()
        return result

    def xmlToFile(self, file, context, settings=None):
        reader = saxutils.XMLGenerator(file, 'utf-8')
        self.xmlToSax(context, reader, settings)

    def xmlToSax(self, context, reader, settings=None):
        reader.startDocument()
        reader.startPrefixMapping(None, self._default_namespace)
        for prefix, uri in self._namespaces.items():
            reader.startPrefixMapping(prefix, uri)
        self.getXMLSource(context, reader, settings).sax()
        reader.endDocument()
        
    def getDefaultNamespace(self):
        return self._default_namespace
    
class BaseXMLSource:
    def __init__(self, context, registry, reader, settings):
        self.context = context
        self._registry = registry
        self.reader = reader
        self._settings = settings
        
    def getXMLSource(self, context):
        """Give the XML source for a particular context object.
        """
        return self._registry.getXMLSource(
            context, self.reader, self._settings)
    
    def sax(self):
        """To be overridden in subclasses
        """
        raise NotImplemented

    def startElementNS(self, ns, name, attrs=None):
        """Starts a named XML element in the provided namespace with
        optional attributes
        """
        d = {}
        
        if attrs is not None:
            for key, value in attrs.items():
                # keep namespaced attributes
                if isinstance(key, tuple):
                    d[key] = value
                else:
                    d[(None, key)] = value

        self.reader.startElementNS(
            (ns, name),
            None,
            d)
        
    def endElementNS(self, ns, name):
        """Ends a named element in the provided namespace
        """
        self.reader.endElementNS(
            (ns, name),
            None)

    def getDefaultNamespace(self):
        return self._registry.getDefaultNamespace()
    
    def startElement(self, name, attrs=None):
        """Starts a named XML element in the default namespace with optional
        attributes
        """
        self.startElementNS(self.getDefaultNamespace(), name, attrs)
        
    def endElement(self, name):
        """Ends a named element in the default namespace
        """
        self.endElementNS(self.getDefaultNamespace(), name)
