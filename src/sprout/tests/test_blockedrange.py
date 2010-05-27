import unittest
from sprout.blockedrange import Ranges


class BlockedRangesTestCase(unittest.TestCase):
    def test_noop(self):
        b = Ranges(0, 10)
        self.assertEquals([(0, 10)], b.getOpenRanges())

    def test_single_block(self):
        b = Ranges(0, 10)
        b.block(4, 6)
        self.assertEquals([(0, 4), (6, 10)],
                          b.getOpenRanges())
        self.assertEquals([(4, 6)],
                          b.getBlockedRanges())

    def test_empty_block(self):
        b = Ranges(0, 10)
        b.block(4, 6)
        b.block(5, 6)
        self.assertEquals([(0, 4), (6, 10)],
                          b.getOpenRanges())
        self.assertEquals([(4, 6)],
                           b.getBlockedRanges())

    def test_expand_block(self):
        b = Ranges(0, 100)
        b.block(40, 60)
        b.block(30, 70)
        self.assertEquals([(0, 30), (70, 100)],
                          b.getOpenRanges())
        self.assertEquals([(30, 70)],
                          b.getBlockedRanges())

    def test_separate_blocks(self):
        b = Ranges(0, 100)
        b.block(10, 20)
        b.block(60, 70)
        self.assertEquals([(0, 10), (20, 60), (70, 100)],
                          b.getOpenRanges())
        self.assertEquals([(10, 20), (60, 70)],
                          b.getBlockedRanges())

    def test_overlapping_blocks_start(self):
        b = Ranges(0, 100)
        b.block(25, 75)
        b.block(10, 30)
        self.assertEquals([(0, 10), (75, 100)],
                          b.getOpenRanges())
        self.assertEquals([(10, 75)],
                          b.getBlockedRanges())

    def test_overlapping_blocks_start_reverse(self):
        b = Ranges(0, 100)
        b.block(10, 30)
        b.block(25, 75)
        self.assertEquals([(0, 10), (75, 100)],
                          b.getOpenRanges())

    def test_overlapping_blocks_end(self):
        b = Ranges(0, 100)
        b.block(25, 75)
        b.block(70, 80)
        self.assertEquals([(0, 25), (80, 100)],
                          b.getOpenRanges())

    def test_overlapping_blocks_end_reverse(self):
        b = Ranges(0, 100)
        b.block(70, 80)
        b.block(25, 75)
        self.assertEquals([(0, 25), (80, 100)],
                          b.getOpenRanges())

    def test_multi_block(self):
        b = Ranges(0, 100)
        b.block(20, 30)
        b.block(35, 40)
        b.block(10, 50)
        self.assertEquals([(0, 10), (50, 100)],
                          b.getOpenRanges())

    def test_repeated_block(self):
        b = Ranges(0, 100)
        b.block(50, 60)
        b.block(50, 60)
        self.assertEquals([(0, 50), (60, 100)],
                          b.getOpenRanges())

    def test_subsequent_block(self):
        b = Ranges(0, 100)
        b.block(50, 60)
        b.block(60, 70)
        self.assertEquals([(0, 50), (70, 100)],
                          b.getOpenRanges())

    def test_subsequent_block_reverse(self):
        b = Ranges(0, 100)
        b.block(60, 70)
        b.block(50, 60)
        self.assertEquals([(0, 50), (70, 100)],
                          b.getOpenRanges())

    def test_block_all(self):
        b = Ranges(0, 10)
        b.block(0, 10)
        self.assertEquals([],
                          b.getOpenRanges())
        self.assertEquals([(0, 10)],
                          b.getBlockedRanges())
        self.assertEquals([(0, 10, False)],
                           b.getRanges())


def test_suite():
    suite = unittest.TestSuite()
    for testcase in [BlockedRangesTestCase]:
        suite.addTest(unittest.makeSuite(testcase))
    return suite


