from xml.sax.saxutils import XMLGenerator

class StableXMLGenerator(XMLGenerator):
    def __init__(self, out=None, encoding="iso-8859-1"):
        XMLGenerator.__init__(self, out, encoding)
        self._last_start_element = None
        
    def _processLast(self):
        if self._last_start_element is not None:
            self._startElementNSHelper(*self._last_start_element)
            self._last_start_element = None
            
    def startElement(self, name, attrs):
        self._processLast()
        XMLGenerator.startElement(self, name, attrs)

    def endElement(self, name):
        self._processLast()
        XMLGenerator.endElement(self, name)
        
    def startElementNS(self, name, qname, attrs):
        self._processLast()
        self._last_start_element = (name, qname, attrs)

    def _startElementNSHelper(self, name, qname, attrs, close=0):
        if name[0] is None:
            name = name[1]
        elif self._current_context[name[0]] is None:
            # default namespace
            name = name[1]
        else:
            name = self._current_context[name[0]] + ":" + name[1]
        self._out.write('<' + name)

        for k,v in self._undeclared_ns_maps:
            if k is None:
                self._out.write(' xmlns="%s"' % (v or ''))
            else:
                self._out.write(' xmlns:%s="%s"' % (k,v))
        self._undeclared_ns_maps = []

        # sort attributes so we generate stable output
        names = attrs.keys()
        names.sort()
        
        for name in names:
            value = attrs[name]
            if name[0] is None:
                name = name[1]
            elif self._current_context[name[0]] is None:
                # default namespace
                #If an attribute has a nsuri but not a prefix, we must
                #create a prefix and add a nsdecl
                prefix = self.GENERATED_PREFIX % self._generated_prefix_ctr
                self._generated_prefix_ctr = self._generated_prefix_ctr + 1
                name = prefix + ':' + name[1]
                self._out.write(' xmlns:%s=%s' % (prefix, quoteattr(name[0])))
                self._current_context[name[0]] = prefix
            else:
                name = self._current_context[name[0]] + ":" + name[1]
            self._out.write(' %s=' % name)
            writeattr(self._out, value)
        if close:
            self._out.write('/>')
        else:
            self._out.write('>')

    def endElementNS(self, name, qname):
        if self._last_start_element is not None:
            name, qname, attrs = self._last_start_element
            self._startElementNSHelper(name, qname, attrs, 1)
            self._last_start_element = None
            return
        # XXX: if qname is not None, we better use it.
        # Python 2.0b2 requires us to use the recorded prefix for
        # name[0], though
        if name[0] is None:
            qname = name[1]
        elif self._current_context[name[0]] is None:
            qname = name[1]
        else:
            qname = self._current_context[name[0]] + ":" + name[1]
        self._out.write('</%s>' % qname)

    def characters(self, content):
        if content:
            self._processLast()
            XMLGenerator.characters(self, content)

    def ignorableWhitespace(self, content):
        if content:
            self._processLast()
            XMLGenerator.ignorableWhitespace(self, content)

    def processingInstruction(self, target, data):
        self._processLast()
        XMLGenerator.processingInstruction(self, target, data)
