# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
PyAMF Google adapter tests.

@since: 0.3.1
"""

import datetime
import struct

import miniamf
from miniamf import amf3

from miniamf.tests import util
from miniamf.tests.adapters import google

Spam = util.Spam


if google.has_appengine_sdk():
    from google.appengine.ext import db
    from google.appengine.ext.db import polymodel

    from . import _xdb_models as models

    adapter = miniamf.get_adapter('google.appengine.ext.db')


class BaseTestCase(google.BaseTestCase):
    def decode(self, bytes, encoding=miniamf.AMF3):
        decoded = list(miniamf.decode(bytes, encoding=encoding))

        if len(decoded) == 1:
            return decoded[0]

        return decoded

    def encodeKey(self, key, encoding):
        """
        Returns an AMF encoded representation of a L{db.Key} instance.

        @param key: The L{db.Key} to be encoded.
        @type key: L{db.Key}
        @param encoding: The AMF version.
        """
        if hasattr(key, 'key'):
            # we have a db.Model instance
            try:
                key = key.key()
            except db.NotSavedError:
                key = None

        if not key:
            # the AMF representation of None
            if encoding == miniamf.AMF3:
                return b'\x01'

            return b'\x05'

        if hasattr(key, 'decode'):
            size = len(key.decode('utf-8'))
        else:
            size = len(str(key))

        if hasattr(key, 'encode'):
            key = key.encode('utf-8')
        else:
            key = str(key).encode('utf-8')

        if encoding == miniamf.AMF3:
            return b'\x06%b%b' % (
                amf3.encode_int(size << 1 | amf3.REFERENCE_BIT), key)

        return b'\x02%b%b' % (struct.pack('>H', size), key)


class JessicaFactory(object):
    """
    Provides jessica!
    """

    jessica_attrs = {
        'name': 'Jessica',
        'type': 'cat',
        'birthdate': datetime.date(1986, 10, 2),
        'weight_in_pounds': 5,
        'spayed_or_neutered': False
    }

    @classmethod
    def makeJessica(kls, cls, **kwargs):
        j_kwargs = kls.jessica_attrs.copy()

        j_kwargs.update(kwargs)

        return cls(**j_kwargs)


class EncodingModelTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)

        self.jessica = JessicaFactory.makeJessica(models.PetModel)

    def test_amf0(self):
        encoded = (
            b'\x03', (
                b'\x00\x04_key%s' % (self.encodeKey(self.jessica, miniamf.AMF0)),
                b'\x00\tbirthdate\x0bB^\xc4\xae\xaa\x00\x00\x00\x00\x00',
                b'\x00\x04name\x02\x00\x07Jessica',
                b'\x00\x12spayed_or_neutered\x01\x00',
                b'\x00\x04type\x02\x00\x03cat',
                b'\x00\x10weight_in_pounds\x00@\x14\x00\x00\x00\x00\x00\x00'
            ),
            b'\x00\x00\t'
        )

        self.assertEncodes(self.jessica, encoded, encoding=miniamf.AMF0)

    def test_amf3(self):
        bytes = (
            b'\n\x0b\x01', (
                b'\t_key%s' % (self.encodeKey(self.jessica, miniamf.AMF3)),
                b'\x13birthdate\x08\x01B^\xc4\xae\xaa\x00\x00\x00',
                b'\tname\x06\x0fJessica',
                b'%spayed_or_neutered\x02'
                b'\ttype\x06\x07cat',
                b'!weight_in_pounds\x04\x05',
            ), b'\x01')

        self.assertEncodes(self.jessica, bytes, encoding=miniamf.AMF3)

    def test_save_amf0(self):
        self.jessica.put()

        bytes = (b'\x03', (
            b'\x00\x04_key%s' % self.encodeKey(self.jessica, miniamf.AMF0),
            b'\x00\tbirthdate\x0bB^\xc4\xae\xaa\x00\x00\x00\x00\x00',
            b'\x00\x04name\x02\x00\x07Jessica',
            b'\x00\x12spayed_or_neutered\x01\x00',
            b'\x00\x04type\x02\x00\x03cat',
            b'\x00\x10weight_in_pounds\x00@\x14\x00\x00\x00\x00\x00\x00'),
            b'\x00\x00\t')

        self.assertEncodes(self.jessica, bytes, encoding=miniamf.AMF0)

    def test_save_amf3(self):
        self.jessica.put()

        bytes = (
            b'\n\x0b\x01', (
                b'\t_key%s' % self.encodeKey(self.jessica, miniamf.AMF3),
                b'\x13birthdate\x08\x01B^\xc4\xae\xaa\x00\x00\x00',
                b'\tname\x06\x0fJessica',
                b'%spayed_or_neutered\x02',
                b'\ttype\x06\x07cat',
                b'!weight_in_pounds\x04\x05',
            ), b'\x01'
        )

        self.assertEncodes(self.jessica, bytes, encoding=miniamf.AMF3)

    def test_alias_amf0(self):
        miniamf.register_class(models.PetModel, 'Pet')

        bytes = (
            b'\x10\x00\x03Pet', (
                b'\x00\x04_key%s' % self.encodeKey(self.jessica, miniamf.AMF0),
                b'\x00\tbirthdate\x0bB^\xc4\xae\xaa\x00\x00\x00\x00\x00',
                b'\x00\x04name\x02\x00\x07Jessica',
                b'\x00\x12spayed_or_neutered\x01\x00',
                b'\x00\x04type\x02\x00\x03cat',
                b'\x00\x10weight_in_pounds\x00@\x14\x00\x00\x00\x00\x00\x00'
            ),
            b'\x00\x00\t'
        )

        self.assertEncodes(self.jessica, bytes, encoding=miniamf.AMF0)

    def test_alias_amf3(self):
        miniamf.register_class(models.PetModel, 'Pet')

        bytes = (
            b'\n\x0b\x07Pet', (
                b'\t_key%s' % self.encodeKey(self.jessica, miniamf.AMF3),
                b'\x13birthdate\x08\x01B^\xc4\xae\xaa\x00\x00\x00',
                b'\x07foo\x06\x07bar',
                b'\tname\x06\x0fJessica',
                b'%spayed_or_neutered\x02',
                b'\ttype\x06\x07cat',
                b'!weight_in_pounds\x04\x05',
            ), b'\x01'
        )

        self.assertEncodes(self.jessica, bytes, encoding=miniamf.AMF3)


class EncodingExpandoTestCase(BaseTestCase):
    """
    Tests for encoding L{db.Expando} classes
    """

    def setUp(self):
        BaseTestCase.setUp(self)

        self.jessica = JessicaFactory.makeJessica(
            models.PetExpando, foo='bar'
        )

    def test_amf0(self):
        bytes = (
            b'\x03', (
                b'\x00\x04_key%s' % self.encodeKey(self.jessica, miniamf.AMF0),
                b'\x00\tbirthdate\x0bB^\xc4\xae\xaa\x00\x00\x00\x00\x00',
                b'\x00\x03foo\x02\x00\x03bar'
                b'\x00\x04name\x02\x00\x07Jessica',
                b'\x00\x12spayed_or_neutered\x01\x00',
                b'\x00\x04type\x02\x00\x03cat',
                b'\x00\x10weight_in_pounds\x00@\x14\x00\x00\x00\x00\x00\x00',
            ),
            b'\x00\x00\t'
        )

        self.assertEncodes(self.jessica, bytes, encoding=miniamf.AMF0)

    def test_amf3(self):
        bytes = (
            b'\n\x0b\x01', (
                b'\t_key%s' % self.encodeKey(self.jessica, miniamf.AMF3),
                b'\x13birthdate\x08\x01B^\xc4\xae\xaa\x00\x00\x00',
                b'\x07foo\x06\x07bar',
                b'\tname\x06\x0fJessica',
                b'%spayed_or_neutered\x02',
                b'\ttype\x06\x07cat',
                b'!weight_in_pounds\x04\x05',
            ), b'\x01'
        )

        self.assertEncodes(self.jessica, bytes, encoding=miniamf.AMF3)

    def test_save_amf0(self):
        self.jessica.put()

        bytes = miniamf.encode(self.jessica, encoding=miniamf.AMF0).getvalue()

        self.assertBuffer(bytes, (b'\x03', (
            b'\x00\x04_key%s' % self.encodeKey(self.jessica, miniamf.AMF0),
            b'\x00\tbirthdate\x0bB^\xc4\xae\xaa\x00\x00\x00\x00\x00',
            b'\x00\x03foo\x02\x00\x03bar',
            b'\x00\x04name\x02\x00\x07Jessica',
            b'\x00\x12spayed_or_neutered\x01\x00',
            b'\x00\x04type\x02\x00\x03cat',
            b'\x00\x10weight_in_pounds\x00@\x14\x00\x00\x00\x00\x00\x00',
        ), b'\x00\x00\t'
        ))

    def test_save_amf3(self):
        self.jessica.put()

        bytes = (
            b'\n\x0b\x01', (
                b'\t_key%s' % self.encodeKey(self.jessica, miniamf.AMF3),
                b'\x13birthdate\x08\x01B^\xc4\xae\xaa\x00\x00\x00',
                b'\x07foo\x06\x07bar',
                b'\tname\x06\x0fJessica',
                b'%spayed_or_neutered\x02'
                b'\ttype\x06\x07cat',
                b'!weight_in_pounds\x04\x05',
            ), b'\x01')

        self.assertEncodes(self.jessica, bytes, encoding=miniamf.AMF3)

    def test_alias_amf0(self):
        miniamf.register_class(models.PetExpando, 'Pet')
        bytes = miniamf.encode(self.jessica, encoding=miniamf.AMF0).getvalue()

        self.assertBuffer(bytes, (b'\x10\x00\x03Pet', (
            b'\x00\x04_key%s' % self.encodeKey(self.jessica, miniamf.AMF0),
            b'\x00\tbirthdate\x0bB^\xc4\xae\xaa\x00\x00\x00\x00\x00',
            b'\x00\x04name\x02\x00\x07Jessica',
            b'\x00\x12spayed_or_neutered\x01\x00',
            b'\x00\x04type\x02\x00\x03cat',
            b'\x00\x10weight_in_pounds\x00@\x14\x00\x00\x00\x00\x00\x00',
            b'\x00\x03foo\x02\x00\x03bar'),
            b'\x00\x00\t'))

    def test_alias_amf3(self):
        miniamf.register_class(models.PetExpando, 'Pet')

        bytes = (
            b'\n\x0b\x07Pet', (
                b'\t_key%s' % self.encodeKey(self.jessica, miniamf.AMF3),
                b'\x13birthdate\x08\x01B^\xc4\xae\xaa\x00\x00\x00',
                b'\x07foo\x06\x07bar',
                b'\tname\x06\x0fJessica',
                b'%spayed_or_neutered\x02',
                b'\ttype\x06\x07cat',
                b'!weight_in_pounds\x04\x05',
            ), b'\x01')

        self.assertEncodes(self.jessica, bytes, encoding=miniamf.AMF3)


class EncodingReferencesTestCase(BaseTestCase):
    """
    This test case refers to L{db.ReferenceProperty<http://code.google.com/app
    engine/docs/datastore/typesandpropertyclasses.html#ReferenceProperty>},
    not AMF references.
    """

    def test_model(self):
        a = models.Author(name='Jane Austen')
        a.put()

        amf0_k = self.encodeKey(a, miniamf.AMF0)
        amf3_k = self.encodeKey(a, miniamf.AMF3)

        b = models.Novel(title='Sense and Sensibility', author=a)

        self.assertIdentical(b.author, a)

        bytes = (
            b'\x03', (
                b'\x00\x04_key' + amf0_k,
                b'\x00\x06author\x03', (
                    b'\x00\x04_key\x05',
                    b'\x00\x04name\x02\x00\x0bJane Austen',
                ),
                b'\x00\x05title\x02\x00\x15Sense and Sensibility',
                b'\x00\x00\t'
            ),
            b'\x00\x00\t')

        self.assertEncodes(b, bytes, encoding=miniamf.AMF0)

        bytes = (
            b'\n\x0b\x01', (
                b'\t_key\x01',
                b'\rauthor\n\x0b\x01', (
                    b'\x00' + amf3_k,
                    b'\tname\x06\x17Jane Austen',
                    b'\x01'),
                b'\x0btitle\x06+Sense and Sensibility',
                b'\x01'))

        self.assertEncodes(b, bytes, encoding=miniamf.AMF3)

        # now test with aliases ..
        miniamf.register_class(models.Author, 'Author')
        miniamf.register_class(models.Novel, 'Novel')

        bytes = (
            b'\x10\x00\x05Novel', (
                b'\x00\x05title\x02\x00\x15Sense and Sensibility',
                b'\x00\x04_key' + amf0_k,
                b'\x00\x06author\x10\x00\x06Author', (
                    b'\x00\x04name\x02\x00\x0bJane Austen',
                    b'\x00\x04_key\x05'
                ),
                b'\x00\x00\t'
            ),
            b'\x00\x00\t')

        self.assertEncodes(b, bytes, encoding=miniamf.AMF0)

        bytes = (
            b'\n\x0b\x0bNovel', (
                b'\t_key\x01',
                b'\rauthor\n\x0b\rAuthor', (
                    b'\x02' + amf3_k,
                    b'\tname\x06\x17Jane Austen'
                    b'\x01'),
                b'\x0btitle\x06+Sense and Sensibility',
                b'\x01'))

        self.assertEncodes(b, bytes, encoding=miniamf.AMF3)

    def test_expando(self):
        class Author(db.Expando):
            name = db.StringProperty()

        class Novel(db.Expando):
            title = db.StringProperty()
            author = db.ReferenceProperty(Author)

        a = Author(name='Jane Austen')
        a.put()
        k = str(a.key())
        k_bytes = k.encode('utf-8')

        amf0_k = struct.pack('>H', len(k)) + k_bytes
        amf3_k = amf3.encode_int(len(k) << 1 | amf3.REFERENCE_BIT) + k_bytes

        b = Novel(title='Sense and Sensibility', author=a)

        self.assertIdentical(b.author, a)

        bytes = (
            b'\x03', (
                b'\x00\x05title\x02\x00\x15Sense and Sensibility',
                b'\x00\x04_key\x02' + amf0_k,
                b'\x00\x06author\x03', (
                    b'\x00\x04name\x02\x00\x0bJane Austen',
                    b'\x00\x04_key\x05'
                ),
                b'\x00\x00\t'
            ),
            b'\x00\x00\t')

        self.assertEncodes(b, bytes, encoding=miniamf.AMF0)

        bytes = (
            b'\n\x0b\x01', ((
                b'\t_key\x01',
                b'\rauthor\n\x0b\x01', (
                    b'\x00\x06' + amf3_k,
                    b'\tname\x06\x17Jane Austen\x01'
                ), b'\x02\x01'),
                b'\x0btitle\x06+Sense and Sensibility'
            ),
            b'\x01')

        self.assertEncodes(b, bytes, encoding=miniamf.AMF3)

        # now test with aliases ..
        miniamf.register_class(Author, 'Author')
        miniamf.register_class(Novel, 'Novel')

        bytes = (
            b'\x10\x00\x05Novel', (
                b'\x00\x05title\x02\x00\x15Sense and Sensibility',
                b'\x00\x04_key\x02' + amf0_k,
                b'\x00\x06author\x10\x00\x06Author', (
                    b'\x00\x04name\x02\x00\x0bJane Austen',
                    b'\x00\x04_key\x05'
                ),
                b'\x00\x00\t'
            ),
            b'\x00\x00\t')

        self.assertEncodes(b, bytes, encoding=miniamf.AMF0)

        bytes = (
            b'\n\x0b\x0bNovel', ((
                b'\t_key\x01',
                b'\rauthor\n\x0b\rAuthor', (
                    b'\x02\x06' + amf3_k,
                    b'\tname\x06\x17Jane Austen\x01'
                ), b'\x06\x01'),
                b'\x0btitle\x06+Sense and Sensibility'
            ),
            b'\x01')

        self.assertEncodes(b, bytes, encoding=miniamf.AMF3)

    def test_dynamic_property_referenced_object(self):
        a = models.Author(name='Jane Austen')
        a.put()

        b = models.Novel(title='Sense and Sensibility', author=a)
        b.put()

        x = db.get(b.key())
        foo = [1, 2, 3]

        x.author.bar = foo

        ek = self.encodeKey(x, miniamf.AMF0)
        el = self.encodeKey(a, miniamf.AMF0)

        bytes = (
            b'\x03', (
                b'\x00\x05title\x02\x00\x15Sense and Sensibility',
                b'\x00\x04_key' + ek,
                b'\x00\x06author\x03', (
                    b'\x00\x03bar\n\x00\x00\x00\x03\x00?\xf0\x00\x00\x00\x00'
                    b'\x00\x00\x00@\x00\x00\x00\x00\x00\x00\x00\x00@\x08\x00'
                    b'\x00\x00\x00\x00\x00',
                    b'\x00\x04name\x02\x00\x0bJane Austen',
                    b'\x00\x04_key' + el
                ),
                b'\x00\x00\t'
            ),
            b'\x00\x00\t')

        self.assertEncodes(x, bytes, encoding=miniamf.AMF0)


class ListPropertyTestCase(BaseTestCase):
    """
    Tests for L{db.ListProperty} properties.
    """

    def setUp(self):
        BaseTestCase.setUp(self)

        self.obj = models.ListModel()
        self.obj.numbers = [2, 4, 6, 8, 10]

    def test_encode_amf0(self):
        bytes = (
            b'\x03', (
                b'\x00\x04_key\x05',
                b'\x00\x07numbers\n\x00\x00\x00\x05\x00@'
                b'\x00\x00\x00\x00\x00\x00\x00\x00@\x10\x00\x00\x00\x00\x00'
                b'\x00\x00@\x18\x00\x00\x00\x00\x00\x00\x00@\x20\x00\x00\x00'
                b'\x00\x00\x00\x00@$\x00\x00\x00\x00\x00\x00'
            ),
            b'\x00\x00\t'
        )

        self.assertEncodes(self.obj, bytes, encoding=miniamf.AMF0)

    def test_encode_amf3(self):
        bytes = (
            b'\n\x0b\x01', (
                b'\t_key\x01',
                b'\x0fnumbers\t\x0b\x01\x04\x02\x04\x04\x04\x06\x04\x08\x04\n'
                b'\x01'
            )
        )

        self.assertEncodes(self.obj, bytes, encoding=miniamf.AMF3)

    def test_encode_amf0_registered(self):
        miniamf.register_class(models.ListModel, 'list-model')

        bytes = (
            b'\x10\x00\nlist-model', (
                b'\x00\x04_key\x05',
                b'\x00\x07numbers\n\x00\x00\x00\x05\x00@'
                b'\x00\x00\x00\x00\x00\x00\x00\x00@\x10\x00\x00\x00\x00\x00'
                b'\x00\x00@\x18\x00\x00\x00\x00\x00\x00\x00@\x20\x00\x00\x00'
                b'\x00\x00\x00\x00@$\x00\x00\x00\x00\x00\x00'
            ),
            b'\x00\x00\t'
        )

        self.assertEncodes(self.obj, bytes, encoding=miniamf.AMF0)

    def test_encode_amf3_registered(self):
        miniamf.register_class(models.ListModel, 'list-model')

        bytes = (
            b'\n\x0b\x15list-model', (
                b'\t_key\x01',
                b'\x0fnumbers\t\x0b\x01\x04\x02\x04\x04\x04\x06\x04\x08\x04\n'
                b'\x01'
            )
        )

        self.assertEncodes(self.obj, bytes, encoding=miniamf.AMF3)

    def _check_list(self, x):
        self.assertTrue(isinstance(x, models.ListModel))
        self.assertTrue(hasattr(x, 'numbers'))
        self.assertEqual(x.numbers, [2, 4, 6, 8, 10])

    def test_decode_amf0(self):
        miniamf.register_class(models.ListModel, 'list-model')

        bytes = (
            b'\x10\x00\nlist-model\x00\x07numbers\n\x00\x00\x00\x05\x00@\x00'
            b'\x00\x00\x00\x00\x00\x00\x00@\x10\x00\x00\x00\x00\x00\x00\x00@'
            b'\x18\x00\x00\x00\x00\x00\x00\x00@ \x00\x00\x00\x00\x00\x00\x00@'
            b'$\x00\x00\x00\x00\x00\x00\x00\x00\t')

        x = self.decode(bytes, encoding=miniamf.AMF0)
        self._check_list(x)

    def test_decode_amf3(self):
        miniamf.register_class(models.ListModel, 'list-model')

        bytes = (
            b'\n\x0b\x15list-model\x0fnumbers\t\x0b\x01\x04\x02\x04\x04\x04'
            b'\x06\x04\x08\x04\n\x01')

        x = self.decode(bytes, encoding=miniamf.AMF3)
        self._check_list(x)

    def test_none(self):
        miniamf.register_class(models.ListModel, 'list-model')

        bytes = b'\x10\x00\nlist-model\x00\x07numbers\x05\x00\x00\t'

        x = self.decode(bytes, encoding=miniamf.AMF0)

        self.assertEqual(x.numbers, [])


class DecodingModelTestCase(BaseTestCase):
    """
    """

    def getModel(self):
        return models.PetModel

    def setUp(self):
        BaseTestCase.setUp(self)
        self.model_class = self.getModel()

        self.jessica = JessicaFactory.makeJessica(self.model_class)

        miniamf.register_class(self.model_class, 'Pet')

        self.jessica.put()
        self.key = str(self.jessica.key())

    def _check_model(self, x):
        self.assertTrue(isinstance(x, self.model_class))
        self.assertEqual(x.__class__, self.model_class)

        self.assertEqual(x.type, self.jessica.type)
        self.assertEqual(x.weight_in_pounds, self.jessica.weight_in_pounds)
        self.assertEqual(x.birthdate, self.jessica.birthdate)
        self.assertEqual(x.spayed_or_neutered, self.jessica.spayed_or_neutered)

        # now check db.Model internals
        self.assertEqual(x.key(), self.jessica.key())
        self.assertEqual(x.kind(), self.jessica.kind())
        self.assertEqual(x.parent(), self.jessica.parent())
        self.assertEqual(x.parent_key(), self.jessica.parent_key())
        self.assertTrue(x.is_saved())

    def test_amf0(self):
        bytes = (
            b'\x10\x00\x03Pet\x00\x04_key%s\x00\x04type\x02\x00\x03cat'
            b'\x00\x10weight_in_pounds\x00@\x14\x00\x00\x00\x00\x00\x00\x00'
            b'\x04name\x02\x00\x07Jessica\x00\tbirthdate\x0bB^\xc4\xae\xaa\x00'
            b'\x00\x00\x00\x00\x00\x12spayed_or_neutered\x01\x00\x00\x00\t' % (
                self.encodeKey(self.key, miniamf.AMF0),))

        x = self.decode(bytes, encoding=miniamf.AMF0)

        self._check_model(x)

    def test_amf3(self):
        bytes = (
            b'\n\x0b\x07Pet\tname\x06\x0fJessica\t_key%s\x13birthdate'
            b'\x08\x01B^\xc4\xae\xaa\x00\x00\x00!weight_in_pounds\x04\x05\x07'
            b'foo\x06\x07bar\ttype\x06\x07cat%%spayed_or_neutered\x02\x01' % (
                self.encodeKey(self.key, miniamf.AMF3),))

        x = self.decode(bytes, encoding=miniamf.AMF3)

        self._check_model(x)


class DecodingExpandoTestCase(DecodingModelTestCase):
    """
    """

    def getModel(self):
        return models.PetExpando


class ClassAliasTestCase(BaseTestCase):
    """
    """

    def setUp(self):
        BaseTestCase.setUp(self)

        self.alias = adapter.DataStoreClassAlias(
            models.PetModel, 'foo.bar'
        )

        self.jessica = models.PetModel(name='Jessica', type='cat')
        self.jessica_expando = models.PetExpando(
            name='Jessica', type='cat'
        )
        self.jessica_expando.foo = 'bar'

        self.decoder = miniamf.get_decoder(miniamf.AMF3)

    def test_get_alias(self):
        alias = miniamf.register_class(models.PetModel)

        self.assertTrue(isinstance(alias, adapter.DataStoreClassAlias))

    def test_alias(self):
        self.alias.compile()

        self.assertEqual(self.alias.decodable_properties, [
            'birthdate',
            'name',
            'spayed_or_neutered',
            'type',
            'weight_in_pounds'
        ])

        self.assertEqual(self.alias.encodable_properties, [
            'birthdate',
            'name',
            'spayed_or_neutered',
            'type',
            'weight_in_pounds'
        ])

        self.assertEqual(self.alias.static_attrs, [])
        self.assertEqual(self.alias.readonly_attrs, None)
        self.assertEqual(self.alias.exclude_attrs, None)
        self.assertEqual(self.alias.reference_properties, None)

    def test_get_attrs(self):
        attrs = self.alias.getEncodableAttributes(self.jessica)
        self.assertEqual(attrs, {
            '_key': None,
            'type': 'cat',
            'name': 'Jessica',
            'birthdate': None,
            'weight_in_pounds': None,
            'spayed_or_neutered': None
        })

    def test_get_attrs_expando(self):
        attrs = self.alias.getEncodableAttributes(self.jessica_expando)
        self.assertEqual(attrs, {
            '_key': None,
            'type': 'cat',
            'name': 'Jessica',
            'birthdate': None,
            'weight_in_pounds': None,
            'spayed_or_neutered': None,
            'foo': 'bar'
        })

    def test_get_attributes(self):
        attrs = self.alias.getEncodableAttributes(self.jessica)

        self.assertEqual(attrs, {
            '_key': None,
            'type': 'cat',
            'name': 'Jessica',
            'birthdate': None,
            'weight_in_pounds': None,
            'spayed_or_neutered': None
        })

    def test_get_attributes_saved(self):
        self.jessica.put()

        attrs = self.alias.getEncodableAttributes(self.jessica)

        self.assertEqual(attrs, {
            'name': 'Jessica',
            '_key': str(self.jessica.key()),
            'type': 'cat',
            'birthdate': None,
            'weight_in_pounds': None,
            'spayed_or_neutered': None
        })

    def test_get_attributes_expando(self):
        attrs = self.alias.getEncodableAttributes(self.jessica_expando)

        self.assertEqual(attrs, {
            'name': 'Jessica',
            '_key': None,
            'type': 'cat',
            'birthdate': None,
            'weight_in_pounds': None,
            'spayed_or_neutered': None,
            'foo': 'bar'
        })

    def test_get_attributes_saved_expando(self):
        self.jessica_expando.put()

        attrs = self.alias.getEncodableAttributes(self.jessica_expando)

        self.assertEqual(attrs, {
            'name': 'Jessica',
            '_key': str(self.jessica_expando.key()),
            'type': 'cat',
            'birthdate': None,
            'weight_in_pounds': None,
            'spayed_or_neutered': None,
            'foo': 'bar'
        })

    def test_arbitrary_properties(self):
        self.jessica.foo = 'bar'

        attrs = self.alias.getEncodableAttributes(self.jessica)

        self.assertEqual(attrs, {
            '_key': None,
            'type': 'cat',
            'name': 'Jessica',
            'birthdate': None,
            'weight_in_pounds': None,
            'spayed_or_neutered': None,
            'foo': 'bar'
        })

    def test_property_type(self):
        class PropertyTypeModel(db.Model):
            @property
            def readonly(self):
                return True

            def _get_prop(self):
                return False

            def _set_prop(self, v):
                self.prop = v

            read_write = property(_get_prop, _set_prop)

        alias = adapter.DataStoreClassAlias(PropertyTypeModel, 'foo.bar')

        obj = PropertyTypeModel()

        attrs = alias.getEncodableAttributes(obj)
        self.assertEqual(attrs, {
            '_key': None,
            'read_write': False,
            'readonly': True
        })

        self.assertFalse(hasattr(obj, 'prop'))

        alias.applyAttributes(obj, {
            '_key': None,
            'readonly': False,
            'read_write': 'foo'
        }, codec=self.decoder)

        self.assertEqual(obj.prop, 'foo')


class ReferencesTestCase(BaseTestCase):
    """
    """

    def setUp(self):
        BaseTestCase.setUp(self)

        self.jessica = models.PetModel(name='Jessica', type='cat')
        self.jessica.birthdate = datetime.date(1986, 10, 2)
        self.jessica.weight_in_pounds = 5
        self.jessica.spayed_or_neutered = False

        self.jessica.put()

        self.jessica2 = db.get(self.jessica.key())

        self.assertNotIdentical(self.jessica, self.jessica2)
        self.assertEqual(str(self.jessica.key()), str(self.jessica2.key()))

    def failOnGet(self, *args, **kwargs):
        self.fail('Get attempted %r, %r' % (args, kwargs))

    def test_amf0(self):
        encoder = miniamf.get_encoder(miniamf.AMF0)
        stream = encoder.stream

        encoder.writeElement(self.jessica)

        stream.truncate()

        encoder.writeElement(self.jessica2)
        self.assertEqual(stream.getvalue(), b'\x07\x00\x00')

    def test_amf3(self):
        encoder = miniamf.get_encoder(miniamf.AMF3)
        stream = encoder.stream

        encoder.writeElement(self.jessica)

        stream.truncate()

        encoder.writeElement(self.jessica2)
        self.assertEqual(stream.getvalue(), b'\n\x00')

    def test_nullreference(self):
        c = models.Novel(title='Pride and Prejudice', author=None)
        c.put()

        encoder = miniamf.get_encoder(encoding=miniamf.AMF3)
        alias = adapter.DataStoreClassAlias(models.Novel, None)

        attrs = alias.getEncodableAttributes(c, codec=encoder)

        self.assertEqual(attrs, {
            '_key': str(c.key()),
            'title': 'Pride and Prejudice',
            'author': None
        })


class XDBReferenceCollectionTestCase(BaseTestCase):
    """
    """

    def setUp(self):
        BaseTestCase.setUp(self)
        self.klass = adapter.XDBReferenceCollection

    def test_init(self):
        x = self.klass()

        self.assertEqual(x, {})

    def test_get(self):
        x = self.klass()

        # not a class type
        with self.assertRaises(TypeError):
            x.get(chr, '')

        # not a subclass of db.Model/db.Expando
        with self.assertRaises(TypeError):
            x.get(Spam, '')

        x = self.klass()

        with self.assertRaises(KeyError):
            x.get(models.PetModel, 'foo')

        self.assertEqual(x, {models.PetModel: {}})

        obj = object()

        x[models.PetModel]['foo'] = obj

        obj2 = x.get(models.PetModel, 'foo')

        self.assertEqual(id(obj), id(obj2))
        self.assertEqual(x, {models.PetModel: {'foo': obj}})

    def test_add(self):
        x = self.klass()

        # not a class type
        with self.assertRaises(TypeError):
            x.set(chr, '')

        # not a subclass of db.Model/db.Expando
        with self.assertRaises(TypeError):
            x.set(Spam, '')

        # wrong type for key
        with self.assertRaises(TypeError):
            x.set(models.PetModel, 3)

        x = self.klass()
        pm1 = models.PetModel(type='cat', name='Jessica')
        pm2 = models.PetModel(type='dog', name='Sam')
        pe1 = models.PetExpando(type='cat', name='Toby')

        self.assertEqual(x, {})

        x.set(models.PetModel, 'foo', pm1)
        self.assertEqual(x, {models.PetModel: {'foo': pm1}})
        x.set(models.PetModel, 'bar', pm2)
        self.assertEqual(x, {models.PetModel: {'foo': pm1, 'bar': pm2}})
        x.set(models.PetExpando, 'baz', pe1)
        self.assertEqual(x, {
            models.PetModel: {'foo': pm1, 'bar': pm2},
            models.PetExpando: {'baz': pe1}
        })


class HelperTestCase(BaseTestCase):
    """
    """

    def test_encode_key(self):
        key = db.Key.from_path('PetModel', 'jessica')

        self.assertIsNone(db.get(key))
        self.assertEncodes(key, (
            b'\x05',
        ), encoding=miniamf.AMF0
        )

    def test_getGAEObjects(self):
        context = {}

        x = adapter.getGAEObjects(context)
        self.assertTrue(isinstance(x, adapter.XDBReferenceCollection))
        self.assertTrue('gae_xdb_context' in context)
        self.assertEqual(id(x), id(context['gae_xdb_context']))

    def test_Query_type(self):
        """
        L{db.Query} instances get converted to lists ..
        """
        q = models.EmptyModel.all()

        self.assertTrue(isinstance(q, db.Query))
        self.assertEncodes(q, (b'\n\x00\x00\x00\x00',), encoding=miniamf.AMF0)
        self.assertEncodes(q, (b'\t\x01\x01',), encoding=miniamf.AMF3)


class FloatPropertyTestCase(BaseTestCase):
    """
    Tests for #609.
    """

    def setUp(self):
        BaseTestCase.setUp(self)

        class FloatModel(db.Model):
            f = db.FloatProperty()

        self.klass = FloatModel
        self.f = FloatModel()
        self.alias = adapter.DataStoreClassAlias(self.klass, None)
        self.decoder = miniamf.get_decoder(miniamf.AMF3)

    def test_behaviour(self):
        """
        Test the behaviour of the Google SDK not handling ints gracefully
        """
        with self.assertRaises(db.BadValueError):
            setattr(self.f, 'f', 3)

        self.f.f = 3.0

        self.assertEqual(self.f.f, 3.0)

    def test_apply_attributes(self):
        self.alias.applyAttributes(self.f, {'f': 3}, codec=self.decoder)

        self.assertEqual(self.f.f, 3.0)


class PolyModelTestCase(BaseTestCase):
    """
    Tests for L{db.PolyModel}. See #633
    """

    def setUp(self):
        BaseTestCase.setUp(self)

        class Poly(polymodel.PolyModel):
            s = db.StringProperty()

        self.klass = Poly
        self.p = Poly()
        self.alias = adapter.DataStoreClassAlias(self.klass, None)

    def test_encode(self):
        self.p.s = 'foo'

        attrs = self.alias.getEncodableAttributes(self.p)

        self.assertEqual(attrs, {'_key': None, 's': 'foo'})

    def test_deep_inheritance(self):
        class DeepPoly(self.klass):
            d = db.IntegerProperty()

        self.alias = adapter.DataStoreClassAlias(DeepPoly, None)
        self.dp = DeepPoly()
        self.dp.s = 'bar'
        self.dp.d = 92

        attrs = self.alias.getEncodableAttributes(self.dp)

        self.assertEqual(attrs, {
            '_key': None,
            's': 'bar',
            'd': 92
        })
