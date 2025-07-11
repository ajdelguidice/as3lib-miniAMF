# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Class alias base functionality.

@since: 0.6
"""

import inspect

import miniamf
from . import util


class UnknownClassAlias(Exception):
    """
    Raised if the AMF stream specifies an Actionscript class that does not
    have a Python class alias.

    @see: L{register_class}
    """


class ClassAlias(object):
    """
    Class alias. Provides class/instance meta data to the En/Decoder to allow
    fine grain control and some performance increases.
    """

    def __init__(self, klass, alias=None, **kwargs):
        if not isinstance(klass, type):
            raise TypeError("klass must be a class type, got %r" % klass)

        # In Python 2, both byte and Unicode string types have .decode
        # methods.  In Python 3, only byte strings do.
        if alias is None or isinstance(alias, str):
            pass
        elif hasattr(alias, "decode"):
            alias = alias.decode("utf-8")

        self.checkClass(klass)

        self.klass = klass
        self.alias = alias

        self.static_attrs = kwargs.pop('static_attrs', None)
        self.exclude_attrs = kwargs.pop('exclude_attrs', None)
        self.readonly_attrs = kwargs.pop('readonly_attrs', None)
        self.amf3 = kwargs.pop('amf3', None)
        self.external = kwargs.pop('external', None)
        self.dynamic = kwargs.pop('dynamic', None)
        self.synonym_attrs = kwargs.pop('synonym_attrs', {})

        self._compiled = False
        self.anonymous = False
        self.sealed = None
        self.bases = None

        if self.alias is None:
            self.anonymous = True
            # we don't set this to None because AMF3 untyped objects have a
            # class name of ''
            self.alias = ''
        else:
            if self.alias == '':
                raise ValueError('Cannot set class alias as \'\'')

        if not kwargs.pop('defer', False):
            self.compile()

        if kwargs:
            raise TypeError('Unexpected keyword arguments %r' % (kwargs,))

    def _checkExternal(self):
        k = self.klass

        if not hasattr(k, '__readamf__'):
            raise AttributeError(
                "An externalised class was specified, but"
                " no __readamf__ attribute was found for %r" % (k,)
            )

        if not hasattr(k, '__writeamf__'):
            raise AttributeError(
                "An externalised class was specified, but"
                " no __writeamf__ attribute was found for %r" % (k,)
            )

        if not hasattr(k.__readamf__, '__call__'):
            raise TypeError("%s.__readamf__ must be callable" % (k.__name__,))

        if not hasattr(k.__writeamf__, '__call__'):
            raise TypeError("%s.__writeamf__ must be callable" % (k.__name__,))

    def compile(self):
        """
        This compiles the alias into a form that can be of most benefit to the
        en/decoder.
        """
        if self._compiled:
            return

        self.decodable_properties = set()
        self.encodable_properties = set()
        self.inherited_dynamic = None
        self.inherited_sealed = None
        self.bases = []

        self.exclude_attrs = set(self.exclude_attrs or [])
        self.readonly_attrs = set(self.readonly_attrs or [])
        self.static_attrs = list(self.static_attrs or [])
        self.static_attrs_set = set(self.static_attrs)

        self.sealed = util.is_class_sealed(self.klass)

        if self.external:
            self._checkExternal()
            self._finalise_compile()

            # this class is external so no more compiling is necessary
            return

        if hasattr(self.klass, '__slots__'):
            self.decodable_properties.update(self.klass.__slots__)
            self.encodable_properties.update(self.klass.__slots__)

        for k, v in self.klass.__dict__.items():
            if not isinstance(v, property):
                continue

            if v.fget:
                self.encodable_properties.update([k])

            if v.fset:
                self.decodable_properties.update([k])
            else:
                self.readonly_attrs.update([k])

        mro = inspect.getmro(self.klass)[1:]

        for c in mro:
            self._compile_base_class(c)

        self.getCustomProperties()

        self._finalise_compile()

    def _compile_base_class(self, klass):
        if klass is object:
            return

        try:
            alias = miniamf.get_class_alias(klass)
        except UnknownClassAlias:
            alias = miniamf.register_class(klass)

        alias.compile()

        self.bases.append((klass, alias))

        if alias.exclude_attrs:
            self.exclude_attrs.update(alias.exclude_attrs)

        if alias.readonly_attrs:
            self.readonly_attrs.update(alias.readonly_attrs)

        if alias.static_attrs:
            self.static_attrs_set.update(alias.static_attrs)

            for a in alias.static_attrs:
                if a not in self.static_attrs:
                    self.static_attrs.insert(0, a)

        if alias.encodable_properties:
            self.encodable_properties.update(alias.encodable_properties)

        if alias.decodable_properties:
            self.decodable_properties.update(alias.decodable_properties)

        if self.amf3 is None and alias.amf3:
            self.amf3 = alias.amf3

        if self.dynamic is None and alias.dynamic is not None:
            self.inherited_dynamic = alias.dynamic

        if alias.sealed is not None:
            self.inherited_sealed = alias.sealed

        if alias.synonym_attrs:
            x = self.synonym_attrs
            self.synonym_attrs = alias.synonym_attrs.copy()
            self.synonym_attrs.update(x)

    def _finalise_compile(self):
        if self.dynamic is None:
            self.dynamic = True

            if self.inherited_dynamic is not None:
                if not self.inherited_dynamic \
                        and not self.sealed \
                        and self.inherited_sealed:
                    self.dynamic = True
                else:
                    self.dynamic = self.inherited_dynamic

        if self.sealed:
            self.dynamic = False

        if self.amf3 is None:
            self.amf3 = False

        if self.external is None:
            self.external = False

        if self.static_attrs:
            self.static_attrs = list(self.static_attrs)
            self.static_attrs.sort()

            self.encodable_properties.update(self.static_attrs)
            self.decodable_properties.update(self.static_attrs)

        if self.static_attrs:
            self.static_attrs_set.update(self.static_attrs)

            if self.exclude_attrs:
                self.static_attrs_set.difference_update(self.exclude_attrs)

            for a in self.static_attrs_set:
                if a not in self.static_attrs:
                    self.static_attrs.remove(a)

        if not self.exclude_attrs:
            self.exclude_attrs = None
        else:
            self.encodable_properties.difference_update(self.exclude_attrs)
            self.decodable_properties.difference_update(self.exclude_attrs)

        if self.exclude_attrs is not None:
            self.exclude_attrs = list(self.exclude_attrs)
            self.exclude_attrs.sort()

        if not self.readonly_attrs:
            self.readonly_attrs = None
        else:
            self.decodable_properties.difference_update(self.readonly_attrs)

        if self.readonly_attrs is not None:
            self.readonly_attrs = list(self.readonly_attrs)
            self.readonly_attrs.sort()

        if len(self.decodable_properties) == 0:
            self.decodable_properties = None
        else:
            self.decodable_properties = list(self.decodable_properties)
            self.decodable_properties.sort()

        if len(self.encodable_properties) == 0:
            self.encodable_properties = None
        else:
            self.encodable_properties = list(self.encodable_properties)
            self.encodable_properties.sort()

        self.non_static_encodable_properties = None

        if self.encodable_properties:
            self.non_static_encodable_properties = set(
                self.encodable_properties
            )

            if self.static_attrs:
                self.non_static_encodable_properties.difference_update(
                    self.static_attrs
                )

        self.shortcut_encode = True
        self.shortcut_decode = True

        if (self.encodable_properties or self.static_attrs or
                self.exclude_attrs or self.external or
                self.synonym_attrs):
            self.shortcut_encode = False

        if (self.decodable_properties or self.static_attrs or
                self.exclude_attrs or self.readonly_attrs or
                not self.dynamic or self.external or self.synonym_attrs):
            self.shortcut_decode = False

        self.is_dict = False

        if issubclass(self.klass, dict) or self.klass is dict:
            self.is_dict = True

        self._compiled = True

    def is_compiled(self):
        return self._compiled

    def __str__(self):
        return self.alias

    def __bytes__(self):
        return self.alias.encode('utf-8')

    def __repr__(self):
        k = self.__class__

        return '<%s.%s alias=%r class=%r @ 0x%x>' % (
            k.__module__,
            k.__name__,
            self.alias,
            self.klass,
            id(self)
        )

    def __eq__(self, other):
        if isinstance(other, str):
            return self.alias == other
        elif isinstance(other, self.__class__):
            return self.klass == other.klass
        elif isinstance(other, type):
            return self.klass == other
        else:
            return False

    def __hash__(self):
        return id(self)

    def checkClass(self, klass):
        """
        This function is used to check if the class being aliased fits certain
        criteria. The default is to check that C{__new__} is available or the
        C{__init__} constructor does not need additional arguments. If this is
        the case then L{TypeError} will be raised.

        @since: 0.4
        """
        # Check for __new__ support.
        if hasattr(klass, '__new__') and hasattr(klass.__new__, '__call__'):
            # Should be good to go.
            return

        # Check that the constructor of the class doesn't require any additonal
        # arguments.
        if not (
            hasattr(klass, '__init__') and hasattr(klass.__init__, '__call__')
        ):
            return

        klass_func = klass.__init__.__func__

        if not hasattr(klass_func, 'func_code'):
            # Can't examine it, assume it's OK.
            return

        if klass_func.__defaults__:
            available_arguments = len(klass_func.__defaults__) + 1
        else:
            available_arguments = 1

        needed_arguments = klass_func.__code__.co_argcount

        if available_arguments >= needed_arguments:
            # Looks good to me.
            return

        spec = inspect.getargspec(klass_func)

        raise TypeError(
            "__init__ doesn't support additional arguments: %s" % (
                inspect.formatargspec(*spec)
            )
        )

    def getAttribute(self, obj, attr, codec=None):
        """
        Get the attribute `attr` from `obj`. If no attribute exists,
        `miniamf.Undefined` is returned.

        @param codec: The current `miniamf.codec.Codec` getting the attribute
            (if there is one).
        """
        return getattr(obj, attr)

    def getEncodableAttributes(self, obj, codec=None):
        """
        Must return a C{dict} of attributes to be encoded, even if its empty.

        @param codec: An optional argument that will contain the encoder
            instance calling this function.
        @since: 0.5
        """
        if not self._compiled:
            self.compile()

        if self.is_dict:
            return dict(obj)

        if self.shortcut_encode and self.dynamic:
            return obj.__dict__.copy()

        attrs = {}

        if self.static_attrs:
            for attr in self.static_attrs:
                try:
                    attrs[attr] = self.getAttribute(obj, attr, codec=codec)
                except AttributeError:
                    attrs[attr] = miniamf.Undefined

        if not self.dynamic:
            if self.non_static_encodable_properties:
                for attr in self.non_static_encodable_properties:
                    attrs[attr] = self.getAttribute(obj, attr, codec=codec)

            return attrs

        dynamic_props = util.get_properties(obj)

        if not self.shortcut_encode:
            dynamic_props = set(dynamic_props)

            if self.encodable_properties:
                dynamic_props.update(self.encodable_properties)

            if self.static_attrs:
                dynamic_props.difference_update(self.static_attrs)

            if self.exclude_attrs:
                dynamic_props.difference_update(self.exclude_attrs)

        for attr in dynamic_props:
            attrs[attr] = self.getAttribute(obj, attr, codec=codec)

        if self.synonym_attrs:
            missing = object()

            for k, v in self.synonym_attrs.items():
                value = attrs.pop(k, missing)

                if value is missing:
                    continue

                attrs[v] = value

        return attrs

    def getDecodableAttributes(self, obj, attrs, codec=None):
        """
        Returns a dictionary of attributes for C{obj} that has been filtered,
        based on the supplied C{attrs}. This allows for fine grain control
        over what will finally end up on the object or not.

        @param obj: The object that will recieve the attributes.
        @param attrs: The C{attrs} dictionary that has been decoded.
        @param codec: An optional argument that will contain the decoder
            instance calling this function.
        @return: A dictionary of attributes that can be applied to C{obj}
        @since: 0.5
        """
        if not self._compiled:
            self.compile()

        changed = False

        props = set(attrs.keys())

        if self.static_attrs:
            missing_attrs = self.static_attrs_set.difference(props)

            if missing_attrs:
                raise AttributeError(
                    'Static attributes %r expected when decoding %r' % (
                        missing_attrs, self.klass
                    )
                )

            props.difference_update(self.static_attrs)

        if not props:
            return attrs

        if not self.dynamic:
            if not self.decodable_properties:
                props = set()
            else:
                props.intersection_update(self.decodable_properties)

            changed = True

        if self.readonly_attrs:
            props.difference_update(self.readonly_attrs)
            changed = True

        if self.exclude_attrs:
            props.difference_update(self.exclude_attrs)
            changed = True

        if changed:
            # apply all filters before synonyms
            a = {}

            [a.__setitem__(p, attrs[p]) for p in props]
            attrs = a

        if self.synonym_attrs:
            missing = object()

            for k, v in self.synonym_attrs.items():
                value = attrs.pop(v, missing)

                if value is missing:
                    continue

                attrs[k] = value

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

        util.set_attrs(obj, attrs)

    def getCustomProperties(self):
        """
        Overrride this to provide known static properties based on the aliased
        class.

        @since: 0.5
        """

    def createInstance(self, codec=None):
        """
        Creates an instance of the klass.

        @return: Instance of C{self.klass}.
        """
        if type(self.klass) is type:
            return self.klass.__new__(self.klass)

        return self.klass()
