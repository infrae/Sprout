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
    
class BaseSettings:
    """Base class of settings sent to the handlers.

    Subclass this for custom settings objects.
    """
    def ignoreNotAllowed(self):
        return False

# null settings contains the default settings
NULL_SETTINGS = BaseSettings()

class Importer:
    """A SAX based importer.
    """
    def __init__(self, handler_map=None, default_handler=None):
        """Create an importer.

        The handler map is a mapping from element (ns, name) tuple to
        import handler, which is a subclass of BaseHandler.
        """
        self._default_handler = default_handler
        self._mapping = {}
        if handler_map is not None:
            self.addHandlerMap(handler_map)
        self._stack = []
        
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
            
    def importHandler(self, settings=NULL_SETTINGS, result=None, info=None):
        """Get import handler.

        Useful when we are sending the SAX events directly, not from file.

        settings - import settings object that can be inspected
                   by handlers (optional)
        result - initial result object to attach everything to (optional)

        returns handler object. handler.result() gives the end result, or pass
        initial result yourself.
        """
        return _SaxImportHandler(self, settings, result, info)

    def importFromFile(self, f, settings=NULL_SETTINGS,
                       result=None, info=None):
        """Import from file object.

        f - file object
        settings - import settings object that can be inspected
                   by handlers (optional)
        result - initial result object to attach everything to (optional)

        returns top result object
        """
        self.clear()
        handler = self.importHandler(settings, result, info)
        parser = xml.sax.make_parser()
        parser.setFeature(feature_namespaces, 1)
        parser.setContentHandler(handler)
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

    def clear(self):
        """Clear registry from any overrides.

        Exceptions during import can leave the system in an
        confused state (overrides still on stack). This restores
        the initial conditions.
        """
        self._stack = []
        mapping = {}
        for key, value in self._mapping.items():
            mapping[key] = [value[0]]
        self._mapping = mapping

    # ACCESSORS
    

    # PRIVATE

    def _getHandler(self, element):
        """Retrieve handler for a particular element (ns, name) tuple.
        """
        try:
            return self._mapping[element][-1]
        except KeyError:
            return self._default_handler

    def _pushOverrides(self, overrides):
        """Push override handlers onto stack.

        Overrides provide new handlers for (existing) elements.
        Until popped again, the new handlers are used.
       
        overrides - mapping with key is element tuple (ns, name),
                    value is handler instance.
        """
        for element, handler in overrides.items():
            self._pushOverride(element, handler)
        self._stack.append(overrides.keys())
      
    def _popOverrides(self):
        """Pop overrides.

        Removes the overrides from the stack, restoring to previous
        state.
        """
        elements = self._stack.pop()
        for element in elements:
            self._popOverride(element)

    def _pushOverride(self, element, handler):
        self._mapping.setdefault(element, []).append(handler)

    def _popOverride(self, element):
        stack = self._mapping[element]
        stack.pop()
        if not stack:
            del self._mapping[element]
   
class _SaxImportHandler(ContentHandler):
    """Receives the SAX events and dispatches them to sub handlers.
    """
    
    def __init__(self, importer, settings=None, result=None, info=None):
        self._importer = importer
        self._handler_stack = []
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
        factory = self._importer._getHandler(name)
        if factory is None:
            handler = parent_handler = self._handler_stack[-1]
        else:
            if self._handler_stack:
                parent_handler = self._handler_stack[-1]
                result = parent_handler.result()
            else:
                parent_handler = None
                result = self._result
            handler = factory(
                result,
                parent_handler,
                self._settings,
                self._info)
            handler.setDocumentLocator(self._locator)
            self._importer._pushOverrides(handler.getOverrides())
            self._handler_stack.append(handler)
            self._depth_stack.append(self._depth)
        if (parent_handler is None or
            parent_handler._checkElementAllowed(name)):
            handler.startElementNS(name, qname, attrs)
        self._depth += 1

    def endElementNS(self, name, qname):
        self._depth -= 1
        handler = parent_handler = self._handler_stack[-1]
        if self._depth == self._depth_stack[-1]:
            self._result = handler.result()
            self._handler_stack.pop()
            self._depth_stack.pop()
            self._importer._popOverrides()
            if self._handler_stack:
                parent_handler = self._handler_stack[-1]
            else:
                parent_handler = None
        if (parent_handler is None or
            parent_handler._checkElementAllowed(name)):
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
    
class DummyLocator:
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
    
