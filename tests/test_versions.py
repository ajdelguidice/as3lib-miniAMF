# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Tests for L{miniamf.version}
"""

import unittest

from miniamf import versions


class VersionTestCase(unittest.TestCase):
    """
    Tests for L{miniamf.version.get_version}
    """

    def test_version(self):
        self.assertEqual(versions.get_version((0, 0)), u"0.0")
        self.assertEqual(versions.get_version((0, 1)), u"0.1")
        self.assertEqual(versions.get_version((3, 2)), u"3.2")
        self.assertEqual(versions.get_version((3, 2, 1)), u"3.2.1")

        self.assertEqual(
            versions.get_version((3, 2, 1, b'alpha')),
            u"3.2.1alpha"
        )

        self.assertEqual(
            versions.get_version((3, 2, 1, u"final")),
            u"3.2.1final"
        )

    def test_class(self):
        V = versions.Version

        v1 = V(0, 1)

        self.assertEqual(v1, (0, 1))
        self.assertEqual(str(v1), u"0.1")

        v2 = V(3, 2, 1, u"final")

        self.assertEqual(v2, (3, 2, 1, u"final"))
        self.assertEqual(str(v2), u"3.2.1final")

        self.assertTrue(v2 > v1)
