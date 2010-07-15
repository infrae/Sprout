
from HTMLParser import HTMLParser
from htmlentitydefs import name2codepoint

from sprout.saxext.hookablehandler import HookableHandler

IMMEDIATE_CLOSE_TAGS = ['br']

MUST_HAVE_END_TAGS = ['a', 'abbr', 'acronym', 'address', 'applet',
                        'b', 'bdo', 'big', 'blink', 'blockquote',
                        'button', 'caption', 'center', 'cite',
                        'comment', 'del', 'dfn', 'dir', 'div',
                        'dl', 'dt', 'em', 'embed', 'fieldset',
                        'font', 'form', 'frameset', 'h1', 'h2',
                        'h3', 'h4', 'h5', 'h6', 'i', 'iframe',
                        'ins', 'kbd', 'label', 'legend', 'li',
                        'listing', 'map', 'marquee', 'menu',
                        'multicol', 'nobr', 'noembed', 'noframes',
                        'noscript', 'object', 'ol', 'optgroup',
                        'option', 'p', 'pre', 'q', 's', 'script',
                        'select', 'small', 'span', 'strike',
                        'strong', 'style', 'sub', 'sup', 'table',
                        'tbody', 'td', 'textarea', 'tfoot',
                        'th', 'thead', 'title', 'tr', 'tt', 'u',
                        'ul', 'xmp']


class HtmlTagFixerFilter(HookableHandler):
    """makes sure that some elements do or don't get a closing tag"""

    def __init__(self, output_handler):
        HookableHandler.__init__(self, output_handler)
        self._count = 0
        self._stack = []

    def startElementNS_preprocess(self, name, qname, attrs):
        self._stack.append((name, self._count))
        self._count += 1

    def endElementNS_preprocess(self, name, qname):
        if name[1] not in MUST_HAVE_END_TAGS:
            return
        last_name, last_count = self._stack[-1]
        if last_name == name and last_count == self._count - 1:
            self.getOutputHandler().characters(' ')

    def characters_simple(self):
        self._count += 1


class Html2SaxParser(HTMLParser):
    """Turn arbitrary HTML events into XML-compliant SAX stream.
    """

    def __init__(self, handler):
        HTMLParser.__init__(self)
        self._handler = HtmlTagFixerFilter(handler)
        self._stack = []

    def _createAttrDict(self, attrs):
        result = {}
        for key, value in attrs:
            if value is None:
                value = key
            result[(None, key)] = value
        return result

    def close(self):
        # close everything still open
        stack = self._stack
        while stack:
            pushed_tag = stack.pop()
            self._handler.endElementNS((None, pushed_tag), None)
        HTMLParser.close(self)

    def handle_starttag(self, tag, attrs):
        if tag in IMMEDIATE_CLOSE_TAGS:
            self._handler.startElementNS((None, tag), None, {})
            self._handler.endElementNS((None, tag), None)
            return
        self._handler.startElementNS((None, tag), None,
                                    self._createAttrDict(attrs))
        self._stack.append(tag)

    def handle_endtag(self, tag):
        if tag in IMMEDIATE_CLOSE_TAGS:
            return
        popped = []
        stack = self._stack[:]
        while stack:
            pushed_tag = stack.pop()
            popped.append(pushed_tag)
            if tag == pushed_tag:
                for popped_tag in popped:
                    self._handler.endElementNS((None, popped_tag), None)
                self._stack = stack
                break
        # if stray end tag, don't do a thing with the stack

    def handle_startendtag(self, tag, attrs):
        self._handler.startElementNS((None, tag), None,
                                     self._createAttrDict(attrs))
        self._handler.endElementNS((None, tag), None)

    def handle_data(self, data):
        self._handler.characters(data)

    def handle_charref(self, name):
        # &#...; direct unicode codepoint
        if name.startswith('x'):
            # hex value
            value = int(name[1:], 16)
        else:
            # normal int
            value = int(name)
        try:
            c = unichr(value)
        except ValueError:
            # can't handle this, ignore
            return
        self._handler.characters(c)

    def handle_entityref(self, name):
        # &foo; named entity reference
        try:
            nr = name2codepoint[name]
        except KeyError:
            # can't handle this, ignore
            return
        try:
            c = unichr(nr)
        except ValueError:
            # can't handle this, ignore
            return
        self._handler.characters(c)

    def handle_comment(self, data):
        # skip comments
        pass

    def handle_decl(self, decl):
        # skip any decl
        pass

    def handle_pi(self, data):
        # skip processing instructions
        pass


def saxify(html, handler, validate=False):
    if validate:
        validator = HTMLParser()
        # This will raise an exception if it cannot process the html
        validator.feed(html)
        validator.close()
    parser = Html2SaxParser(handler)
    parser.feed(html)
    parser.close()
