"""
An XML importer based on layered SAX handlers.

Elements can have their own sax handlers associated with them, which
handle all events inside those elements.
"""
import xml.sax
from xml.sax.handler import feature_namespaces
from xml.sax.handler import ContentHandler
from StringIO import StringIO


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


class BaseSettings(object):
    """Base class of settings sent to the handlers.

    Subclass this for custom settings objects.
    """
    def __init__(self, ignore_not_allowed=False, import_filter_factory=None):
        self._ignore_not_allowed = ignore_not_allowed
        self._import_filter_factory = import_filter_factory

    def ignoreNotAllowed(self):
        return self._ignore_not_allowed

    def getImportFilterFactory(self):
        return self._import_filter_factory


# null settings contains the default settings
NULL_SETTINGS = BaseSettings()
IGNORE_SETTINGS = BaseSettings(ignore_not_allowed=True)


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
        self._mapping = {}
        if handler_map is not None:
            self.addHandlerMap(handler_map)

    # MANIPULATORS

    def getMapping(self):
        return self._mapping.copy()

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

    def importHandler(self, settings=NULL_SETTINGS, result=None, info=None):
        """Get import handler.

        Useful when we are sending the SAX events directly, not from file.

        settings - import settings object that can be inspected
                   by handlers (optional)
        result - initial result object to attach everything to (optional)

        Does not apply any import filters.

        returns handler object. handler.result() gives the end result, or pass
        initial result yourself.
        """
        return _SaxImportHandler(MappingStack(self.getMapping()),
                                 settings,
                                 result,
                                 info)

    def importFromFile(self, f, settings=NULL_SETTINGS,
                       result=None, info=None):
        """Import from file object.

        f - file object
        settings - import settings object that can be inspected
                   by handlers (optional)
        result - initial result object to attach everything to (optional)

        Applies an import filter if one is specified in the settings.

        returns top result object
        """
        handler = self.importHandler(settings, result, info)
        parser = xml.sax.make_parser()
        parser.setFeature(feature_namespaces, 1)
        import_filter_factory = settings.getImportFilterFactory()
        if import_filter_factory is not None:
            parser_handler = import_filter_factory(handler)
        else:
            parser_handler = handler
        parser.setContentHandler(parser_handler)
        handler.setDocumentLocator(parser)
        parser.parse(f)
        return handler.result()

    def importFromString(self, s, settings=NULL_SETTINGS,
                         result=None, info=None):
        """Import from string.

        s - string with XML text
        settings - import settings object that can be inspected
                   by handlers (optional)
        result - initial result object to attach everything to (optional)

        returns top result object
        """
        f = StringIO(s)
        return self.importFromFile(f, settings, result, info)


class _SaxImportHandler(ContentHandler):
    """Receives the SAX events and dispatches them to sub handlers.

    The importer is a ImporterMappingStack object
    """

    def __init__(self, mapping_stack, settings=None, result=None, info=None):
        self.__mapping_stack = mapping_stack
        # top of the handler stack is handler which ignores any events,
        self._handler_stack = [IgnoringHandler(result, None, settings, info)]
        self._depth_stack = []
        self._depth = 0
        self._outer_result = result
        self._result = result
        self._settings = settings
        self._locator = DummyLocator()
        self._info = info

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
                self._settings,
                self._info))
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
                self._settings,
                self._info)
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

    def getInfo(self):
        return self._info

    def getSettings(self):
        return self._settings

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
    def __init__(self, parent, parent_handler,
                 settings=NULL_SETTINGS, info=None):
        """Initialize BaseHandler.

        parent - the parent object as being constructed in the import
        parent_handler - the SAX handler constructing the parent object
        settings - optional import settings object.
        """
        self._parent = parent
        self._parent_handler = parent_handler
        self._result = None
        self._data = {}
        self._settings = settings
        self._info = info

    # MANIPULATORS

    def setResult(self, result):
        """Sets the result data for this handler
        """
        self._result = result

    def setData(self, key, value):
        """Many sub-elements with text-data use this to pass that data to
        their parent (self.parentHandler().setData(foo, bar))
        """
        self._data[key] = value

    def setDocumentLocator(self, locator):
        self._locator = locator

    # ACCESSORS

    def getInfo(self):
        return self._info

    def getData(self, key):
        if self._data.has_key(key):
            return self._data[key]
        return None

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
        else:
            return self._parent

    def settings(self):
        """Get import settings object.
        """
        return self._settings

    def _checkElementAllowed(self, name):
        if self.isElementAllowed(name):
            return True
        if self._settings.ignoreNotAllowed():
            return False
        raise ElementNotAllowedError,\
              "Element %s in namespace %s is not allowed here" % (
            name[1], name[0])

    def _checkTextAllowed(self, chrs):
        if self.isTextAllowed(chrs):
            return True
        if self._settings.ignoreNotAllowed():
            return False
        raise TextNotAllowedError,\
              "Element %s in namespace %s is not allowed here" % (
            name[1], name[0])

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


