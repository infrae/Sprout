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

class ElementRegistry:
    """An element registry which can be overridden while handling events.
    """
    def __init__(self, handler_map=None):
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

    
    def pushOverrides(self, overrides):
        """Push override handlers onto stack.

        Overrides provide new handlers for (existing) elements.
        Until popped again, the new handlers are used.

        overrides - mapping with key is element tuple (ns, name),
                    value is handler instance.
        """
        for element, handler in overrides.items():
            self._pushOverride(element, handler)
        self._stack.append(overrides.keys())
      
    def popOverrides(self):
        """Pop overrides.

        Removes the overrides from the stack, restoring to previous
        state.
        """
        elements = self._stack.pop()
        for element in elements:
            self._popOverride(element)

    # ACCESSORS
    
    def getXMLElementHandler(self, element):
        """Retrieve handler for a particular element (ns, name) tuple.
        """
        try:
            return self._mapping[element][-1]
        except KeyError:
            return None

    # PRIVATE
    
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
    
    def __init__(self, registry, settings=None, result=None):
        self._registry = registry
        self._handler_stack = []
        self._depth_stack = []
        self._depth = 0
        self._outer_result = result
        self._result = result
        self._settings = settings
        
    def startDocument(self):
        pass 
    
    def endDocument(self):
        pass    

    def startElementNS(self, name, qname, attrs):
        factory = self._registry.getXMLElementHandler(name)
        if factory is None:
            handler = self._handler_stack[-1]
        else:
            if self._handler_stack:
                parent_handler = self._handler_stack[-1]
                result = parent_handler.result()
            else:
                parent_handler = None
                result = self._result
            handler = factory(result, parent_handler, self._settings)
            self._registry.pushOverrides(handler.getOverrides())
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
            self._registry.popOverrides()
        handler.endElementNS(name, qname)
        
    def characters(self, chrs):
        handler = self._handler_stack[-1]
        handler.characters(chrs)

    def result(self):
        """Return result object of whole import.

        If we passed in a result object, then this is always going to
        be the one we need, otherwise get result of outer element.
        """
        return self._outer_result or self._result
    
class BaseHandler:
    """Base class of all sub handlers.
    """
    def __init__(self, parent, parent_handler, settings=None):
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

    # MANIPULATORS

    def setResult(self, result):
        """Sets the result data for this handler
        """
        self._result = result
    
    def setData(self, key, value):
        """Many sub-elements with text-data use this to pass that data to
        their parent (self.getParentHandler().setData(foo, bar))
        """
        self._data[key] = value

    # ACCESSORS

    def getData(self, key):
        if self._data.has_key(key):
            return self._data[key]
        return None

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

def importHandler(registry, settings=None, result=None):
    """Get import handler.

    Useful when we are sending the SAX events directly, not from file.

    registry - import handler registry to use
    settings - import settings object that can be inspected
               by handlers (optional)
    result - initial result object to attach everything to (optional)

    returns handler object. handler.result() gives the end result, or pass
    initial result yourself.
    """
    return _SaxImportHandler(registry, settings, result)
    
def importFromString(s, registry, settings=None, result=None):
    """Import from string.

    s - string with XML text
    registry - import handler registry to use
    settings - import settings object that can be inspected
               by handlers (optional)
    result - initial result object to attach everything to (optional)

    returns top result object
    """
    f = StringIO(s)
    return importFromFile(f, registry, settings, result)
    
def importFromFile(f, registry, settings=None, result=None):
    """Import from file object.

    f - file object
    registry - import handler registry to use
    settings - import settings object that can be inspected
               by handlers (optional)
    result - initial result object to attach everything to (optional)

    returns top result object
    """ 
    handler = _SaxImportHandler(registry, settings, result)
    parser = xml.sax.make_parser()
    parser.setFeature(feature_namespaces, 1)
    parser.setContentHandler(handler)
    parser.parse(f)
    return handler.result()
