# -*- coding: utf-8 -*-
#
# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Tests for Local Shared Object (LSO) Implementation.

@since: 0.1.0
"""

from io import BytesIO
import tempfile
import unittest
import warnings

import miniamf
from miniamf import sol
from miniamf.tests.util import check_buffer

warnings.simplefilter('ignore', RuntimeWarning)


class DecoderTestCase(unittest.TestCase):
    def test_header(self):
        bytes = (
            b'\x00\xbf\x00\x00\x00\x15TCSO\x00\x04\x00\x00\x00\x00\x00'
            b'\x05hello\x00\x00\x00\x00'
        )

        try:
            sol.decode(bytes)
        except Exception:
            self.fail("Error occurred during decoding stream")

    def test_invalid_header(self):
        bytes = (
            b'\x00\x00\x00\x00\x00\x15TCSO\x00\x04\x00\x00\x00\x00\x00'
            b'\x05hello\x00\x00\x00\x00'
        )
        self.assertRaises(miniamf.DecodeError, sol.decode, bytes)

    def test_invalid_header_length(self):
        bytes = (
            b'\x00\xbf\x00\x00\x00\x05TCSO\x00\x04\x00\x00\x00\x00\x00'
            b'\x05hello\x00\x00\x00\x00'
        )
        self.assertRaises(miniamf.DecodeError, sol.decode, bytes)

    def test_strict_header_length(self):
        bytes = (
            b'\x00\xbf\x00\x00\x00\x00TCSO\x00\x04\x00\x00\x00\x00\x00'
            b'\x05hello\x00\x00\x00\x00'
        )

        try:
            sol.decode(bytes, strict=False)
        except Exception:
            self.fail("Error occurred during decoding stream")

    def test_invalid_signature(self):
        bytes = (
            b'\x00\xbf\x00\x00\x00\x15ABCD\x00\x04\x00\x00\x00\x00\x00'
            b'\x05hello\x00\x00\x00\x00'
        )
        self.assertRaises(miniamf.DecodeError, sol.decode, bytes)

    def test_invalid_header_name_length(self):
        bytes = (
            b'\x00\xbf\x00\x00\x00\x15TCSO\x00\x04\x00\x00\x00\x00\x00'
            b'\x01hello\x00\x00\x00\x00'
        )
        self.assertRaises(miniamf.DecodeError, sol.decode, bytes)

    def test_invalid_header_padding(self):
        bytes = (
            b'\x00\xbf\x00\x00\x00\x15TCSO\x00\x04\x00\x00\x00\x00\x00'
            b'\x05hello\x00\x00\x01\x00'
        )
        self.assertRaises(miniamf.DecodeError, sol.decode, bytes)

    def test_unknown_encoding(self):
        bytes = (
            b'\x00\xbf\x00\x00\x00\x15TCSO\x00\x04\x00\x00\x00\x00\x00'
            b'\x05hello\x00\x00\x00\x01'
        )
        self.assertRaises(ValueError, sol.decode, bytes)

    def test_amf3(self):
        bytes = (
            b'\x00\xbf\x00\x00\x00aTCSO\x00\x04\x00\x00\x00\x00\x00\x08'
            b'EchoTest\x00\x00\x00\x03\x0fhttpUri\x06=http://localhost:8000'
            b'/gateway/\x00\x0frtmpUri\x06+rtmp://localhost/echo\x00'
        )

        self.assertEqual(
            sol.decode(bytes), (
                u'EchoTest',
                {
                    u'httpUri': u'http://localhost:8000/gateway/',
                    u'rtmpUri': u'rtmp://localhost/echo'
                }
            )
        )


class EncoderTestCase(unittest.TestCase):
    def test_encode_header(self):
        stream = sol.encode('hello', {})

        self.assertEqual(
            stream.getvalue(),
            b'\x00\xbf\x00\x00\x00\x15TCSO\x00\x04\x00\x00\x00\x00\x00'
            b'\x05hello\x00\x00\x00\x00'
        )

    def test_multiple_values(self):
        stream = sol.encode('hello', {'name': 'value', 'spam': 'eggs'})

        self.assertTrue(
            check_buffer(stream.getvalue(), HelperTestCase.contents)
        )

    def test_amf3(self):
        bytes = (
            b'\x00\xbf\x00\x00\x00aTCSO\x00\x04\x00\x00\x00\x00\x00\x08'
            b'EchoTest\x00\x00\x00\x03', (
                b'\x0fhttpUri\x06=http://localhost:8000/gateway/\x00',
                b'\x0frtmpUri\x06+rtmp://localhost/echo\x00'
            )
        )

        stream = sol.encode(
            u'EchoTest', {
                u'httpUri': u'http://localhost:8000/gateway/',
                u'rtmpUri': u'rtmp://localhost/echo'
            },
            encoding=miniamf.AMF3
        )

        self.assertTrue(check_buffer(stream.getvalue(), bytes))


class HelperTestCase(unittest.TestCase):
    contents = (
        b'\x00\xbf\x00\x00\x002TCSO\x00\x04\x00\x00\x00\x00\x00\x05hello'
        b'\x00\x00\x00\x00', (
            b'\x00\x04name\x02\x00\x05value\x00',
            b'\x00\x04spam\x02\x00\x04eggs\x00'
        )
    )

    contents_str = (
        b'\x00\xbf\x00\x00\x002TCSO\x00\x04\x00\x00\x00\x00\x00'
        b'\x05hello\x00\x00\x00\x00\x00\x04name\x02\x00\x05value\x00\x00'
        b'\x04spam\x02\x00\x04eggs\x00')

    def setUp(self):
        self.fp = tempfile.NamedTemporaryFile()
        self.file_name = self.fp.name

    def tearDown(self):
        self.fp.close()

    def _fill_file(self):
        self.fp.write(self.contents_str)
        self.fp.flush()

    def test_load_name(self):
        self._fill_file()

        s = sol.load(self.file_name)
        self.assertEqual(s.name, 'hello')
        self.assertEqual(s, {'name': 'value', 'spam': 'eggs'})

    def test_load_file(self):
        self._fill_file()
        y = self.fp.tell()
        self.fp.seek(0)

        s = sol.load(self.fp)
        self.assertEqual(s.name, 'hello')
        self.assertEqual(s, {'name': 'value', 'spam': 'eggs'})

        self.assertFalse(self.fp.closed)
        self.assertEqual(y, self.fp.tell())

    def test_save_name(self):
        s = sol.SOL('hello')
        s.update({'name': 'value', 'spam': 'eggs'})
        sol.save(s, self.file_name)

        self.fp.seek(0)
        self.assertTrue(check_buffer(self.fp.read(), self.contents))

    def test_save_file(self):
        s = sol.SOL('hello')
        s.update({'name': 'value', 'spam': 'eggs'})

        sol.save(s, self.fp)
        self.assertFalse(self.fp.closed)

        self.fp.seek(0)
        self.assertTrue(check_buffer(self.fp.read(), self.contents))


class SOLTestCase(unittest.TestCase):
    def test_create(self):
        s = sol.SOL('eggs')

        self.assertEqual(s, {})
        self.assertEqual(s.name, 'eggs')

    def test_save(self):
        s = sol.SOL('hello')
        s.update({'name': 'value', 'spam': 'eggs'})

        x = BytesIO()
        s.save(x)
        self.assertTrue(check_buffer(x.getvalue(), HelperTestCase.contents))
