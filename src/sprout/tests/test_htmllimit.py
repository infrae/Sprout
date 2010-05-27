# -*- coding: utf-8 -*-

import unittest
import os
from StringIO import StringIO

from sprout import htmllimit


def makeXML(html, maxlength=-1):
    f = StringIO()
    limit = htmllimit.HTMLLimiter(f)
    limit.parse(html, maxlength)
    return f.getvalue()


def load_testfile(name):
    fp = open(
        os.path.join(
            os.path.dirname(
                os.path.abspath(__file__),
            ),
            'htmllimit_testdata',
            name,
        ),
        'r'
    )
    data = fp.read()
    fp.close()
    # remove trailing slash
    return data[:-1]


class HTMLLimitTestCase(unittest.TestCase):
    """Test case for the HTML limiter"""

    def setUp(self):
        self.data = load_testfile('start.html')

    def test_no_limit(self):
        self.assertEquals(load_testfile('fixed.html'),
                            makeXML(self.data))

    def test_limit_10(self):
        self.assertEquals(load_testfile('limit_10.html'),
                            makeXML(self.data, 10))

    def test_limit_8(self):
        self.assertEquals(load_testfile('limit_8.html'),
                            makeXML(self.data, 8))

    def test_limit_5(self):
        self.assertEquals(load_testfile('limit_5.html'),
                            makeXML(self.data, 5))

    def test_limit_4(self):
        self.assertEquals(load_testfile('limit_4.html'),
                            makeXML(self.data, 4))

    def test_limit_1(self):
        self.assertEquals(load_testfile('limit_1.html'),
                            makeXML(self.data, 1))


def test_suite():
    suite = unittest.TestSuite()
    for testcase in [HTMLLimitTestCase]:
        suite.addTest(unittest.makeSuite(testcase))
    return suite

