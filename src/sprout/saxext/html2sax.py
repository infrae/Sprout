import HTMLParser as htmlparser
from HTMLParser import HTMLParser
import re
from htmlentitydefs import name2codepoint

IMMEDIATE_CLOSE_TAGS = ['br']

class Html2SaxParser(HTMLParser):
    """Turn arbitrary HTML events into XML-compliant SAX stream.
    """
    def __init__(self, handler):
        HTMLParser.__init__(self)
        self._handler = handler
        self._stack = []
        
    def _createAttrDict(self, attrs):
        result = {}
        for key, value in attrs:
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
        try:
            c = unichr(int(name))
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

def saxify(html, handler):
    parser = Html2SaxParser(handler)
    parser.feed(html)
    parser.close()
