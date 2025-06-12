# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Tests for the L{array} L{miniamf.adapters._array} module.

@since: 0.5
"""

import array
import unittest

import miniamf


class ArrayTestCase(unittest.TestCase):
    """
    """

    def setUp(self):
        self.orig = [ord('f'), ord('o'), ord('o')]

        self.obj = array.array('b')

        self.obj.append(ord('f'))
        self.obj.append(ord('o'))
        self.obj.append(ord('o'))

    def encdec(self, encoding):
        return next(miniamf.decode(
            miniamf.encode(self.obj, encoding=encoding),
            encoding=encoding))

    def test_amf0(self):
        self.assertEqual(self.encdec(miniamf.AMF0), self.orig)

    def test_amf3(self):
        self.assertEqual(self.encdec(miniamf.AMF3), self.orig)
