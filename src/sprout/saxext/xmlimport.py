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

class XMLOverridableElementRegistry:
    """An element registry which can be overridden while handling events.
    """
    def __init__(self):
        self._mapping = {}
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
    
class SaxImportHandler(ContentHandler):
    """Receives the SAX events and dispatches them to sub handlers.
    """
    
    def __init__(self, registry, start_object, settings=None):
        self._registry = registry
        self._handler_stack = []
        self._depth_stack = []
        self._object = start_object
        self._settings = settings
        # XXX Might need this later for context sensitive parsing
        self._depth = 0
        
    def startDocument(self):
        # XXX probably some export metadata should be read and handled here.
        # Export will have some configuration options that may impact the
        # import process.
        # XXX maybe handle encoding?
        pass 
    
    def endDocument(self):
        # XXX finalization
        pass
    
    def startElementNS(self, name, qname, attrs):
        factory = self._registry.getXMLElementHandler(name)
        if factory is None:
            handler = self._handler_stack[-1]
        else:
            if self._handler_stack:
                parent_handler = self._handler_stack[-1]
                object = parent_handler.getResult()
            else:
                parent_handler = None
                object = self._object
            handler = factory(object, parent_handler, self._settings)
            self._registry.pushOverrides(handler.getOverrides())
            self._handler_stack.append(handler)
            self._depth_stack.append(self._depth)
        handler.startElementNS(name, qname, attrs)
        self._depth += 1

    def endElementNS(self, name, qname):
        self._depth -= 1
        handler = self._handler_stack[-1]
        if self._depth == self._depth_stack[-1]:
            self._handler_stack.pop()
            self._depth_stack.pop()
            self._registry.popOverrides()
        handler.endElementNS(name, qname)
        
    def characters(self, chrs):
        handler = self._handler_stack[-1]
        handler.characters(chrs)
    
class BaseHandler:
    """Base class of all sub handlers.
    """
    def __init__(self, parent, parent_handler, settings=None):
        # it is essential NOT to confuse self._parent and
        # self._parent_handler. The is the parent object as it is being
        # constructed from the import, the latter is the handler that is 
        # handling the parent of the current handled element.
        self._parent = parent
        self._parent_handler = parent_handler
        self._result = None
        self._data = {}
        self._metadata_set = None
        self._metadata_key = None
        self._metadata = {}
        self._settings = settings
        
    def getOverrides(self):
        """Returns a dictionary of overridden handlers for xml elements. 
        (The handlers override any registered handler for that element, but
        getOverrides() can be used to 'override' tags that aren't
        registered.)
        """
        return {}

    def setData(self, key, value):
        """Many sub-elements with text-data use this to pass that data to
        their parent (self._parent_handler.setData(foo, bar))
        """
        self._data[key] = value

    def getData(self, key):
        if self._data.has_key(key):
            return self._data[key]
        return None

    def getParentHandler(self):
        """Gets the parent handler
        """
        return self._parent_handler
    
    def getParent(self):
        """Gets the parent 
        """
        return self._parent
    
    def getResult(self):
        """Gets the result data for this handler or the result data of the
        parent, if this handler didn't set any
        """
        if self._result is not None:
            return self._result
        else:
            return self._parent

    def setResult(self, result):
        """Sets the result data for this handler
        """
        self._result = result
    
    def startElementNS(self, name, qname, attrs):
        pass
    
    def endElementNS(self, name, qname):
        pass

    def characters(self, chrs):
        pass

def importFromString(s, registry, start_object, settings=None):
    """Import from string.

    s - string with XML text
    registry - import handler registry to use
    start_object - object to attach everything to
    settings - optional import settings object that can be inspected
               by handlers.
    """
    f = StringIO(s)
    importFromFile(f, registry, start_object, settings)
    
def importFromFile(f, registry, start_object, settings=None):
    """Import from file object.

    f - file object
    registry - import handler registry to use
    start_object - object to attach everything to
    settings - optional import settings object that can be inspected
               by handlers
    """ 
    handler = SaxImportHandler(registry, start_object, settings)
    parser = xml.sax.make_parser()
    parser.setFeature(feature_namespaces, 1)
    parser.setContentHandler(handler)
    parser.parse(f)
