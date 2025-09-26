# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
C{django.db.models} adapter module.

@see: U{Django Project<http://www.djangoproject.com>}
@since: 0.4.1
"""

import datetime
import miniamf

from itertools import chain

from django.db import models
from django.db.models.base import Model
from django.db.models import fields
from django.db.models.fields import files, related


# Model._meta.get_all_field_names was removed in django 1.10.
def _get_all_field_names(meta):
    return list(set(chain.from_iterable(
        (f.name, f.attname) if hasattr(f, 'attname') else (f.name,)
        for f in meta.get_fields()
        if not (f.many_to_one and f.related_model is None)
    )))


class DjangoReferenceCollection(dict):
    """
    This helper class holds a dict of klass to pk/objects loaded from the
    underlying db.

    @since: 0.5
    """

    def _getClass(self, klass):
        if klass not in self.keys():
            self[klass] = {}

        return self[klass]

    def getClassKey(self, klass, key):
        """
        Return an instance based on klass/key.

        If an instance cannot be found then C{KeyError} is raised.

        @param klass: The class of the instance.
        @param key: The primary_key of the instance.
        @return: The instance linked to the C{klass}/C{key}.
        @rtype: Instance of C{klass}.
        """
        d = self._getClass(klass)

        return d[key]

    def addClassKey(self, klass, key, obj):
        """
        Adds an object to the collection, based on klass and key.

        @param klass: The class of the object.
        @param key: The datastore key of the object.
        @param obj: The loaded instance from the datastore.
        """
        d = self._getClass(klass)

        d[key] = obj


class DjangoClassAlias(miniamf.ClassAlias):

    def getCustomProperties(self):
        self.fields = {}
        self.relations = {}
        self.columns = []

        self.meta = self.klass._meta

        for name in _get_all_field_names(self.meta):
            x = self.meta.get_field(name)
            if x.auto_created or isinstance(x, related.ForeignObjectRel):
                continue

            if isinstance(x, files.FileField):
                self.readonly_attrs.update([name])
            if isinstance(x, (models.ManyToManyField, models.ForeignKey)):
                self.relations[name] = x
            else:
                self.fields[name] = x

        parent_fields = []

        for field in self.meta.parents.values():
            parent_fields.append(field.attname)
            try:
                del self.relations[field.name]
            except KeyError:
                continue

        self.exclude_attrs.update(parent_fields)

        props = self.fields.keys()

        self.encodable_properties.update(props)
        self.decodable_properties.update(props)

        self.exclude_attrs.update(['_state'])

    def _compile_base_class(self, klass):
        if klass is Model:
            return

        miniamf.ClassAlias._compile_base_class(self, klass)

    def _encodeValue(self, field, value):
        if value is fields.NOT_PROVIDED:
            return miniamf.Undefined

        if value is None:
            return value

        # deal with dates ..
        if isinstance(field, fields.DateTimeField):
            return value
        elif isinstance(field, fields.DateField):
            return datetime.datetime(
                value.year,
                value.month,
                value.day,
                0,  # hour
                0,  # minute
                0,  # second
            )
        elif isinstance(field, fields.TimeField):
            return datetime.datetime(
                1970,  # year
                1,  # month
                1,  # day
                value.hour,
                value.minute,
                value.second,
                value.microsecond
            )
        elif isinstance(value, files.FieldFile):
            return value.name

        return value

    def _decodeValue(self, field, value):
        if value is miniamf.Undefined:
            return fields.NOT_PROVIDED

        if isinstance(field, fields.AutoField) and value == 0:
            return None
        elif isinstance(field, fields.DateTimeField):
            # deal with dates
            return value
        elif isinstance(field, fields.DateField):
            if not value:
                return None

            return datetime.date(value.year, value.month, value.day)
        elif isinstance(field, fields.TimeField):
            if not value:
                return None

            return datetime.time(
                value.hour,
                value.minute,
                value.second,
                value.microsecond,
            )

        return value

    def getEncodableAttributes(self, obj, **kwargs):
        attrs = miniamf.ClassAlias.getEncodableAttributes(self, obj, **kwargs)

        if not attrs:
            attrs = {}

        for name, prop in self.fields.items():
            if name in attrs.keys():
                attrs[name] = self._encodeValue(prop, getattr(obj, name))

        for key in attrs.keys():
            if key.startswith('_'):
                del attrs[key]

        for name, relation in self.relations.items():
            if name in obj._state.fields_cache:
                attrs[name] = getattr(obj, name)

            if isinstance(relation, models.ManyToManyField):
                attrs[name] = [x for x in getattr(obj, name).all()]
            else:
                attrs.pop(relation.attname, None)

        return attrs

    def getDecodableAttributes(self, obj, attrs, **kwargs):
        attrs = miniamf.ClassAlias.getDecodableAttributes(
            self,
            obj,
            attrs,
            **kwargs
        )

        if self.decodable_properties:
            for n in self.decodable_properties:
                if n in self.relations:
                    continue

                try:
                    f = self.fields[n]
                except KeyError:
                    continue

                attrs[f.attname] = self._decodeValue(f, attrs[n])

        # primary key of django object must always be set first for
        # relationships with other model objects to work properly
        # and dict.iteritems() does not guarantee order
        #
        # django also forces the use only one attribute as primary key, so
        # our obj._meta.pk.attname check is sufficient)
        pk_attr = obj._meta.pk.attname
        pk = attrs.pop(pk_attr, None)

        if pk:
            if pk is fields.NOT_PROVIDED:
                attrs[pk_attr] = pk
            else:
                # load the object from the database
                try:
                    loaded_instance = self.klass.objects.filter(pk=pk)[0]
                    obj.__dict__ = loaded_instance.__dict__
                except IndexError:
                    pass

        if not getattr(obj, pk_attr):
            for name, relation in self.relations.items():
                if isinstance(relation, related.ManyToManyField):
                    try:
                        if len(attrs[name]) == 0:
                            del attrs[name]
                    except KeyError:
                        pass

        return attrs

    def applyAttributes(self, obj, attrs, codec=None):
        """
        Applies the collection of attributes C{attrs} to aliased object C{obj}.
        Called when decoding reading aliased objects from an AMF byte stream.

        Override this to provide fine grain control of application of
        attributes to C{obj}.

        @param codec: An optional argument that will contain the en/decoder
            instance calling this function.
        """
        if not self._compiled:
            self.compile()

        if not self.shortcut_decode:
            attrs = self.getDecodableAttributes(obj, attrs, codec=codec)
        else:
            if self.is_dict:
                obj.update(attrs)

                return

            if not self.sealed:
                obj.__dict__.update(attrs)

                return

        o = setattr

        if hasattr(obj, '__setitem__'):
            o = type(obj).__setitem__

        for k, v in attrs.items():
            try:
                o(obj, k, v)
            except TypeError:
                getattr(obj, k).set(v)


def getDjangoObjects(context):
    """
    Returns a reference to the C{django_objects} on the context. If it doesn't
    exist then it is created.

    @rtype: Instance of L{DjangoReferenceCollection}
    @since: 0.5
    """
    c = context.extra
    k = 'django_objects'

    try:
        return c[k]
    except KeyError:
        c[k] = DjangoReferenceCollection()

    return c[k]


def writeDjangoObject(obj, encoder=None):
    """
    The Django ORM creates new instances of objects for each db request.
    This is a problem for MiniAMF as it uses the C{id(obj)} of the object to do
    reference checking.

    We could just ignore the problem, but the objects are conceptually the
    same so the effort should be made to attempt to resolve references for a
    given object graph.

    We create a new map on the encoder context object which contains a dict of
    C{object.__class__: {key1: object1, key2: object2, .., keyn: objectn}}. We
    use the primary key to do the reference checking.

    @since: 0.5
    """
    s = obj.pk

    if s is None:
        encoder.writeObject(obj)

        return

    django_objects = getDjangoObjects(encoder.context)
    kls = obj.__class__

    try:
        referenced_object = django_objects.getClassKey(kls, s)
    except KeyError:
        referenced_object = obj
        django_objects.addClassKey(kls, s, obj)

    encoder.writeObject(referenced_object)


# initialise the module here: hook into miniamf
miniamf.register_alias_type(DjangoClassAlias, Model)
miniamf.add_type(Model, writeDjangoObject)
