from sprout.saxext.generator import XMLGenerator
from sprout.saxext import html2sax
import sys

class HTMLLimiter(XMLGenerator):
    """Fix (potentially unwellformed) HTML and limit the length of the text
        displayed.
    """

    def __init__(self, out=sys.stdout, encoding='UTF-8'):
        XMLGenerator.__init__(self, out, encoding)

        self._current_length = 0
        self._working = False
        self._stack = []
        # stole some code from saxext.collapser to get characters events
        # only emitted once for each piece of text (including entities)
        self._buffer = []

    def parse(self, html, maxlength=-1):
        """parse the html

            maxlength is the maximum amount of text displayed (excluding
            ignorable whitespace), a value < 0 returns the full html
        """
        self.maxlength = maxlength
        self._working = True
        html2sax.saxify(html, self)

    def startElementNS(self, name, qname, attrs):
        """Start element

            overridden so the text buffer can be maintained, as well
            as a stack to keep track of the elements that should get closed
            when self.maxlength is reached
        """
        self.flush()
        if not self._working:
            return
        self._stack.append((name, qname))
        XMLGenerator.startElementNS(self, name, qname, attrs)

    def endElementNS(self, name, qname):
        """End element"""
        self.flush()
        if not self._stack[-1] == (name, qname):
            return
        self._stack.pop()
        XMLGenerator.endElementNS(self, name, qname)

    def characters(self, content):
        """Handle character data

            rather than just writing it to the stream, buffer it, this
            makes keeping track of ignorable whitespace way easier
        """
        if not self._working:
            return
        self._buffer.append(content)

    def flush(self):
        """If there is text in the buffer, concatenate and write it"""
        content = ''.join(self._buffer)
        if (self.maxlength >= 0 and
                len(content.strip()) >= self.maxlength - self._current_length):
            content = content[:self.maxlength - self._current_length]
            self._working = False
        XMLGenerator.characters(self, content)
        # ignore ignorable whitespace, this is not perfect since it may
        # throw away spaces when they do get displayed..
        if content.strip():
            self._current_length += len(content)
        self._buffer = []

if __name__ == '__main__':
    # some example code, you can use this on the command line to clean
    # up and limit HTML files
    import sys
    if len(sys.argv) != 3:
        print 'usage: %s <html-file> <limit>' % sys.argv[0]
        sys.exit()
    fp = open(sys.argv[1])
    data = fp.read()
    fp.close()
    l = HTMLLimiter()
    l.parse(data, int(sys.argv[2]))
