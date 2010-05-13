"""
Take SAX events, produce SAX events collapsing subsequent characters()
events into one if possible.
"""
from sprout.saxext.hookablehandler import HookableHandler

class CollapsingHandler(HookableHandler):
    def __init__(self, output_handler):
        HookableHandler.__init__(self, output_handler)
        self._buffer = []

    def characters_override(self, content):
        self._buffer.append(content)

    def _flushCharacters(self):
        if self._buffer:
            self.getOutputHandler().characters(''.join(self._buffer))
            self._buffer = []

    startElementNS_simple = _flushCharacters
    endElementNS_simple = _flushCharacters
    processingInstruction_simple = _flushCharacters
