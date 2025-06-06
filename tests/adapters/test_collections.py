# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Tests for the L{collections} L{miniamf.adapters._collections} module.

@since: 0.5
"""

import collections
import unittest

import miniamf


class CollectionsTestCase(unittest.TestCase):
    """
    """

    def encdec(self, encoding):
        return next(miniamf.decode(
            miniamf.encode(self.obj, encoding=encoding),
            encoding=encoding))


class DequeTestCase(CollectionsTestCase):
    """
    Tests for L{collections.deque}
    """

    def setUp(self):
        CollectionsTestCase.setUp(self)

        self.orig = [1, 2, 3]
        self.obj = collections.deque(self.orig)

    def test_amf0(self):
        self.assertEqual(self.encdec(miniamf.AMF0), self.orig)

    def test_amf3(self):
        self.assertEqual(self.encdec(miniamf.AMF3), self.orig)


class DefaultDictTestCase(CollectionsTestCase):
    """
    Tests for L{collections.defaultdict}
    """

    def setUp(self):
        CollectionsTestCase.setUp(self)

        s = 'mississippi'
        self.obj = collections.defaultdict(int)

        for k in s:
            self.obj[k] += 1

        self.orig = dict(self.obj)

    def test_amf0(self):
        self.assertEqual(self.encdec(miniamf.AMF0), self.orig)

    def test_amf3(self):
        self.assertEqual(self.encdec(miniamf.AMF3), self.orig)


class OrderedDictTestCase(CollectionsTestCase):
    """
    Tests for L{collections.OrderedDict}
    """

    def setUp(self):
        CollectionsTestCase.setUp(self)

        self.obj = collections.OrderedDict(
            [('apple', 4), ('banana', 3), ('orange', 2), ('pear', 1)]
        )
        self.orig = dict(self.obj)

    def test_amf0(self):
        self.assertEqual(self.encdec(miniamf.AMF0), self.orig)

    def test_amf3(self):
        self.assertEqual(self.encdec(miniamf.AMF3), self.orig)


class CounterTestCase(CollectionsTestCase):
    """
    Tests for L{collections.Counter}
    """

    def setUp(self):
        CollectionsTestCase.setUp(self)

        self.obj = collections.Counter({'blue': 3, 'red': 2, 'green': 1})

        self.orig = dict(self.obj)

    def test_amf0(self):
        self.assertEqual(self.encdec(miniamf.AMF0), self.orig)

    def test_amf3(self):
        self.assertEqual(self.encdec(miniamf.AMF3), self.orig)


class NamedTupleTestCase(CollectionsTestCase):
    """
    Tests for L{collections.namedtuple}
    """

    def setUp(self):
        CollectionsTestCase.setUp(self)

        user_vo = collections.namedtuple('user_vo', 'id name age')

        miniamf.add_type(user_vo, lambda obj, encoder: obj._asdict())

        self.obj = user_vo(1, 'Hadrien', 30)
        self.orig = self.obj._asdict()

    def test_amf0(self):
        self.assertEqual(self.encdec(miniamf.AMF0), self.orig)

    def test_amf3(self):
        self.assertEqual(self.encdec(miniamf.AMF3), self.orig)
