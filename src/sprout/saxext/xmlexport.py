"""
An XML exporter based on SAX events.
"""
from StringIO import StringIO
from xml.sax import saxutils

class XMLSourceRegistry:
    """Registers Content Types to XML Sources that generate Sax-events.
    """
    def __init__(self):
        self._mapping = {}
        self._fallback = None
    
    def registerXMLSource(self, klass, xml_source):
        self._mapping[klass] = xml_source
        
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
        reader = saxutils.XMLGenerator(file, 'UTF-8')
        self.xmlToSax(context, reader, settings)

    def xmlToSax(self, context, reader, settings=None):
        self.getXMLSource(context, reader, settings).xmlToSax()
    
class BaseXMLSource:
    def __init__(self, context, registry, reader, settings):
        self.context = context
        self._registry = registry
        self._reader = reader
        self._settings = settings
        
    def xmlToSax(self):
        """Export self.context to XML Sax-events 
        """
        self._reader.startPrefixMapping(None, self.ns_default)
        if self._settings is not None:
            mappings = self._settings.getMappings()
            for prefix in mappings.keys():
                self._reader.startPrefixMapping(prefix, mappings[prefix])
        self._sax()

    def getXMLSource(self, context):
        """Give the XML source for a particular context object.
        """
        return self._registry.getXMLSource(
            context, self._reader, self._settings)
    
    def _sax(self):
        """To be overridden in subclasses
        """
        raise NotImplemented

    def _startElementNS(self, ns, name, attrs=None):
        """Starts a named XML element in the provided namespace with
        optional attributes
        """
        d = {}
        
        if attrs is not None:
            for key, value in attrs.items():
                d[(None, key)] = value
        self._reader.startElementNS(
            (ns, name),
            None,
            d)
        
    def _endElementNS(self, ns, name):
        """Ends a named element in the provided namespace
        """
        self._reader.endElementNS(
            (ns, name),
            None)
        
    def _startElement(self, name, attrs=None):
        """Starts a named XML element in the default namespace with optional
        attributes
        """
        self._startElementNS(self.ns_default, name, attrs)
        
    def _endElement(self, name):
        """Ends a named element in the default namespace
        """
        self._endElementNS(self.ns_default, name)
