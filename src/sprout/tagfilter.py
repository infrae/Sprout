import re
try:
    set
except NameError:
    from sets import Set as set

from htmlentitydefs import name2codepoint
from sprout.blockedrange import Ranges

start_tag_re = re.compile(r"""
  <[a-zA-Z][-.a-zA-Z0-9:_]*          # tag name
  (?:\s+                             # whitespace before attribute name
    (?:[a-zA-Z_][-.:a-zA-Z0-9_]*     # attribute name
      (?:\s*=\s*                     # value indicator
        (?:'[^']*'                   # LITA-enclosed value
          |\"[^\"]*\"                # LIT-enclosed value
          |[^'\">\s]+                # bare value
         )
       )?
     )
   )*
  \s*                                # trailing whitespace
  /?                                 # could be singleton tag
  >
""", re.VERBOSE)

tagfind = re.compile('[a-zA-Z][-.a-zA-Z0-9:_]*')
attrfind = re.compile(
    r'\s*([a-zA-Z_][-.:a-zA-Z_0-9]*)(\s*=\s*'
    r'(\'[^\']*\'|"[^"]*"|[-a-zA-Z0-9./,:;+*%?!&$\(\)_#=~]*))?')



class TagFilter:
    """Can filter XMLish text escaping any tags that are not known.

    This is definitely *not* a normal way to treat XML, but may be useful
    to clean up messy user input with mistakes, such as HTML.

    This right now only supports open tags and closing tags.
    """

    def __init__(self, html_entities=False):
        self._elements = {}
        if html_entities:
            entity_names = ['&%s;' % name for name in name2codepoint.keys()]
        else:
            entity_names = ['&amp;', '&gt;', '&lt;']
        self._entities = re.compile('|'.join(entity_names),
                                    re.IGNORECASE | re.MULTILINE)

    def registerElement(self, name,
                        attribute_names=None,
                        optional_attribute_names=None):
        attribute_names = set(attribute_names or [])
        optional_attribute_names = set(optional_attribute_names or [])
        all_attribute_names = attribute_names.union(optional_attribute_names)
        self._elements[name] = attribute_names, all_attribute_names

    def getElementNames(self):
        return self._elements.keys()

    def findNonElements(self, s):
        """Given a string, find returns a Ranges object.

        Ranges that are valid tags will be blocked.
        """
        b = Ranges(0, len(s))
        for name, (required_attrnames, attrnames) in self._elements.items():
            # block all start tags
            q = re.compile('<%s' % name, re.IGNORECASE | re.MULTILINE)
            i = 0
            while 1:
                m = q.search(s, i)
                if m is None:
                    break
                index = m.start()
                i = m.end()
                # find end of pattern and block range for it
                m = start_tag_re.match(s, index)
                if m is not None:
                    # but only if attributes are the same
                    text_attrnames = set(
                        self.attribute_names(s, m.start(), m.end()))
                    # must have all required attribute names and
                    # be a subset of all possible attribute names
                    if (required_attrnames.issubset(text_attrnames) and
                        text_attrnames.issubset(attrnames)):
                        b.block(m.start(), m.end())
            # block all end tags
            q = re.compile('</%s>' % name, re.IGNORECASE | re.MULTILINE)
            i = 0
            while 1:
                m = q.search(s, i)
                if m is None:
                    break
                index = m.start()
                i = m.end()
                b.block(index, i)
        # block all unknown entities
        i = 0
        while 1:
            m = self._entities.search(s, i)
            if m is None:
                break
            index = m.start()
            i = m.end()
            b.block(index, i)
        return b

    def escapeNonElements(self, text):
        result = []
        b = self.findNonElements(text)
        for s, e, open in b.getRanges():
            subs = text[s:e]
            if open:
                subs = subs.replace('&', '&amp;')
                subs = subs.replace('<', '&lt;')
                subs = subs.replace('>', '&gt;')
            result.append(subs)
        return ''.join(result)

    def attribute_names(self, rawdata, i, j):
        result = []
        match = tagfind.match(rawdata, i + 1)
        k = match.end()

        while k < j:
            m = attrfind.match(rawdata, k)
            if not m:
                break
            attrname = m.group(1)
            result.append(attrname.lower())
            k = m.end()
        return result
