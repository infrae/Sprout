class HookableHandler:
    """Handler that can be hooked into.
    
    This handler by default doesn't do anything to events but pass
    them through. By subclassing it, hook methods can be specified
    however that are executed before these events, and/or instead of
    these events.

    Possible hooks:

    <method_name>_simple

    calls a callable without parameters, no return value expected, before
    event is passed through.
    
    <method_name>_preprocess

    calls a callable with parameter of original function. If return value,
    these are assumed to be the pre-processed arguments for the real event.
    
    <method_name>_override

    call this instead of passing the event along.

    To get to the handler that events are passed along to, use
    getOutputHandler().
    """

    def __init__(self, output_handler):
        self._output_handler = output_handler
 
    def setHook(self, method_name, function):
        """Set a hook function to a particular method.

        Gets executed before method is executed, with parameters of
        method. If this returns something, this is assumed to be the
        processed parameters of what the method will receive.

        Can be used to preprocess parameters.
        """
        self._hooks[method_name] = function

    def setSimpleHook(self, method_name, function):
        """Set a hook function for a particular method.

        Hook gets no parameters and returns nothing.
        """
        self._simple_hooks[method_name] = function

    def setOverride(self, method_name, function):
        """Instead of doing normal behavior, call function instead.
        """
        self._overrides[method_name] = function

    def _hookedExecute(self, method_name, *args, **kw):
        simple = getattr(self, method_name + '_simple', None)
        if simple is not None:
            simple()
        preprocess = getattr(self, method_name + '_preprocess', None)
        result = None
        if preprocess is not None:
            result = preprocess(*args)
        if result is not None:
            args = result
            kw = {}
        override = getattr(self, method_name + '_override', None)
        if override is not None:
            override(*args, **kw)
        else:
            getattr(self._output_handler, method_name)(*args, **kw)

    def startDocument(self):
        self._hookedExecute('startDocument')
        
    def endDocument(self):
        self._hookedExecute('endDocument')
        
    def startPrefixMapping(self, prefix, uri):
        self._hookedExecute('startPrefixMapping', prefix, uri)
        
    def endPrefixMapping(self, prefix):
        self._hookedExecute('endPrefixMapping', prefix)
        
    def startElement(self, name, attrs):
        self._hookedExecute('startElement', name, attrs)
        
    def endElement(self, name):
        self._hookedExecute('endElement', name)
        
    def startElementNS(self, name, qname, attrs):
        self._hookedExecute('startElementNS', name, qname, attrs)
        
    def endElementNS(self, name, qname):
        self._hookedExecute('endElementNS', name, qname)
        
    def characters(self, content):
        self._hookedExecute('characters', content)
        
    def ignorableWhitespace(self, chars):
        self._hookedExecute('ignorableWhitespace', chars)

    def processingInstruction(self, target, data):
        self._hookedExecute('processingInstruction', target, data)
        
    def skippedEntity(self, name):
        self._skippedEntity('skippedEntity', target, data)

    def getOutputHandler(self):
        return self._output_handler
