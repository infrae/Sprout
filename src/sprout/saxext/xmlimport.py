# -*- coding: utf-8 -*-
# Copyright (c) 2013  Infrae. All rights reserved.
# See also LICENSE.txt
"""
An XML importer based on layered SAX handlers.

Elements can have their own sax handlers associated with them, which
handle all events inside those elements.
"""
import io
import xml.sax
import xml.sax.handler

from sprout.saxext.utils import Options


class XMLImportError(Exception):
    pass


class NotAllowedError(XMLImportError):
    """Something found that is not allowed.
    """


class ElementNotAllowedError(NotAllowedError):
    """Element is found that is not allowed.
    """


class TextNotAllowedError(NotAllowedError):
    """Text is found that is not allowed.
    """

class MappingStack(object):
    """A runtime stack for content handlers

    It wraps a Importer mapping and provides overrides.
    """

    def __init__(self, mapping):
        """Initialize handlers/content mapping from the importer
        """
        self.__mapping = mapping
        self.__stack = []

    def getHandler(self, element):
        """Retrieve handler for a particular element (ns, name) tuple.
        """
        try:
            return self.__mapping[element][-1]
        except KeyError:
            return None

    def pushOverrides(self, overrides):
        """Push override handlers onto stack.

        Overrides provide new handlers for (existing) elements.
        Until popped again, the new handlers are used.

        overrides - mapping with key is element tuple (ns, name),
                    value is handler instance.
        """
        for element, handler in overrides.items():
            self.pushOverride(element, handler)
        self.__stack.append(overrides.keys())

    def pushOverridesAll(self, handler):
        """Push special handler for all overrides.
        """
        keys = self.__mapping.keys()
        for element in keys:
            self.pushOverride(element, handler)
        self.__stack.append(keys)

    def popOverrides(self):
        """Pop overrides.

        Removes the overrides from the stack, restoring to previous
        state.
        """
        elements = self.__stack.pop()
        for element in elements:
            self.popOverride(element)

    def pushOverride(self, element, handler):
        self.__mapping.setdefault(element, []).append(handler)

    def popOverride(self, element):
        stack = self.__mapping[element]
        stack.pop()
        if not stack:
            del self.__mapping[element]


class Importer(object):
    """A SAX based importer.
    """

    def __init__(self, handler_map=None):
        """Create an importer.

        The handler map is a mapping from element (ns, name) tuple to
        import handler, which is a subclass of BaseHandler.
        """
        self._defaults = {'ignore_not_allowed': False,
                          'import_filter': None}
        self._mapping = {}
        if handler_map is not None:
            self.addHandlerMap(handler_map)

    # MANIPULATORS

    def addHandlerMap(self, handler_map):
        """Add map of handlers for elements.

        handler_map - mapping with key is element tuple (ns, name),
                      value is handler instance.
        """
        for element, handler in handler_map.items():
            self._mapping[element] = [handler]

    def registerHandler(self, element, handler_factory):
        """Register a handler for a single element.

        element - an xml element name
        handler_factory - the class of the SAX event handler for it
                           (subclass of BaseHandler)
        """
        self._mapping[element] = [handler_factory]

    def registerOption(self, name, default=None):
        """Register an option that can be queried by producer later
        on.

        name - Name of the existing option. If provided in the options
        dictionary it will be returned, otherwise None will be.
        """
        self._defaults[name] = default

    def importHandler(self, result=None, options=None, extra=None):
        """Get import handler.

        Useful when we are sending the SAX events directly, not from file.

        settings - import settings object that can be inspected
                   by handlers (optional)
        result - initial result object to attach everything to (optional)

        Does not apply any import filters.

        returns handler object. handler.result() gives the end result, or pass
        initial result yourself.
        """
        options = self.getOptions(options)
        handler = _SaxImportHandler(MappingStack(self.getMapping()),
                                    options,
                                    result,
                                    extra)
        if options.import_filter is not None:
            return options.import_filter(handler)
        return handler

    def importFromStream(self, stream, result=None, options=None, extra=None):
        """Import from file object.

        sream - file object
        settings - import settings object that can be inspected
                   by handlers (optional)
        result - initial result object to attach everything to (optional)

        Applies an import filter if one is specified in the settings.

        returns top result object
        """
        handler = self.importHandler(result, options, extra)
        parser = xml.sax.make_parser()
        parser.setFeature(xml.sax.handler.feature_namespaces, 1)
        parser.setContentHandler(handler)
        handler.setDocumentLocator(parser)
        parser.parse(stream)
        return handler.result()

    def importFromString(self, string, result=None, options=None, extra=None):
        """Import from string.

        string - string with XML text
        settings - import settings object that can be inspected
                   by handlers (optional)
        result - initial result object to attach everything to (optional)

        returns top result object
        """
        return self.importFromStream(io.BytesIO(string), result, options, extra)

    def getOptions(self, options):
        """Return the set of possible options.
        """
        if isinstance(options, Options):
            return options
        return Options(options, self._defaults.copy())

    def getMapping(self):
        return self._mapping.copy()


