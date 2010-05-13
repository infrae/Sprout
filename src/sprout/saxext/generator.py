"""A cleaned up SAX generator. Also include stable generator.
"""
import xml.sax.handler
import codecs

class NotSupportedError(Exception):
    pass

class XMLGenerator(xml.sax.handler.ContentHandler):
    """Updated version of XMLGenerator from xml.sax.saxutils.

    This takes the SAX parser in Python and improves it (with some hints
    from the PyXML version as well).

    Differences:

    Producing a unicode stream is now possible, if encoding argument is
    set to None. The stream needs to be unicode aware itself in that case.

    No defaulting to sys.stdout; output stream must always be provided.

    Classic non-namespace events are not handled but raise error
    to avoid confusion.

    Refactoring to more cleanly support StableXMLGenerator.

    Closes empty elements immediately.

    Stability in the outputting of attributes (they're sorted).

    Code has been cleaned up.
    """

    def __init__(self, out, encoding="UTF-8"):
        xml.sax.handler.ContentHandler.__init__(self)
        if encoding is not None:
            out = _outputwrapper(out, encoding)
        self._out = out
        self._ns_contexts = [{}] # contains uri -> prefix dicts
        self._current_context = self._ns_contexts[-1]
        self._undeclared_ns_maps = []
        self._encoding = encoding
        self._last_start_element = None

    def _processLast(self):
        if self._last_start_element is not None:
            self._startElementNSHelper(*self._last_start_element)
            self._last_start_element = None

    # ContentHandler methods

    def startDocument(self):
        if self._encoding is not None:
            self._out.write('<?xml version="1.0" encoding="%s"?>\n' %
                            self._encoding)
        else:
            self._out.write('<?xml version="1.0"?>\n')

    def startPrefixMapping(self, prefix, uri):
        self._ns_contexts.append(self._current_context.copy())
        self._current_context[uri] = prefix
        self._undeclared_ns_maps.append((prefix, uri))

    def endPrefixMapping(self, prefix):
        self._current_context = self._ns_contexts[-1]
        del self._ns_contexts[-1]

    def startElement(self, name, attrs):
        raise NotSupportedError,\
              "XMLGenerator does not support non-namespace SAX events."

    def endElement(self, name):
        raise NotSupportedError,\
              "XMLGenerator does not support non-namespace SAX events."

    def startElementNS(self, name, qname, attrs):
        """Start element.

        Note that qname is always ignored in favor of namespace lookup
        in the name tuple.
        """
        self._processLast()

        # handle as much as possible here so that errors are raised
        # at the right spot, and not only at endElementNS()

        uri, localname = name
        if uri is None:
            qname = localname
        elif self._current_context[uri] is None:
            # default namespace
            qname = localname
        else:
            qname = self._current_context[uri] + ":" + localname

        # sorted to get predictability in output
        names = attrs.keys()
        names.sort()

        attr_data = []
        for name in names:
            value = attrs[name]
            uri, localname = name
            if uri is None:
                attr_qname = localname
            else:
                prefix = self._current_context[uri]
                if prefix is None:
                    raise KeyError, "Attribute in default namespace, "\
                          "but no prefix declared."
                # this gives a key error if attribute is in default namespace
                attr_qname = self._current_context[uri] + ":" + localname
            attr_data.append((attr_qname, value))

        self._last_start_element = (qname, attr_data)

    def _startElementNSHelper(self, qname, attr_data, close=False):
        self._out.write('<' + qname)

        # sort namespace declarations; None prefix will be sorted to beginning
        self._undeclared_ns_maps.sort()
        for k,v in self._undeclared_ns_maps:
            if k is None:
                self._out.write(' xmlns="%s"' % (v or ''))
            else:
                self._out.write(' xmlns:%s="%s"' % (k,v))
        self._undeclared_ns_maps = []

        for qname, value in attr_data:
            self._out.write(' %s=' % qname)
            writeattr(self._out, value)

        if close:
            self._out.write('/>')
        else:
            self._out.write('>')

    def endElementNS(self, name, qname):
        """End element.

        Note that namespace lookup is always ignored in favor of namespace
        lookup in qname.
        """
        if self._last_start_element is not None:
            qname, attr_data = self._last_start_element
            self._startElementNSHelper(qname, attr_data, True)
            self._last_start_element = None
            return
        uri, localname = name
        if uri is None:
            qname = localname
        elif self._current_context[uri] is None:
            qname = localname
        else:
            qname = self._current_context[uri] + ":" + localname
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
