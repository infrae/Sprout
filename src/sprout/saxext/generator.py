"""A cleaned up SAX generator. Also include stable generator.
"""
import xml.sax.handler
import codecs

class NotSupportedError(Exception):
    pass

class XMLGenerator(xml.sax.handler.ContentHandler):
    """Updated version of XMLGenerator from xml.sax.saxutils.

    This takes the PyXML version (the default Python version is buggy
    in Python 2.3).

    Differences:
    
    Producing a unicode stream is now possible, if encoding argument is
    set to None. The stream needs to be unicode aware itself in that case.

    No defaulting to sys.stdout; output stream must always be provided.
    
    Classic non-namespace events are not handled to avoid confusion.

    Refactoring to more cleanly support StableXMLGenerator.

    Closes empty elements immediately.

    Stability in the outputting of attributes (they're sorted).
    
    Code has been cleaned up.
    """
    GENERATED_PREFIX = "sprout.saxext.generator%s"

    def __init__(self, out, encoding="UTF-8"):
        xml.sax.handler.ContentHandler.__init__(self)
        if encoding is not None:
            self._out = _outputwrapper(out, encoding)
        self._ns_contexts = [{}] # contains uri -> prefix dicts
        self._current_context = self._ns_contexts[-1]
        self._undeclared_ns_maps = []
        self._encoding = encoding
        self._generated_prefix_ctr = 0
        self._last_start_element = None

    def _processLast(self):
        if self._last_start_element is not None:
            self._startElementNSHelper(*self._last_start_element)
            self._last_start_element = None

    # ContentHandler methods

    def startDocument(self):
        self._out.write('<?xml version="1.0" encoding="%s"?>\n' %
                        self._encoding)

    def startPrefixMapping(self, prefix, uri):
        self._ns_contexts.append(self._current_context.copy())
        self._current_context[uri] = prefix
        self._undeclared_ns_maps.append((prefix, uri))

    def endPrefixMapping(self, prefix):
        self._current_context = self._ns_contexts[-1]
        del self._ns_contexts[-1]

    def startElement(self, name, attrs):
        raise NotSupportedError, "XMLGenerator does not support non-namespace SAX events."
    
    def endElement(self, name):
        raise NotSupportedError, "XMLGenerator does not support non-namespace SAX events."

    def startElementNS(self, name, qname, attrs):
        self._processLast()
        self._last_start_element = (name, qname, attrs)

    def _startElementNSHelper(self, name, qname, attrs, close=False):
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

        # sorted to get predictability in output
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
            self._startElementNSHelper(name, qname, attrs, True)
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
            writetext(self._out, content)

    def ignorableWhitespace(self, content):
        if content:
            self._processLast()
            self._out.write(content)

    def processingInstruction(self, target, data):
        self._processLast()
        self._out.write('<?%s %s?>' % (target, data))


def __dict_replace(s, d):
    """Replace substrings of a string using a dictionary."""
    for key, value in d.items():
        s = s.replace(key, value)
    return s

def escape(data, entities={}):
    """Escape &, <, and > in a string of data.

    You can escape other strings of data by passing a dictionary as
    the optional entities parameter.  The keys and values must all be
    strings; each key will be replaced with its corresponding value.
    """
    data = data.replace("&", "&amp;")
    data = data.replace("<", "&lt;")
    data = data.replace(">", "&gt;")
    if entities:
        data = __dict_replace(data, entities)
    return data

def unescape(data, entities={}):
    """Unescape &amp;, &lt;, and &gt; in a string of data.

    You can unescape other strings of data by passing a dictionary as
    the optional entities parameter.  The keys and values must all be
    strings; each key will be replaced with its corresponding value.
    """
    data = data.replace("&lt;", "<")
    data = data.replace("&gt;", ">")
    if entities:
        data = __dict_replace(data, entities)
    # must do ampersand last
    return data.replace("&amp;", "&")

def quoteattr(data, entities={}):
    """Escape and quote an attribute value.

    Escape &, <, and > in a string of data, then quote it for use as
    an attribute value.  The \" character will be escaped as well, if
    necessary.

    You can escape other strings of data by passing a dictionary as
    the optional entities parameter.  The keys and values must all be
    strings; each key will be replaced with its corresponding value.
    """
    data = escape(data, entities)
    if '"' in data:
        if "'" in data:
            data = '"%s"' % data.replace('"', "&quot;")
        else:
            data = "'%s'" % data
    else:
        data = '"%s"' % data
    return data

def _outputwrapper(stream,encoding):
    writerclass = codecs.lookup(encoding)[3]
    return writerclass(stream)

def writetext(stream, text, entities={}):
    stream.errors = "xmlcharrefreplace"
    stream.write(escape(text, entities))
    stream.errors = "strict"

def writeattr(stream, text):
    countdouble = text.count('"')
    if countdouble:
        countsingle = text.count("'")
        if countdouble <= countsingle:
            entities = {'"': "&quot;"}
            quote = '"'
        else:
            entities = {"'": "&apos;"}
            quote = "'"
    else:
        entities = {}
        quote = '"'
    stream.write(quote)
    writetext(stream, text, entities)
    stream.write(quote)
