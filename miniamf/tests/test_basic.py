# -*- encoding: utf-8 -*-
# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
General tests.

@since: 0.1.0
"""

from types import ModuleType
import unittest

import miniamf
from miniamf.tests.util import ClassCacheClearingTestCase, replace_dict, Spam


class ASObjectTestCase(unittest.TestCase):
    """
    I exercise all functionality relating to the L{ASObject<miniamf.ASObject>}
    class.
    """

    def test_init(self):
        bag = miniamf.ASObject(spam='eggs', baz='spam')

        self.assertEqual(bag, dict(spam='eggs', baz='spam'))
        self.assertEqual(bag.spam, 'eggs')
        self.assertEqual(bag.baz, 'spam')

    def test_eq(self):
        bag = miniamf.ASObject()

        self.assertEqual(bag, {})
        self.assertNotEqual(bag, {'spam': 'eggs'})

        bag2 = miniamf.ASObject()

        self.assertEqual(bag2, {})
        self.assertEqual(bag, bag2)
        self.assertNotEqual(bag, None)

    def test_setitem(self):
        bag = miniamf.ASObject()

        self.assertEqual(bag, {})

        bag['spam'] = 'eggs'

        self.assertEqual(bag.spam, 'eggs')

    def test_delitem(self):
        bag = miniamf.ASObject({'spam': 'eggs'})

        self.assertEqual(bag.spam, 'eggs')
        del bag['spam']

        self.assertRaises(AttributeError, lambda: bag.spam)

    def test_getitem(self):
        bag = miniamf.ASObject({'spam': 'eggs'})

        self.assertEqual(bag['spam'], 'eggs')

    def test_iter(self):
        bag = miniamf.ASObject({'spam': 'eggs'})

        x = []

        for k, v in bag.items():
            x.append((k, v))

        self.assertEqual(x, [('spam', 'eggs')])

    def test_hash(self):
        bag = miniamf.ASObject({'spam': 'eggs'})

        self.assertNotEqual(None, hash(bag))


class HelperTestCase(unittest.TestCase):
    """
    Tests all helper functions in C{miniamf.__init__}
    """

    def setUp(self):
        self.default_encoding = miniamf.DEFAULT_ENCODING

    def tearDown(self):
        miniamf.DEFAULT_ENCODING = self.default_encoding

    def test_get_decoder(self):
        self.assertRaises(ValueError, miniamf.get_decoder, 'spam')

        decoder = miniamf.get_decoder(miniamf.AMF0, stream=b'123', strict=True)
        self.assertEqual(decoder.stream.getvalue(), b'123')
        self.assertTrue(decoder.strict)

        decoder = miniamf.get_decoder(miniamf.AMF3, stream=b'456', strict=True)
        self.assertEqual(decoder.stream.getvalue(), b'456')
        self.assertTrue(decoder.strict)

    def test_get_encoder(self):
        miniamf.get_encoder(miniamf.AMF0)
        miniamf.get_encoder(miniamf.AMF3)
        self.assertRaises(ValueError, miniamf.get_encoder, b'spam')

        encoder = miniamf.get_encoder(miniamf.AMF0, stream=b'spam')
        self.assertEqual(encoder.stream.getvalue(), b'spam')
        self.assertFalse(encoder.strict)

        encoder = miniamf.get_encoder(miniamf.AMF3, stream=b'eggs')
        self.assertFalse(encoder.strict)

        encoder = miniamf.get_encoder(miniamf.AMF0, strict=True)
        self.assertTrue(encoder.strict)

        encoder = miniamf.get_encoder(miniamf.AMF3, strict=True)
        self.assertTrue(encoder.strict)

    def test_encode(self):
        self.assertEqual(
            miniamf.encode(u'connect', 1.0).getvalue(),
            b'\x06\x0fconnect\x05?\xf0\x00\x00\x00\x00\x00\x00'
        )

    def test_decode(self):
        self.assertEqual(
            list(miniamf.decode(
                b'\x06\x0fconnect\x05?\xf0\x00\x00\x00\x00\x00\x00')),
            [u'connect', 1.0]
        )

    def test_default_encoding(self):
        miniamf.DEFAULT_ENCODING = miniamf.AMF3

        x = miniamf.encode('foo').getvalue()

        self.assertEqual(x, b'\x06\x07foo')

        miniamf.DEFAULT_ENCODING = miniamf.AMF0

        x = miniamf.encode('foo').getvalue()

        self.assertEqual(x, b'\x02\x00\x03foo')


class UnregisterClassTestCase(ClassCacheClearingTestCase):
    def test_klass(self):
        alias = miniamf.register_class(Spam, 'spam.eggs')

        miniamf.unregister_class(Spam)
        self.assertTrue('spam.eggs' not in miniamf.CLASS_CACHE)
        self.assertTrue(Spam not in miniamf.CLASS_CACHE)
        self.assertTrue(alias not in miniamf.CLASS_CACHE)

    def test_alias(self):
        alias = miniamf.register_class(Spam, 'spam.eggs')

        miniamf.unregister_class('spam.eggs')
        self.assertTrue('spam.eggs' not in miniamf.CLASS_CACHE)
        self.assertTrue(alias not in miniamf.CLASS_CACHE)


class ClassLoaderTestCase(ClassCacheClearingTestCase):
    def test_register(self):
        self.assertTrue(chr not in miniamf.CLASS_LOADERS)
        miniamf.register_class_loader(chr)
        self.assertTrue(chr in miniamf.CLASS_LOADERS)

    def test_bad_register(self):
        self.assertRaises(TypeError, miniamf.register_class_loader, 1)
        miniamf.register_class_loader(ord)

    def test_unregister(self):
        self.assertTrue(chr not in miniamf.CLASS_LOADERS)
        miniamf.register_class_loader(chr)
        self.assertTrue(chr in miniamf.CLASS_LOADERS)

        miniamf.unregister_class_loader(chr)
        self.assertTrue(chr not in miniamf.CLASS_LOADERS)

        self.assertRaises(LookupError, miniamf.unregister_class_loader, chr)

    def test_load_class(self):
        def class_loader(x):
            self.assertEqual(x, 'spam.eggs')

            return Spam

        miniamf.register_class_loader(class_loader)

        self.assertTrue('spam.eggs' not in miniamf.CLASS_CACHE)
        miniamf.load_class('spam.eggs')
        self.assertTrue('spam.eggs' in miniamf.CLASS_CACHE)

    def test_load_unknown_class(self):
        def class_loader(x):
            return None

        miniamf.register_class_loader(class_loader)

        with self.assertRaises(miniamf.UnknownClassAlias):
            miniamf.load_class('spam.eggs')

    def test_load_class_by_alias(self):
        def class_loader(x):
            self.assertEqual(x, 'spam.eggs')
            return miniamf.ClassAlias(Spam, 'spam.eggs')

        miniamf.register_class_loader(class_loader)

        self.assertTrue('spam.eggs' not in miniamf.CLASS_CACHE)
        miniamf.load_class('spam.eggs')
        self.assertTrue('spam.eggs' in miniamf.CLASS_CACHE)

    def test_load_class_bad_return(self):
        def class_loader(x):
            return 'xyz'

        miniamf.register_class_loader(class_loader)

        self.assertRaises(TypeError, miniamf.load_class, 'spam.eggs')

    def test_load_class_by_module(self):
        miniamf.load_class('unittest.TestCase')

    def test_load_class_by_module_bad(self):
        with self.assertRaises(miniamf.UnknownClassAlias):
            miniamf.load_class('unittest.TestCase.')


class TypeMapTestCase(unittest.TestCase):
    def setUp(self):
        self.tm = miniamf.TYPE_MAP.copy()

        self.addCleanup(replace_dict, self.tm, miniamf.TYPE_MAP)

    def test_add_invalid(self):
        mod = ModuleType('spam')
        self.assertRaises(TypeError, miniamf.add_type, mod)
        self.assertRaises(TypeError, miniamf.add_type, {})
        self.assertRaises(TypeError, miniamf.add_type, 'spam')
        self.assertRaises(TypeError, miniamf.add_type, u'eggs')
        self.assertRaises(TypeError, miniamf.add_type, 1)
        self.assertRaises(TypeError, miniamf.add_type, 234234)
        self.assertRaises(TypeError, miniamf.add_type, 34.23)
        self.assertRaises(TypeError, miniamf.add_type, None)
        self.assertRaises(TypeError, miniamf.add_type, object())

        class A:
            pass

        self.assertRaises(TypeError, miniamf.add_type, A())

    def test_add_same(self):
        miniamf.add_type(chr)
        self.assertRaises(KeyError, miniamf.add_type, chr)

    def test_add_class(self):
        class A:
            pass

        class B(object):
            pass

        miniamf.add_type(A)
        self.assertTrue(A in miniamf.TYPE_MAP)

        miniamf.add_type(B)
        self.assertTrue(B in miniamf.TYPE_MAP)

    def test_add_callable(self):
        td = miniamf.add_type(ord)

        self.assertTrue(ord in miniamf.TYPE_MAP)
        self.assertTrue(td in miniamf.TYPE_MAP.values())

    def test_add_multiple(self):
        td = miniamf.add_type((chr,))

        class A(object):
            pass

        class B(object):
            pass

        class C(object):
            pass

        td = miniamf.add_type([A, B, C])
        self.assertEqual(td, miniamf.get_type([A, B, C]))

    def test_get_type(self):
        self.assertRaises(KeyError, miniamf.get_type, chr)
        td = miniamf.add_type((chr,))
        self.assertRaises(KeyError, miniamf.get_type, chr)

        td2 = miniamf.get_type((chr, ))
        self.assertEqual(td, td2)

        td2 = miniamf.get_type([chr, ])
        self.assertEqual(td, td2)

    def test_remove(self):
        self.assertRaises(KeyError, miniamf.remove_type, chr)
        td = miniamf.add_type((chr,))

        self.assertRaises(KeyError, miniamf.remove_type, chr)
        td2 = miniamf.remove_type((chr,))

        self.assertEqual(td, td2)


class ErrorClassMapTestCase(unittest.TestCase):
    """
    I test all functionality related to manipulating L{miniamf.ERROR_CLASS_MAP}
    """

    def setUp(self):
        self.map_copy = miniamf.ERROR_CLASS_MAP.copy()
        self.addCleanup(replace_dict, self.map_copy, miniamf.ERROR_CLASS_MAP)

    def test_add(self):
        class A:
            pass

        class B(Exception):
            pass

        self.assertRaises(TypeError, miniamf.add_error_class, None, 'a')

        # class A does not sub-class Exception
        self.assertRaises(TypeError, miniamf.add_error_class, A, 'a')

        miniamf.add_error_class(B, 'b')
        self.assertEqual(miniamf.ERROR_CLASS_MAP['b'], B)

        miniamf.add_error_class(B, 'a')
        self.assertEqual(miniamf.ERROR_CLASS_MAP['a'], B)

        class C(Exception):
            pass

        self.assertRaises(ValueError, miniamf.add_error_class, C, 'b')

    def test_remove(self):
        class B(Exception):
            pass

        miniamf.ERROR_CLASS_MAP['abc'] = B

        self.assertRaises(TypeError, miniamf.remove_error_class, None)

        miniamf.remove_error_class('abc')
        self.assertFalse('abc' in miniamf.ERROR_CLASS_MAP)
        self.assertRaises(KeyError, miniamf.ERROR_CLASS_MAP.__getitem__, 'abc')

        miniamf.ERROR_CLASS_MAP['abc'] = B

        miniamf.remove_error_class(B)

        self.assertRaises(KeyError, miniamf.ERROR_CLASS_MAP.__getitem__, 'abc')
        self.assertRaises(ValueError, miniamf.remove_error_class, B)
        self.assertRaises(ValueError, miniamf.remove_error_class, 'abc')


class DummyAlias(miniamf.ClassAlias):
    pass


class RegisterAliasTypeTestCase(unittest.TestCase):
    def setUp(self):
        self.old_aliases = miniamf.ALIAS_TYPES.copy()
        self.addCleanup(replace_dict, self.old_aliases, miniamf.ALIAS_TYPES)

    def test_bad_klass(self):
        self.assertRaises(TypeError, miniamf.register_alias_type, 1)

    def test_subclass(self):
        self.assertFalse(issubclass(self.__class__, miniamf.ClassAlias))
        with self.assertRaises(ValueError):
            miniamf.register_alias_type(self.__class__)

    def test_no_args(self):
        self.assertTrue(issubclass(DummyAlias, miniamf.ClassAlias))
        self.assertRaises(ValueError, miniamf.register_alias_type, DummyAlias)

    def test_type_args(self):
        self.assertTrue(issubclass(DummyAlias, miniamf.ClassAlias))
        self.assertRaises(TypeError,
                          miniamf.register_alias_type, DummyAlias, 1)

    def test_single(self):
        class A(object):
            pass

        miniamf.register_alias_type(DummyAlias, A)

        self.assertTrue(DummyAlias in miniamf.ALIAS_TYPES)
        self.assertEqual(miniamf.ALIAS_TYPES[DummyAlias], (A,))

    def test_multiple(self):
        class A(object):
            pass

        class B(object):
            pass

        with self.assertRaises(TypeError):
            miniamf.register_alias_type(DummyAlias, A, 'hello')

        miniamf.register_alias_type(DummyAlias, A, B)
        self.assertTrue(DummyAlias in miniamf.ALIAS_TYPES)
        self.assertEqual(miniamf.ALIAS_TYPES[DummyAlias], (A, B))

    def test_duplicate(self):
        class A(object):
            pass

        miniamf.register_alias_type(DummyAlias, A)

        with self.assertRaises(RuntimeError):
            miniamf.register_alias_type(DummyAlias, A)

    def test_unregister(self):
        """
        Tests for L{miniamf.unregister_alias_type}
        """
        class A(object):
            pass

        self.assertFalse(DummyAlias in miniamf.ALIAS_TYPES)
        self.assertEqual(miniamf.unregister_alias_type(A), None)

        miniamf.register_alias_type(DummyAlias, A)

        self.assertTrue(DummyAlias in miniamf.ALIAS_TYPES)
        self.assertEqual(miniamf.unregister_alias_type(DummyAlias), (A,))


class TypedObjectTestCase(unittest.TestCase):
    def test_externalised(self):
        o = miniamf.TypedObject(None)

        self.assertRaises(miniamf.DecodeError, o.__readamf__, None)
        self.assertRaises(miniamf.EncodeError, o.__writeamf__, None)

    def test_alias(self):
        class Foo:
            pass

        alias = miniamf.TypedObjectClassAlias(Foo, 'bar')

        self.assertEqual(alias.klass, miniamf.TypedObject)
        self.assertNotEqual(alias.klass, Foo)


class PackageTestCase(ClassCacheClearingTestCase):
    """
    Tests for L{miniamf.register_package}
    """

    class NewType(object):
        pass

    class ClassicType:
        pass

    def setUp(self):
        ClassCacheClearingTestCase.setUp(self)

        self.module = ModuleType("foo")

        self.module.Classic = self.ClassicType
        self.module.New = self.NewType
        self.module.b = b'binary'
        self.module.i = 12323
        self.module.f = 345.234
        self.module.u = u"Unicöde"
        self.module.l = ["list", "of", "junk"]
        self.module.d = {"foo": "bar", "baz": "gak"}
        self.module.obj = object()
        self.module.mod = self.module
        self.module.lam = lambda _: None

        self.NewType.__module__ = "foo"
        self.ClassicType.__module__ = "foo"

        self.spam_module = Spam.__module__
        Spam.__module__ = "foo"

        self.names = (self.module.__name__,)

    def tearDown(self):
        ClassCacheClearingTestCase.tearDown(self)

        Spam.__module__ = self.spam_module

        self.module.__name__ = self.names

    def check_module(self, r, base_package):
        self.assertEqual(len(r), 2)

        for c in [self.NewType, self.ClassicType]:
            alias = r[c]

            self.assertTrue(isinstance(alias, miniamf.ClassAlias))
            self.assertEqual(alias.klass, c)
            self.assertEqual(alias.alias, base_package + c.__name__)

    def test_module(self):
        r = miniamf.register_package(self.module, 'com.example')
        self.check_module(r, 'com.example.')

    def test_all(self):
        self.module.Spam = Spam

        self.module.__all__ = ['Classic', 'New']

        r = miniamf.register_package(self.module, 'com.example')
        self.check_module(r, 'com.example.')

    def test_ignore(self):
        self.module.Spam = Spam

        r = miniamf.register_package(self.module, 'com.example',
                                     ignore=['Spam'])
        self.check_module(r, 'com.example.')

    def test_separator(self):
        r = miniamf.register_package(self.module, 'com.example', separator='/')

        self.ClassicType.__module__ = 'com.example'
        self.NewType.__module__ = 'com.example'
        self.check_module(r, 'com.example/')

    def test_name(self):
        self.module.__name__ = 'spam.eggs'
        self.ClassicType.__module__ = 'spam.eggs'
        self.NewType.__module__ = 'spam.eggs'

        r = miniamf.register_package(self.module)
        self.check_module(r, 'spam.eggs.')

    def test_dict(self):
        """
        @see: #585
        """
        d = dict()
        d['Spam'] = Spam

        r = miniamf.register_package(d, 'com.example', strict=False)

        self.assertEqual(len(r), 1)

        alias = r[Spam]

        self.assertTrue(isinstance(alias, miniamf.ClassAlias))
        self.assertEqual(alias.klass, Spam)
        self.assertEqual(alias.alias, 'com.example.Spam')

    def test_odd(self):
        self.assertRaises(TypeError, miniamf.register_package, object())
        self.assertRaises(TypeError, miniamf.register_package, 1)
        self.assertRaises(TypeError, miniamf.register_package, 1.2)
        self.assertRaises(TypeError, miniamf.register_package, 23897492834)
        self.assertRaises(TypeError, miniamf.register_package, [])
        self.assertRaises(TypeError, miniamf.register_package, b'')
        self.assertRaises(TypeError, miniamf.register_package, u'')

    def test_strict(self):
        self.module.Spam = Spam

        Spam.__module__ = self.spam_module

        r = miniamf.register_package(self.module, 'com.example', strict=True)
        self.check_module(r, 'com.example.')

    def test_not_strict(self):
        self.module.Spam = Spam

        Spam.__module__ = self.spam_module

        r = miniamf.register_package(self.module, 'com.example', strict=False)

        self.assertEqual(len(r), 3)

        for c in [self.NewType, self.ClassicType, Spam]:
            alias = r[c]

            self.assertTrue(isinstance(alias, miniamf.ClassAlias))
            self.assertEqual(alias.klass, c)
            self.assertEqual(alias.alias, 'com.example.' + c.__name__)

    def test_list(self):
        class Foo:
            pass

        class Bar:
            pass

        ret = miniamf.register_package([Foo, Bar], 'spam.eggs')

        self.assertEqual(len(ret), 2)

        for c in [Foo, Bar]:
            alias = ret[c]

            self.assertTrue(isinstance(alias, miniamf.ClassAlias))
            self.assertEqual(alias.klass, c)
            self.assertEqual(alias.alias, 'spam.eggs.' + c.__name__)


class UndefinedTestCase(unittest.TestCase):
    """
    Tests for L{miniamf.Undefined}
    """

    def test_none(self):
        """
        L{miniamf.Undefined} is not referentially identical to C{None}.
        """
        self.assertFalse(miniamf.Undefined is None)

    def test_non_zero(self):
        """
        Truth test for L{miniamf.Undefined} == C{False}.
        """
        self.assertFalse(miniamf.Undefined)


class TestAMF0Codecs(unittest.TestCase):
    """
    Tests for getting encoder/decoder for AMF0 with extension support.
    """

    def test_default_decoder(self):
        """
        If the extension is available, it must be returned by default.
        """
        try:
            from miniamf._accel import amf0
        except ImportError:
            from miniamf import amf0

        decoder = miniamf.get_decoder(miniamf.AMF0)

        self.assertIsInstance(decoder, amf0.Decoder)

    def test_ext_decoder(self):
        """
        With `use_ext=True` specified, the extension must be returned.
        """
        try:
            from miniamf._accel import amf0
        except ImportError:
            self.skipTest('amf0 extension not available')

        decoder = miniamf.get_decoder(miniamf.AMF0, use_ext=True)

        self.assertIsInstance(decoder, amf0.Decoder)

    def test_pure_decoder(self):
        """
        With `use_ext=False` specified, the extension must NOT be returned.
        """
        from miniamf import amf0

        decoder = miniamf.get_decoder(miniamf.AMF0, use_ext=False)

        self.assertIsInstance(decoder, amf0.Decoder)

    def test_default_encoder(self):
        """
        If the extension is available, it must be returned by default.
        """
        try:
            from miniamf._accel import amf0
        except ImportError:
            from miniamf import amf0

        encoder = miniamf.get_encoder(miniamf.AMF0)

        self.assertIsInstance(encoder, amf0.Encoder)

    def test_ext_encoder(self):
        """
        With `use_ext=True` specified, the extension must be returned.
        """
        try:
            from miniamf._accel import amf0
        except ImportError:
            self.skipTest('amf0 extension not available')

        encoder = miniamf.get_encoder(miniamf.AMF0, use_ext=True)

        self.assertIsInstance(encoder, amf0.Encoder)

    def test_pure_encoder(self):
        """
        With `use_ext=False` specified, the extension must NOT be returned.
        """
        from miniamf import amf0

        encoder = miniamf.get_encoder(miniamf.AMF0, use_ext=False)

        self.assertIsInstance(encoder, amf0.Encoder)


class TestAMF3Codecs(unittest.TestCase):
    """
    Tests for getting encoder/decoder for amf3 with extension support.
    """

    def test_default_decoder(self):
        """
        If the extension is available, it must be returned by default.
        """
        try:
            from miniamf._accel import amf3
        except ImportError:
            from miniamf import amf3

        decoder = miniamf.get_decoder(miniamf.AMF3)

        self.assertIsInstance(decoder, amf3.Decoder)

    def test_ext_decoder(self):
        """
        With `use_ext=True` specified, the extension must be returned.
        """
        try:
            from miniamf._accel import amf3
        except ImportError:
            self.skipTest('amf3 extension not available')

        decoder = miniamf.get_decoder(miniamf.AMF3, use_ext=True)

        self.assertIsInstance(decoder, amf3.Decoder)

    def test_pure_decoder(self):
        """
        With `use_ext=False` specified, the extension must NOT be returned.
        """
        from miniamf import amf3

        decoder = miniamf.get_decoder(miniamf.AMF3, use_ext=False)

        self.assertIsInstance(decoder, amf3.Decoder)

    def test_default_encoder(self):
        """
        If the extension is available, it must be returned by default.
        """
        try:
            from miniamf._accel import amf3
        except ImportError:
            from miniamf import amf3

        encoder = miniamf.get_encoder(miniamf.AMF3)

        self.assertIsInstance(encoder, amf3.Encoder)

    def test_ext_encoder(self):
        """
        With `use_ext=True` specified, the extension must be returned.
        """
        try:
            from miniamf._accel import amf3
        except ImportError:
            self.skipTest('amf3 extension not available')

        encoder = miniamf.get_encoder(miniamf.AMF3, use_ext=True)

        self.assertIsInstance(encoder, amf3.Encoder)

    def test_pure_encoder(self):
        """
        With `use_ext=False` specified, the extension must NOT be returned.
        """
        from miniamf import amf3

        encoder = miniamf.get_encoder(miniamf.AMF3, use_ext=False)

        self.assertIsInstance(encoder, amf3.Encoder)
