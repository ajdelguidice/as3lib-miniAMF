# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Tests for the C{decimal} module integration.
"""

import unittest
import decimal

import miniamf


class DecimalTestCase(unittest.TestCase):
    def test_amf0_encode(self):
        x = decimal.Decimal("1.23456463452345")

        self.assertEqual(
            miniamf.encode(x, encoding=miniamf.AMF0, strict=False).getvalue(),
            b'\x00?\xf3\xc0\xc6\xd8\xa18\xfa'
        )

        with self.assertRaises(miniamf.EncodeError):
            miniamf.encode(x, encoding=miniamf.AMF0, strict=True)

    def test_amf3_encode(self):
        x = decimal.Decimal("1.23456463452345")

        self.assertEqual(
            miniamf.encode(x, encoding=miniamf.AMF3, strict=False).getvalue(),
            b'\x05?\xf3\xc0\xc6\xd8\xa18\xfa'
        )

        with self.assertRaises(miniamf.EncodeError):
            miniamf.encode(x, encoding=miniamf.AMF3, strict=True)
