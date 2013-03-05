# -*- coding: utf-8 -*-
# Copyright (c) 2013  Infrae. All rights reserved.
# See also LICENSE.txt
"""
An XML exporter based on SAX events.
"""
import tempfile
import os

from grokcore import component
from zope.component import queryMultiAdapter
from zope.interface import implements, Interface

from sprout.saxext.generator import XMLGenerator
from sprout.saxext.interfaces import IExporterRegistry, IXMLProducer
from sprout.saxext.utils import Options


class XMLExportError(Exception):
    pass


class ExporterTemporaryResult(object):
    """Exporter temporary result in a temporary file. Large exports
    cannot be conained in memory, we have to use a file for it.
    """
    __slots__ = ('filename', 'file')

    def __init__(self, handle, filename):
        self.filename = filename
        self.file = os.fdopen(handle, 'w+')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def read(self, *args):
        return self.file.read(*args)

    def seek(self, *args):
        return self.file.seek(*args)

    def close(self):
        # Remove the temporary file when it is closed.
        self.file.close()
        os.remove(self.filename)

class Exporter(object):
    """Export objects to XML, using SAX.
    """
    implements(IExporterRegistry)

    def __init__(self, default_namespace, generator=None):
        self._defaults = {'as_document': True, 'encoding': 'utf-8'}
        self._mapping = {}
        self._fallback = None
        self._default_namespace = default_namespace
        self._namespaces = {}
        if generator is None:
            generator = XMLGenerator
        self._generator = generator

    # MANIPULATORS

    def registerOption(self, name, default=None):
        """Register an option that can be queried by producer later
        on.

        name - Name of the existing option. If provided in the options
        dictionary it will be returned, otherwise None will be.
        """
        self._defaults[name] = default

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

    def exportToSax(self, exported, handler, options=None, extra=None):
        """Export to sax events on handler.

        exported - the object to convert to XML
        handler - a SAX event handler that events will be sent to
        settings - optionally a settings object to configure export
        """
        options = self.getOptions(options)
        if options.as_document:
            handler.startDocument()
        if self._default_namespace is not None:
            handler.startPrefixMapping(None, self._default_namespace)
        for prefix, uri in self._namespaces.items():
            handler.startPrefixMapping(prefix, uri)
        configuration = ExportConfiguration(
            self, exported, handler, options, extra)
        producer = configuration.getProducer(exported)
        producer.sax()
        if options.as_document:
            handler.endDocument()

    def exportToStream(self, exported, file, options=None, extra=None):
        """Export object by writing XML to file object.

        exported - the object to convert to XML
        file - a Python file object to write to
        settings - optionally a settings object to configure export
        """
        options = self.getOptions(options)
        handler = self._generator(file, options.encoding)
        self.exportToSax(exported, handler, options, extra)

    def exportToTemporary(self, exported, options=None, extra=None):
        """Export the object into a temporary file.
        """
        result = ExporterTemporaryResult(*tempfile.mkstemp('.xml'))
        try:
            self.exportToStream(exported, result.file, options, extra)
        except:
            result.close()
            raise
        result.seek(0)
        return result

    def exportToString(self, exported, options=None, extra=None):
        """Export object as XML string.

        obj - the object to convert to XML
        settings - optionally a settings object to configure export

        Returns XML string.
        """
        with self.exportToTemporary(exported, options, extra) as output:
            return output.read()

    def getDefaultNamespace(self):
        """The default namespace for the XML generated by this exporter.
        """
        return self._default_namespace

    def getNamespaces(self, prefix=False):
        if prefix:
            return self._namespaces.items()
        return self._namespaces.values()

    def getOptions(self, options):
        """Return the set of possible options.
        """
        if isinstance(options, Options):
            return options
        return Options(options, self._defaults.copy())


class ExportConfiguration(object):
    implements(Interface)

    def __init__(self, registry, exported, handler, options, extra):
        self._exported = exported
        self._options = options
        self._extra = extra
        self.handler = handler
        self.registry = registry

    def getExported(self):
        # Return exported object.
        return self._exported

    def getExtra(self):
        return self._extra

    def getOptions(self):
        return self._options

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

    def getExported(self):
        return self.configuration.getExported()

    def getExtra(self):
        return self.configuration.getExtra()

    def getOptions(self):
        return self.configuration.getOptions()

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

    def startPrefixMapping(self, prefix, url):
        self.handler.startPrefixMapping(prefix, url)

    def endPrefixMapping(self, prefix):
        self.handler.endPrefixMapping(prefix)

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

    def subsax(self, context, **kw):
        """Generate SAX events for context object.

        context - the context object (typically sub oject) to generate SAX
                  events for.
        """
        self.configuration.getProducer(context).sax(**kw)


class Producer(BaseProducer, component.MultiAdapter):
    component.provides(IXMLProducer)
    component.baseclass()
