class Ranges:
    """A set of ranges that can be blocked.

    Progressively subranges can be removed and the object maintains what
    ranges are left.
    """
    def __init__(self, s, e):
        self._s = s
        self._e = e
        self._open = [(s, e)]

    def block(self, i, j):
        """Block another subrange.
        """
        open = []
        # XXX could use bisect here to target possibly affected ranges,
        # which might optimize it for complicated situations
        for s, e in self._open:
            # if there is overlap
            #  s..i...j..e
            if s < i < e and s <= j < e:
                open.append((s, i))
                open.append((j, e))
            # i..s..e..j
            elif i <= s and j >= e:
                # all wiped out
                pass
            # s..i...e...j
            elif s < i < e:
                open.append((s, i))
            # i...s...j...e
            elif s <= j < e:
                open.append((j, e))
            else:
                open.append((s, e))
        self._open = open

    def getOpenRanges(self):
        """Get all ranges that are still open.
        """
        return self._open

    def getBlockedRanges(self):
        """Get all the ranges that are blocked.
        """
        return [r[:2] for r in self.getRanges() if not r[2]]

    def getRanges(self):
        """Get all ranges, with a third element indicating blocked status.

        True if open.
        """
        ranges = []
        last_e = self._s
        e = 0
        for s, e in self._open:
            if last_e != s:
                ranges.append((last_e, s, False))
            ranges.append((s, e, True))
            last_e = e
        if e != self._e:
            ranges.append((e, self._e, False))
        return ranges
