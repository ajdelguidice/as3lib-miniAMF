# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
U{Mini-AMF<http://miniamf.org>} provides Action Message Format (U{AMF
<http://en.wikipedia.org/wiki/Action_Message_Format>}) support for Python that
is compatible with the Adobe U{Flash Player
<http://en.wikipedia.org/wiki/Flash_Player>}.

@since: October 2007
@status: Production/Stable
"""

import inspect
from importlib import import_module

from . import util, _version
from .adapters import register_adapters, get_adapter
from .alias import ClassAlias, UnknownClassAlias


__all__ = [
    'register_class',
    'register_class_loader',
    'get_adapter',
    'encode',
    'decode',
    '__version__',
    'version'
]

#: Mini-AMF version number.
__version__ = version = _version.version

#: Class alias mapping support. Contains two types of keys: The string alias
#: related to the class and the class object itself. Both point to the linked
#: L{ClassAlias} object.
#: @see: L{register_class}, L{unregister_class}, and L{register_package}
CLASS_CACHE = {}

#: Class loaders. An iterable of callables that are handed a string alias and
#: return a class object or C{None} it not handled.
#: @see: L{register_class_loader} and L{unregister_class_loader}
CLASS_LOADERS = []

#: Custom type map.
#: @see: L{get_type}, L{add_type}, and L{remove_type}
TYPE_MAP = {}

#: Maps error classes to string codes.
#: @see: L{add_error_class} and L{remove_error_class}
ERROR_CLASS_MAP = {
    TypeError.__name__: TypeError,
    KeyError.__name__: KeyError,
    LookupError.__name__: LookupError,
    IndexError.__name__: IndexError,
    NameError.__name__: NameError,
    ValueError.__name__: ValueError
}
#: Alias mapping support.
#: @see: L{get_class_alias}, L{register_alias_type}, and
#: L{unregister_alias_type}
ALIAS_TYPES = {}

#: A list of callbacks to execute once a decode has been successful.
POST_DECODE_PROCESSORS = []

#: Specifies that objects are serialized using AMF for ActionScript 1.0
#: and 2.0 that were introduced in the Adobe Flash Player 6.
AMF0 = 0

#: Specifies that objects are serialized using AMF for ActionScript 3.0
#: that was introduced in the Adobe Flash Player 9.
AMF3 = 3

#: Supported AMF encoding types.
#: @see: L{AMF0}, L{AMF3}, and L{DEFAULT_ENCODING}
ENCODING_TYPES = (AMF0, AMF3)

#: Default encoding
DEFAULT_ENCODING = AMF3


class UndefinedType(object):
    """
    Represents the C{undefined} value in the Adobe Flash Player client.
    """

    def __repr__(self):
        return 'miniamf.Undefined'

    def __bool__(self):
        return False


#: Represents the C{undefined} value in the Adobe Flash Player client.
Undefined = UndefinedType()


class BaseError(Exception):
    """
    Base AMF Error.

    All AMF related errors should be subclassed from this class.
    """


class DecodeError(BaseError):
    """
    Raised if there is an error in decoding an AMF data stream.
    """


class EOStream(BaseError):
    """
    Raised if the data stream has come to a natural end.
    """


class ReferenceError(BaseError):
    """
    Raised if an AMF data stream refers to a non-existent object or string
    reference (in the case of AMF3).
    """


class EncodeError(BaseError):
    """
    Raised if the element could not be encoded to AMF.
    """


class ASObject(dict):
    """
    Represents a Flash Actionscript Object (typed or untyped).

    I supply a C{dict} interface to support C{getattr}/C{setattr} calls.
    """

    class __amf__:
        dynamic = True

    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError:
            raise AttributeError('Unknown attribute \'%s\'' % (k,))

    def __setattr__(self, k, v):
        self[k] = v

    def __repr__(self):
        return dict.__repr__(self)

    def __hash__(self):
        return id(self)


class MixedArray(dict):
    """
    Used to be able to specify the C{mixedarray} type.
    """


class TypedObject(dict):
    """
    This class is used when a strongly typed object is decoded but there is no
    registered class to apply it to.

    This object can only be used for standard streams - i.e. not externalized
    data. If encountered, and C{strict} mode is C{False}, a L{DecodeError}
    or L{EncodeError} will be raised.

    @ivar alias: The alias of the typed object.
    @type alias: C{string}
    @since: 0.4
    @raise DecodeError: Unable to decode an externalised stream.
    @raise EncodeError: Unable to encode an externalised stream.
    """

    def __init__(self, alias):
        dict.__init__(self)

        self.alias = alias

    def __readamf__(self, o):
        raise DecodeError(
            'Unable to decode an externalised stream with class alias \'%s\'.'
            '\n\nA class alias was found and because strict mode is False an '
            'attempt was made to decode the object automatically. To decode '
            'this stream, a registered class with the alias and a '
            'corresponding __readamf__ method will be required.' % (
                self.alias,
            )
        )

    def __writeamf__(self, o):
        raise EncodeError(
            'Unable to encode an externalised stream with class alias \'%s\'.'
            '\n\nA class alias was found and because strict mode is False an '
            'attempt was made to encode the object automatically. To encode '
            'this stream, a registered class with the alias and a '
            'corresponding __writeamf__ method will be required.' % (
                self.alias,
            )
        )


class TypedObjectClassAlias(ClassAlias):
    """
    The meta class for L{TypedObject} used to adapt Mini-AMF.

    @since: 0.4
    """

    klass = TypedObject

    def __init__(self, *args, **kwargs):
        ClassAlias.__init__(self, self.klass, kwargs.pop('alias', args[0]))

    def createInstance(self, codec=None):
        return self.klass(self.alias)

    def checkClass(kls, klass):
        pass


class ErrorAlias(ClassAlias):
    """
    Adapts Python exception objects to Adobe Flash Player error objects.

    @since: 0.5
    """

    def getCustomProperties(self):
        self.exclude_attrs.update(['args'])

    def getEncodableAttributes(self, obj, **kwargs):
        attrs = ClassAlias.getEncodableAttributes(self, obj, **kwargs)

        attrs['message'] = str(obj)
        attrs['name'] = obj.__class__.__name__

        return attrs


def register_class(klass, alias=None):
    """
    Registers a class to be used in the data streaming. This is the equivalent
    of the C{[RemoteClass(alias="foobar")]} metatag in Adobe Flex, and the
    C{flash.net.registerClassAlias} method in Actionscript 3.0.

    @return: The registered L{ClassAlias} instance.
    @see: L{unregister_class}
    @see: U{flash.net.registerClassAlias on Adobe Help (external)
            <http://help.adobe.com/en_US/FlashPlatform/reference/actionscript/3/flash/net/package.html#registerClassAlias%28%29>}
    """
    meta = util.get_class_meta(klass)

    if alias is not None:
        meta['alias'] = alias

    alias_klass = util.get_class_alias(klass) or ClassAlias

    x = alias_klass(klass, defer=True, **meta)

    if not x.anonymous:
        CLASS_CACHE[x.alias] = x

    CLASS_CACHE[klass] = x

    return x


def unregister_class(alias):
    """
    Opposite of L{register_class}.

    @raise UnknownClassAlias: Unknown alias.
    """
    try:
        x = CLASS_CACHE[alias]
    except KeyError:
        raise UnknownClassAlias('Unknown alias %r' % (alias,))

    if not x.anonymous:
        del CLASS_CACHE[x.alias]

    del CLASS_CACHE[x.klass]

    return x


def get_class_alias(klass_or_alias):
    """
    Finds the L{ClassAlias} that is registered to C{klass_or_alias}.

    If a string is supplied and no related L{ClassAlias} is found, the alias is
    loaded via L{load_class}.

    @raise UnknownClassAlias: Unknown alias
    """
    try:
        return CLASS_CACHE[klass_or_alias]
    except KeyError:
        if isinstance(klass_or_alias, str):
            return load_class(klass_or_alias)
        raise UnknownClassAlias('Unknown alias for %r' % (klass_or_alias,))


def register_class_loader(loader):
    """
    Registers a loader that is called to provide the C{class} for a specific
    alias.

    The C{loader} is provided with one argument, the class alias (as a string).
    If the loader succeeds in finding a suitable class then it should return
    that class, otherwise it should return C{None}.

    An example::

        def lazy_load_from_my_module(alias):
            if not alias.startswith('foo.bar.'):
                return None

            from foo import bar

            if alias == 'foo.bar.Spam':
                return bar.Spam
            elif alias == 'foo.bar.Eggs':
                return bar.Eggs

        miniamf.register_class_loader(lazy_load_from_my_module)

    @raise TypeError: C{loader} must be callable
    @see: L{unregister_class_loader}
    """
    if not callable(loader):
        raise TypeError("loader must be callable")

    if loader not in CLASS_LOADERS:
        CLASS_LOADERS.insert(0, loader)


def unregister_class_loader(loader):
    """
    Unregisters a class loader.

    @param loader: The class loader to be unregistered.
    @raise LookupError: The C{loader} was not registered.
    @see: L{register_class_loader}
    """
    try:
        CLASS_LOADERS.remove(loader)
    except ValueError:
        raise LookupError("loader not registered")


def _load_class_from_module(alias):
    """
    Load a class by guessing the name of a module that might define it.
    This is always the final entry in CLASS_LOADERS.
    """
    mod_class = alias.split('.')

    if not mod_class:
        return None

    module = '.'.join(mod_class[:-1])
    klass = mod_class[-1]

    try:
        module = util.get_module(module)
    except (ImportError, AttributeError):
        return None

    return getattr(module, klass)


def load_class(alias):
    """
    Finds the class registered to the alias.

    The search is done in order:
      1. Checks if the class name has been registered via L{register_class}
         or L{register_package}.
      2. Checks all functions registered via L{register_class_loader}.
      3. Attempts to load the class via standard module loading techniques.

    @param alias: The class name.
    @type alias: C{string}
    @raise UnknownClassAlias: The C{alias} was not found.
    @raise TypeError: Expecting class type or L{ClassAlias} from loader.
    @return: Class registered to the alias.
    @rtype: C{classobj}
    """
    # Try the CLASS_CACHE first
    try:
        return CLASS_CACHE[alias]
    except KeyError:
        pass

    for loader in CLASS_LOADERS:
        klass = loader(alias)

        if klass is None:
            continue

        if isinstance(klass, type):
            return register_class(klass, alias)

        if isinstance(klass, ClassAlias):
            CLASS_CACHE[klass.alias] = klass
            CLASS_CACHE[klass.klass] = klass
            return klass.klass

        raise TypeError("Expecting class object, not %r, from loader"
                        % klass)

    # All available methods for finding the class have been exhausted
    raise UnknownClassAlias("Unknown alias for %r" % (alias,))


def decode(stream, *args, **kwargs):
    """
    A generator function to decode a datastream.

    @param stream: AMF data to be decoded.
    @type stream: byte data
    @kwarg encoding: AMF encoding type. One of L{ENCODING_TYPES}.
    @type encoding: C{int}
    @return: A generator that will decode each element in the stream.
    """
    encoding = kwargs.pop('encoding', DEFAULT_ENCODING)
    decoder = get_decoder(encoding, stream, *args, **kwargs)

    return decoder


def encode(*args, **kwargs):
    """
    A helper function to encode an element.

    @param args: The Python data to be encoded.
    @kwarg encoding: AMF encoding type. One of L{ENCODING_TYPES}.
    @type encoding: C{int}
    @return: A L{util.BufferedByteStream} object that contains the data.
    """
    encoding = kwargs.pop('encoding', DEFAULT_ENCODING)
    encoder = get_encoder(encoding, **kwargs)

    [encoder.writeElement(el) for el in args]

    stream = encoder.stream
    stream.seek(0)

    return stream


def _get_amf_module(version, use_ext):
    """
    Returns a module for a specific version of AMF.

    @param use_ext: Whether to use the extensions. If `None` (the default) the
        extension will be attempted before falling back to the pure python
        version. If `False`, only the pure python version will be returned. If
        `True` the extension will be returned. If the extension does not exist
        L{ImportError} will be raised.
    """
    if version not in ENCODING_TYPES:
        raise ValueError('Invalid AMF version: %r specified' % (version,))

    module_name = '.amf%s' % (version,)

    if use_ext is None:
        packages = ['miniamf._accel', 'miniamf']
    elif use_ext:
        packages = ['miniamf._accel']
    else:
        packages = ['miniamf']

    exc = None
    for pkg in packages:
        try:
            return import_module(module_name, pkg)

        except ImportError as e:
            exc = e

    raise exc


def get_decoder(encoding, *args, **kwargs):
    """
    Returns a L{codec.Decoder} capable of decoding AMF[C{encoding}] streams.

    @param encoding: AMF encoding type. One of L{ENCODING_TYPES}.
    @type encoding: C{int}
    @param use_ext: Whether to use the extensions. If `None` (the default) the
        extension will be attempted before falling back to the pure python
        version. If `False`, only the pure python version will be returned. If
        `True` the extension will be returned. If the extension does not exist
        L{ImportError} will be raised.
    @raise ValueError: Unknown C{encoding}.
    """
    use_ext = kwargs.pop('use_ext', None)
    module = _get_amf_module(encoding, use_ext)
    return module.Decoder(*args, **kwargs)


def get_encoder(encoding, *args, **kwargs):
    """
    Returns a L{codec.Encoder} capable of encoding AMF[C{encoding}] streams.

    @kwarg encoding: AMF encoding type. One of L{ENCODING_TYPES}.
    @type encoding: C{int}
    @param use_ext: Whether to use the extensions. If `None` (the default) the
        extension will be attempted before falling back to the pure python
        version. If `False`, only the pure python version will be returned. If
        `True` the extension will be returned. If the extension does not exist
        L{ImportError} will be raised.
    @raise ValueError: Unknown C{encoding} type.
    """
    use_ext = kwargs.pop('use_ext', None)
    module = _get_amf_module(encoding, use_ext)
    return module.Encoder(*args, **kwargs)


def blaze_loader(alias):
    """
    Loader for BlazeDS framework compatibility classes, specifically
    implementing C{ISmallMessage}.

    @type alias: C{string}
    @see: U{BlazeDS<http://opensource.adobe.com/wiki/display/blazeds/BlazeDS>}
    @see: U{ISmallMessage on Adobe Help (external) <http://help.adobe.com/en_US
        /FlashPlatform/reference/actionscript/3/mx/messaging/messages/
        ISmallMessage.html>}
    @since: 0.5
    """
    if alias not in ('DSC', 'DSK'):
        return

    import miniamf.flex.messaging  # noqa

    return CLASS_CACHE[alias]


def flex_loader(alias):
    """
    Loader for L{Flex<pyamf.flex>} framework compatibility classes.

    @type alias: C{string}
    @raise UnknownClassAlias: Trying to load an unknown Flex compatibility
        class.
    """
    if not alias.startswith('flex.'):
        return

    try:
        if alias.startswith('flex.messaging.messages'):
            import miniamf.flex.messaging
        elif alias.startswith('flex.messaging.io'):
            import miniamf.flex
        elif alias.startswith('flex.data.messages'):
            import miniamf.flex.data  # noqa

        return CLASS_CACHE[alias]
    except KeyError:
        raise UnknownClassAlias(alias)


def add_type(type_, func=None):
    """
    Adds a custom type to L{TYPE_MAP}. A custom type allows fine grain control
    of what to encode to an AMF data stream.

    @raise TypeError: Unable to add C{_type} as a custom type (expected a class
                      or callable).
    @raise KeyError: Type already exists.
    @see: L{get_type} and L{remove_type}
    """
    def _check_type(type_):
        if not (isinstance(type_, type) or
                callable(type_)):
            raise TypeError(
                'Unable to add %r as a custom type (expected a class or '
                'callable)' % (type_,)
            )

    if isinstance(type_, list):
        type_ = tuple(type_)

    if type_ in TYPE_MAP:
        raise KeyError('Type %r already exists' % (type_,))

    if isinstance(type_, tuple):
        for x in type_:
            _check_type(x)
    else:
        _check_type(type_)

    TYPE_MAP[type_] = func


def get_type(type_):
    """
    Gets the declaration for the corresponding custom type.

    @raise KeyError: Unknown type.
    @see: L{add_type} and L{remove_type}
    """
    if isinstance(type_, list):
        type_ = tuple(type_)

    for k, v in TYPE_MAP.items():
        if k == type_:
            return v

    raise KeyError("Unknown type %r" % (type_,))


def remove_type(type_):
    """
    Removes the custom type declaration.

    @return: Custom type declaration.
    @see: L{add_type} and L{get_type}
    """
    declaration = get_type(type_)

    del TYPE_MAP[type_]

    return declaration


def add_error_class(klass, code):
    """
    Maps an exception class to a string code.

    An example::

        >>> class AuthenticationError(Exception):
        ...     pass
        ...
        >>> miniamf.add_error_class(AuthenticationError, 'Auth.Failed')
        >>> print miniamf.ERROR_CLASS_MAP
        {
            'TypeError': <type 'exceptions.TypeError'>,
            'IndexError': <type 'exceptions.IndexError'>,
            'Auth.Failed': <class '__main__.AuthenticationError'>,
            'KeyError': <type 'exceptions.KeyError'>,
            'NameError': <type 'exceptions.NameError'>,
            'LookupError': <type 'exceptions.LookupError'>
        }

    @param klass: Exception class
    @param code: Exception code
    @type code: string
    @see: L{remove_error_class}
    @raise TypeError: C{klass} must be of class type.
    @raise TypeError: Error classes must subclass the C{__builtin__.Exception}
        class.
    @raise ValueError: C{code} is already registered to an error class.
    """

    if not isinstance(klass, type):
        raise TypeError("klass must be a class type")

    mro = inspect.getmro(klass)

    if Exception not in mro:
        raise TypeError(
            'Error classes must subclass the __builtin__.Exception class')

    if code in ERROR_CLASS_MAP:
        raise ValueError('Code %s is already registered' % (code,))

    ERROR_CLASS_MAP[code] = klass


def remove_error_class(klass):
    """
    Removes a class from the L{ERROR_CLASS_MAP}.

    An example::

       >>> class AuthenticationError(Exception):
       ...     pass
       ...
       >>> miniamf.add_error_class(AuthenticationError, 'Auth.Failed')
       >>> miniamf.remove_error_class(AuthenticationError)

    @type klass: string or class
    @see: L{add_error_class}
    @raise ValueError: Cannot find registered class.
    @raise TypeError: C{klass} is invalid type.
    """

    if isinstance(klass, type):
        for k, v in ERROR_CLASS_MAP.items():
            if v is klass:
                klass = k
                break
        else:
            raise ValueError('Class %s is not registered' % (klass,))

    if not isinstance(klass, str):
        raise TypeError("Expected class or string, not %r" % klass)

    try:
        del ERROR_CLASS_MAP[klass]
    except KeyError:
        raise ValueError('Class %s is not registered' % (klass,))


def register_alias_type(klass, *args):
    """
    This function allows you to map subclasses of L{ClassAlias} to classes
    listed in C{args}.

    When an object is read/written from/to the AMF stream, a paired
    L{ClassAlias} instance is created (or reused), based on the Python class of
    that object. L{ClassAlias} provides important metadata for the class and
    can also control how the equivalent Python object is created, how the
    attributes are applied etc.

    Use this function if you need to do something non-standard.

    @since: 0.4
    @see:
     - L{unregister_alias_type}
    @raise RuntimeError: alias is already registered
    @raise TypeError: Value supplied to C{klass} is not a class
    @raise ValueError:
     - New aliases must subclass L{miniamf.ClassAlias}
     - At least one type must be supplied
    """
    def check_type_registered(arg):
        for k, v in ALIAS_TYPES.items():
            for kl in v:
                if arg is kl:
                    raise RuntimeError('%r is already registered under %r' % (
                        arg, k))

    if not isinstance(klass, type):
        raise TypeError('klass must be class')

    if not issubclass(klass, ClassAlias):
        raise ValueError('New aliases must subclass miniamf.ClassAlias')

    if len(args) == 0:
        raise ValueError('At least one type must be supplied')

    if len(args) == 1 and hasattr(args[0], '__call__'):
        check_type_registered(args[0])
    else:
        for arg in args:
            if not isinstance(arg, type):
                raise TypeError('%r must be class' % (arg,))

            check_type_registered(arg)

    ALIAS_TYPES[klass] = args

    for k, v in CLASS_CACHE.copy().items():
        new_alias = util.get_class_alias(v.klass)

        if new_alias is klass:
            meta = util.get_class_meta(v.klass)
            meta['alias'] = v.alias

            alias_klass = klass(v.klass, **meta)

            CLASS_CACHE[k] = alias_klass
            CLASS_CACHE[v.klass] = alias_klass


def unregister_alias_type(klass):
    """
    Removes the klass from the L{ALIAS_TYPES} register.

    @see: L{register_alias_type}
    """
    return ALIAS_TYPES.pop(klass, None)


def register_package(module=None, package=None, separator='.', ignore=None,
                     strict=True):
    """
    This is a helper function that takes the concept of Actionscript packages
    and registers all the classes in the supplied Python module under that
    package. It auto-aliased all classes in C{module} based on the parent
    C{package}.

    @param module: The Python module that will contain all the classes to
        auto alias.
    @type module: C{module} or C{dict}
    @param package: The base package name. e.g. 'com.example.app'. If this
        is C{None} then the value is inferred from C{module.__name__}.
    @type package: C{string} or C{None}
    @param separator: The separator used to append to C{package} to form the
        complete alias.
    @type separator: C{string}
    @param ignore: To give fine grain control over what gets aliased and what
        doesn't, supply a list of classes that you B{do not} want to be
        aliased.
    @type ignore: C{iterable}
    @param strict: Whether only classes that originate from C{module} will be
        registered.
    @type strict: C{boolean}

    @return: A dict of all the classes that were registered and their
        respective L{ClassAlias} counterparts.
    @since: 0.5
    @raise TypeError: Cannot get a list of classes from C{module}.
    """
    ignore = ignore or []

    if isinstance(module, str):
        if not module:
            raise TypeError('Cannot get list of classes from %r' % (module,))

        package = module
        module = None

    if module is None:
        prev_frame = inspect.stack()[1][0]
        module = prev_frame.f_locals

    if type(module) is dict:
        def has(x):
            return x in module

        get = module.__getitem__
    elif type(module) is list:
        def has(x):
            return x in module

        get = module.__getitem__
        strict = False
    else:
        def has(x):
            return hasattr(module, x)

        def get(x):
            return getattr(module, x)

    if package is None:
        if has('__name__'):
            package = get('__name__')
        else:
            raise TypeError('Cannot get list of classes from %r' % (module,))

    if has('__all__'):
        keys = get('__all__')
    elif hasattr(module, '__dict__'):
        keys = module.__dict__.keys()
    elif hasattr(module, 'keys'):
        keys = module.keys()
    elif isinstance(module, list):
        keys = range(len(module))
    else:
        raise TypeError('Cannot get list of classes from %r' % (module,))

    def check_attr(attr):
        if not isinstance(attr, type):
            return False

        if attr.__name__ in ignore:
            return False

        try:
            if strict and attr.__module__ != get('__name__'):
                return False
        except AttributeError:
            return False

        return True

    registered = {}
    for k in keys:
        klass = get(k)
        if not check_attr(klass):
            continue
        alias = '%s%s%s' % (package, separator, klass.__name__)

        registered[klass] = register_class(klass, alias)

    return registered


def set_default_etree(etree):
    """
    Sets the default interface that will called apon to both de/serialise XML
    entities. This means providing both C{tostring} and C{fromstring}
    functions.

    For testing purposes, will return the previous value for this (if any).
    """
    from miniamf import xml

    return xml.set_default_interface(etree)


def add_post_decode_processor(func):
    """
    Adds a function to be called when a payload has been successfully decoded.

    This is useful for adapter as the last chance to modify the Python graph
    before it enters user land.

    The function takes two arguments, the decoded payload and the context's
    `extra` dict. It MUST return the payload that will be finally returned.

    @see: L{miniamf.codec.Decoder.finalise}
    @since: 0.7.0
    """
    if not callable(func):
        raise TypeError('%r must be callable' % (func,))

    POST_DECODE_PROCESSORS.append(func)


# setup some some standard class registrations and class loaders.
register_class_loader(_load_class_from_module)
register_class(ASObject)
register_class_loader(flex_loader)
register_class_loader(blaze_loader)
register_alias_type(TypedObjectClassAlias, TypedObject)
register_alias_type(ErrorAlias, Exception)

register_adapters()

# Special case: The 'sets' adapter also applies to the built-in types
# 'set' and 'frozenset', so it should be loaded regardless of whether
# the 'sets' module is loaded.  (Also, in Python 3, the 'sets' module
# doesn't exist.)
import_module('._sets', 'miniamf.adapters')
