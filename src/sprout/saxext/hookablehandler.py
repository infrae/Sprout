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

    def __init__(self, parent):
        self._parent = parent

    def _warp(self, method_name, *args, **kw):
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
            getattr(self._parent, method_name)(*args, **kw)

    def getOutputHandler(self):
        return self._parent

    def setDocumentLocator(self, parser):
        self._parent.setDocumentLocator(parser)

    def result(self):
        return self._parent.result()

    def startDocument(self):
        self._warp('startDocument')

    def endDocument(self):
        self._warp('endDocument')

    def startPrefixMapping(self, prefix, uri):
        self._warp('startPrefixMapping', prefix, uri)

    def endPrefixMapping(self, prefix):
        self._warp('endPrefixMapping', prefix)

    def startElement(self, name, attrs):
        self._warp('startElement', name, attrs)

    def endElement(self, name):
        self._warp('endElement', name)

    def startElementNS(self, name, qname, attrs):
        self._warp('startElementNS', name, qname, attrs)

    def endElementNS(self, name, qname):
        self._warp('endElementNS', name, qname)

    def characters(self, content):
        self._warp('characters', content)

    def ignorableWhitespace(self, chars):
        self._warp('ignorableWhitespace', chars)

    def processingInstruction(self, target, data):
        self._warp('processingInstruction', target, data)

    def skippedEntity(self, name):
        self._warp('skippedEntity', name)

