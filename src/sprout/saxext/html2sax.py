import HTMLParser as htmlparser
from HTMLParser import HTMLParser
import re

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
        self._handler.startElementNS((None, tag), None,
                                    self._createAttrDict(attrs))
        self._stack.append(tag)
       
    def handle_endtag(self, tag):
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
        # translate to unicode character
        raise NotImplementedError
    
    def handle_entityref(self, name):
        if name == 'lt':
            self._handler.characters('<')
        elif name == 'gt':
            self._handler.characters('>')
        elif name == 'amp':
            self._handler.characters('&')
            
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