class _SaxImportHandler(xml.sax.handler.ContentHandler):
    """Receives the SAX events and dispatches them to sub handlers.

    The importer is a ImporterMappingStack object
    """

    def __init__(self, mapping_stack, options=None, result=None, extra=None):
        self.__mapping_stack = mapping_stack
        # top of the handler stack is handler which ignores any events,
        self._handler_stack = [IgnoringHandler(result, None, options, extra)]
        self._depth_stack = []
        self._depth = 0
        self._outer_result = result
        self._result = result
        self._options = options
        self._locator = DummyLocator()
        self._extra = extra

    def setDocumentLocator(self, locator):
        self._locator = locator

    def startDocument(self):
        pass

    def endDocument(self):
        pass

    def startElementNS(self, name, qname, attrs):
        parent_handler = self._handler_stack[-1]
        if not parent_handler._checkElementAllowed(name):
            # we're not allowed and ignoring the element and all subelements
            self.__mapping_stack.pushOverridesAll(IgnoringHandler)
            self._handler_stack.append(IgnoringHandler(
                parent_handler.result(),
                parent_handler,
                self._options,
                self._extra))
            self._depth_stack.append(self._depth)
            self._depth += 1
            return
        # check whether we have a special handler
        factory = self.__mapping_stack.getHandler(name)
        if factory is None:
            # no handler, use parent's handler
            handler = parent_handler
        else:
            # create new subhandler
            handler = factory(
                parent_handler.result(),
                parent_handler,
                self._options,
                self._extra)
            handler.setDocumentLocator(self._locator)
            self.__mapping_stack.pushOverrides(handler.getOverrides())
            self._handler_stack.append(handler)
            self._depth_stack.append(self._depth)

        handler.startElementNS(name, qname, attrs)
        self._depth += 1

    def endElementNS(self, name, qname):
        self._depth -= 1
        handler = self._handler_stack[-1]
        if self._depth == self._depth_stack[-1]:
            self._result = handler.result()
            self._handler_stack.pop()
            self._depth_stack.pop()
            self.__mapping_stack.popOverrides()
            parent_handler = self._handler_stack[-1]
        else:
            parent_handler = handler

        if parent_handler._checkElementAllowed(name):
            handler.endElementNS(name, qname)

    def characters(self, chrs):
        handler = self._handler_stack[-1]
        if handler._checkTextAllowed(chrs):
            handler.characters(chrs)

    def getExtra(self):
        return self._extra

    def getOptions(self):
        return self._options

    def result(self):
        """Return result object of whole import.

        If we passed in a result object, then this is always going to
        be the one we need, otherwise get result of outer element.
        """
        return self._outer_result or self._result


class DummyLocator(object):
    """A dummy locator which is used if no document locator is available.
    """

    def getColumnNumber(self):
        """Return the column number where the current event ends.
        """
        return None

    def getLineNumber(self):
        """Return the line number where the current event ends.
        """
        return None

    def getPublicId(self):
        """Return the public identifier for the current event.
        """
        return None

    def getSystemId(self):
        """Return the system identifier for the current event.
        """
        return None


class BaseHandler(object):
    """Base class of all handlers.

    This should be subclassed to implement your own handlers.
    """
    def __init__(self, parent, parent_handler, options=None, extra=None):
        """Initialize BaseHandler.

        parent - the parent object as being constructed in the import
        parent_handler - the SAX handler constructing the parent object
        settings - optional import settings object.
        """
        self._parent = parent
        self._parent_handler = parent_handler
        self._result = None
        self._data = {}
        self._options = options
        self._extra = extra

    # MANIPULATORS

    def setResult(self, result):
        """Sets the result data for this handler
        """
        self._result = result
        return result

    def setData(self, key, value):
        """Many sub-elements with text-data use this to pass that data to
        their parent (self.parentHandler().setData(foo, bar))
        """
        self._data[key] = value

    def setDocumentLocator(self, locator):
        self._locator = locator

    # ACCESSORS

    def getExtra(self):
        return self._extra

    def getData(self, key):
        return self._data.get(key)

    def clearData(self):
        self._data = {}

    def getDocumentLocator(self):
         return self._locator

    def parentHandler(self):
        """Gets the parent handler
        """
        return self._parent_handler

    def parent(self):
        """Gets the parent
        """
        return self._parent

    def result(self):
        """Gets the result data for this handler or the result data of the
        parent, if this handler didn't set any
        """
        if self._result is not None:
            return self._result
        return self._parent

    def getOptions(self):
        """Get import settings object.
        """
        return self._options

    def _checkElementAllowed(self, name):
        if self.isElementAllowed(name):
            return True
        if self._options.ignore_not_allowed:
            return False
        raise ElementNotAllowedError(
            "Element %s in namespace %s is not allowed here" % (
                name[1], name[0]))

    def _checkTextAllowed(self, chrs):
        if self.isTextAllowed(chrs):
            return True
        if self._options.ignore_not_allowed:
            return False
        raise TextNotAllowedError("Text is not allowed here")

    # OVERRIDES

    def startElementNS(self, name, qname, attrs):
        pass

    def endElementNS(self, name, qname):
        pass

    def characters(self, chrs):
        pass

    def getOverrides(self):
        """Returns a dictionary of overridden handlers for xml elements.
        (The handlers override any registered handler for that element, but
        getOverrides() can be used to 'override' tags that aren't
        registered.)
        """
        return {}

    def isElementAllowed(self, name):
        """Returns True if element is to be processed at all by handler.

        name - ns, name tuple.

        Can be overridden in subclass. If it returns False, element is
        completely ignored or error is raised, depending on configuration
        of importer.
        """
        return True

    def isTextAllowed(self, chrs):
        """Returns True if text is to be processed at all by handler.

        chrs - text input

        Can be overridden in subclass. If it is False, text is either
        completely ignored or error is raised depending on configuration of
        importer.
        """
        return True


class IgnoringHandler(BaseHandler):
    """A handler that ignores any incoming events that cannot be handled.
    """
    pass


