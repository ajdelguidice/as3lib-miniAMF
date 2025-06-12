# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Tests for the C{sets} module integration.
"""

import unittest

import miniamf


# All set types are mapped to sorted tuples.
class BaseTestCase(unittest.TestCase):
    def amf0_encode_test(self, ty):

        x = ty(['1', '2', '3'])
        self.assertEqual(
            miniamf.encode(x, encoding=miniamf.AMF0).getvalue(),
            b'\n\x00\x00\x00\x03'
            b'\x02\x00\x011'
            b'\x02\x00\x012'
            b'\x02\x00\x013'
        )

        y = ty(['z', 'x', 'c', 'v'])
        self.assertEqual(
            miniamf.encode(y, encoding=miniamf.AMF0).getvalue(),
            b'\n\x00\x00\x00\x04'
            b'\x02\x00\x01c'
            b'\x02\x00\x01v'
            b'\x02\x00\x01x'
            b'\x02\x00\x01z'
        )

    def amf3_encode_test(self, ty):

        x = ty(['1', '2', '3'])
        self.assertEqual(
            miniamf.encode(x, encoding=miniamf.AMF3).getvalue(),
            b'\t\x07\x01'
            b'\x06\x031'
            b'\x06\x032'
            b'\x06\x033'
        )

        y = ty(['z', 'x', 'c', 'v'])
        self.assertEqual(
            miniamf.encode(y, encoding=miniamf.AMF3).getvalue(),
            b'\t\t\x01'
            b'\x06\x03c'
            b'\x06\x03v'
            b'\x06\x03x'
            b'\x06\x03z'
        )


class BuiltinSetTypesTestCase(BaseTestCase):
    def test_amf0_set(self):
        self.amf0_encode_test(set)

    def test_amf3_set(self):
        self.amf3_encode_test(set)

    def test_amf0_frozenset(self):
        self.amf0_encode_test(frozenset)

    def test_amf3_frozenset(self):
        self.amf3_encode_test(frozenset)


# The sets module was removed in Python 3.
try:
    ModuleNotFoundError
except NameError:
    ModuleNotFoundError = ImportError

try:
    import sets

    class LibrarySetTypesTestCase(BaseTestCase):
        def test_amf0_Set(self):
            self.amf0_encode_test(sets.Set)

        def test_amf3_Set(self):
            self.amf3_encode_test(sets.Set)

        def test_amf0_ImmutableSet(self):
            self.amf0_encode_test(sets.ImmutableSet)

        def test_amf3_ImmutableSet(self):
            self.amf3_encode_test(sets.ImmutableSet)

except ModuleNotFoundError:
    pass
