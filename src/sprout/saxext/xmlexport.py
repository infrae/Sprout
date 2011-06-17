"""
An XML exporter based on SAX events.
"""
from StringIO import StringIO

from grokcore import component
from zope.component import queryMultiAdapter
from zope.interface import implements, Interface

from sprout.saxext.generator import XMLGenerator
from sprout.saxext.interfaces import IExporterRegistry, IXMLProducer


class XMLExportError(Exception):
    pass


class BaseSettings(object):
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


# null settings contains the default settings
NULL_SETTINGS = BaseSettings()


class Exporter(object):
    """Export objects to XML, using SAX.
    """
    implements(IExporterRegistry)

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

    def registerFallbackProducer(self, producer_factory):
        """Register a fallback XML producer. If a fallback producer is
        registered, it will be used to produce the XML for every class that
        has no producer of its own registered.

        producer_factory - the class of the SAX event producer
                           (subclass of BaseProducer)
        """
        self._fallback = producer_factory

    def registerNamespace(self, prefix, uri):
        """Register a namespace.

        prefix - prefix for namespace as will be shown in the XML
        uri - namespace URI
        """
        self._namespaces[prefix] = uri

    # ACCESSORS

    def exportToSax(self, obj, handler, settings=NULL_SETTINGS, info=None):
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
        producer = ExportConfiguration(
            self, handler, settings, info).getProducer(obj)
        producer.sax()
        if settings.asDocument():
            handler.endDocument()

    def exportToFile(self, obj, file, settings=NULL_SETTINGS, info=None):
        """Export object by writing XML to file object.

        obj - the object to convert to XML
        file - a Python file object to write to
        settings - optionally a settings object to configure export
        """
        handler = self._generator(file, settings.outputEncoding())
        self.exportToSax(obj, handler, settings, info)

    def exportToString(self, obj, settings=NULL_SETTINGS, info=None):
        """Export object as XML string.

        obj - the object to convert to XML
        settings - optionally a settings object to configure export

        Returns XML string.
        """
        f = StringIO()
        self.exportToFile(obj, f, settings, info)
        result = f.getvalue()
        f.close()
        return result

    def getDefaultNamespace(self):
        """The default namespace for the XML generated by this exporter.
        """
        return self._default_namespace


class ExportConfiguration(object):
    implements(Interface)

    def __init__(self, registry, handler, settings, info):
        self._settings = settings
        self._info = info
        self.handler = handler
        self.registry = registry

    def getInfo(self):
        return self._info

    def getSettings(self):
        return self._settings

    def getDefaultNamespace(self):
        return self.registry.getDefaultNamespace()

    def getProducer(self, context):
        """Create SAX event producer for context, handler, settings.

        context - the object to represent as XML
        handler - a handler of SAX events
        settings - settings object configuring export
        """
        producer = queryMultiAdapter((context, self), IXMLProducer)
        if producer is None:
            cls = context.__class__
            factory = self.registry._mapping.get(cls, None)
            if factory is None:
                if self.registry._fallback is None:
                    raise XMLExportError(
                        "Cannot find SAX event producer for: %s" %
                        cls)
                else:
                    factory = self.registry._fallback
            return factory(context, self)
        return producer


class BaseProducer(object):
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
    implements(IXMLProducer)

    def __init__(self, context, configuration):
        self.context = context
        self.handler = configuration.handler
        self.configuration = configuration

    def getInfo(self):
        return self.configuration.getInfo()

    def getSettings(self):
        return self.configuration.getSettings()

    def sax(self):
        """To be overridden in subclasses
        """
        raise NotImplemented

    def characters(self, content):
        self.handler.characters(content)

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
            (ns, name), None, d)

    def endElementNS(self, ns, name):
        """End element event in the provided namespace.
        """
        self.handler.endElementNS(
            (ns, name), None)

    def startElement(self, name, attrs=None):
        """Start element event in the default namespace.

        attrs - see startElementNS.
        """
        self.startElementNS(
            self.configuration.getDefaultNamespace(), name, attrs)

    def endElement(self, name):
        """End element event in the default namespace.
        """
        self.endElementNS(
            self.configuration.getDefaultNamespace(), name)

    def subsax(self, context):
        """Generate SAX events for context object.

        context - the context object (typically sub oject) to generate SAX
                  events for.
        """
        self.configuration.getProducer(context).sax()


class Producer(BaseProducer, component.MultiAdapter):
    component.provides(IXMLProducer)
    component.baseclass()
