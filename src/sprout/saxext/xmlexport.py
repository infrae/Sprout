"""
An XML exporter based on SAX events.
"""
from StringIO import StringIO
from sprout.saxext.generator import XMLGenerator

class XMLExportError(Exception):
    pass

class BaseSettings:
    """Base class of settings sent to XML generation.

    Subclass this for custom settings objects.
    """
    def __init__(self, asDocument=True, outputEncoding='utf-8'):
        self._asDocument = asDocument
        self._outputEncoding = outputEncoding
        
    def asDocument(self):
        """Export XML as document with full prolog.
        """
        return self._asDocument
    
    def outputEncoding(self):
        """Encoding the document will be output as.
        """
        return self._outputEncoding

class BaseData:
    """Base class of data that can be set or changed by the export.
    
    Subclass this for custom data objects.
    """
    
# null settings contains the default settings
NULL_SETTINGS = BaseSettings()

class Exporter:
    """Export objects to XML, using SAX.
    """
    def __init__(self, default_namespace, generator=None):
        self._mapping = {}
        self._fallback = None
        self._default_namespace = default_namespace
        self._namespaces = {}
        if generator is None:
            generator = XMLGenerator
        self._generator = generator

    # MANIPULATORS
    
    def registerProducer(self, klass, producer_factory):
        """Register an XML producer factory for a class.

        klass - the class of the object we want to serialize as XML
        producer_factory - the class of the SAX event producer for it
                           (subclass of BaseProducer)
        """
        self._mapping[klass] = producer_factory
        
    def registerNamespace(self, prefix, uri):
        """Register a namespace.

        prefix - prefix for namespace as will be shown in the XML
        uri - namespace URI
        """
        self._namespaces[prefix] = uri

    # ACCESSORS

    def exportToSax(self, obj, handler, settings=NULL_SETTINGS, data=None):
        """Export to sax events on handler.
        
        obj - the object to convert to XML
        handler - a SAX event handler that events will be sent to
        settings - optionally a settings object to configure export
        """
        if settings.asDocument():
            handler.startDocument()
        if self._default_namespace is not None:
            handler.startPrefixMapping(None, self._default_namespace)
        for prefix, uri in self._namespaces.items():
            handler.startPrefixMapping(prefix, uri)
        self._getProducer(obj, handler, settings, data).sax()
        if settings.asDocument():
            handler.endDocument()

    def exportToFile(self, obj, file, settings=NULL_SETTINGS, data=None):
        """Export object by writing XML to file object.

        obj - the object to convert to XML
        file - a Python file object to write to
        settings - optionally a settings object to configure export
        """
        handler = self._generator(file, settings.outputEncoding())
        self.exportToSax(obj, handler, settings, data)

    def exportToString(self, obj, settings=NULL_SETTINGS, data=None):
        """Export object as XML string.

        obj - the object to convert to XML
        settings - optionally a settings object to configure export

        Returns XML string.
        """
        f = StringIO()
        self.exportToFile(obj, f, settings, data)
        result = f.getvalue()
        f.close()
        return result

    def getDefaultNamespace(self):
        """The default namespace for the XML generated by this exporter.
        """
        return self._default_namespace

    # PRIVATE

    def _getProducer(self, context, handler, settings, data):
        """Create SAX event producer for context, handler, settings.

        context - the object to represent as XML
        handler - a handler of SAX events
        settings - settings object configuring export
        """
        class_ = context.__class__
        producer_factory = self._mapping.get(class_, None)
        if producer_factory is None:
            raise XMLExportError, ("Cannot find SAX event producer for: %s" %
                                   class_)
        return producer_factory(context, self, handler, settings, data)

class BaseProducer:
    """Base class for SAX event producers.

    Subclass this to create a producer generating SAX events.

    Override the sax method in your subclass. The sax method
    can use the following attributes and methods:

    context - the object being exported.
    handler - the SAX handler object, you can send arbitrary SAX events to it,
             such as startElementNS, endElementNS, characters, etc.
    startElement, endElement - convenient ways to generate element events
                               in default namespace.
    startElementNS, endElementNs - convenient way to generate element
                                   events in namespace.

    getProducer - to retrieve a producer for a sub object.
    subsax - to generate SAX events for a sub object
    """
    def __init__(self, context, exporter, handler, settings, data):
        self.context = context
        self._exporter = exporter
        self.handler = handler
        self._settings = settings
        self._export_data = data
        
    def sax(self):
        """To be overridden in subclasses
        """
        raise NotImplemented

    def startElementNS(self, ns, name, attrs=None):
        """Start element event in the provided namespace.

        attrs - Optionally an attribute dictionary can be passed. This
        dictionary is a mapping from attribute names to attribute
        values. If an attribute name is a string, the attribute will
        be in no namespace (no namespace prefix). If the attribute
        name is a tuple, it must contain the namespace URI as the
        first element, the namespace name as the second element.
        """
        d = {}
        
        if attrs is not None:
            for key, value in attrs.items():
                # keep namespaced attributes
                if isinstance(key, tuple):
                    d[key] = value
                else:
                    d[(None, key)] = value
        self.handler.startElementNS(
            (ns, name),
            None,
            d)
        
    def endElementNS(self, ns, name):
        """End element event in the provided namespace.
        """
        self.handler.endElementNS(
            (ns, name),
            None)
    
    def startElement(self, name, attrs=None):
        """Start element event in the default namespace.

        attrs - see startElementNS.
        """
        self.startElementNS(self._exporter.getDefaultNamespace(), name, attrs)
        
    def endElement(self, name):
        """End element event in the default namespace.
        """
        self.endElementNS(self._exporter.getDefaultNamespace(), name)

    def getProducer(self, context):
        """Give the producer for a particular context object.

        context - the context object to get producer for.
        """
        return self._exporter._getProducer(
            context, self.handler, self._settings, self._export_data)

    def subsax(self, context):
        """Generate SAX events for context object.

        context - the context object (typically sub oject) to generate SAX
                  events for.
        """
        self.getProducer(context).sax()
                
