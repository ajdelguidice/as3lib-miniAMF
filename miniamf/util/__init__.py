# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
AMF Utilities.

@since: 0.1.0
"""

import calendar
import datetime
import inspect

import miniamf

try:
    from .._accel.util import BufferedByteStream
except (ImportError, ModuleNotFoundError):
    from .pure import BufferedByteStream


__all__ = [
    'BufferedByteStream',
    'get_timestamp',
    'get_datetime',
    'get_properties',
    'set_attrs',
    'get_class_alias',
    'is_class_sealed',
    'get_class_meta',
    'get_module',
]


def get_timestamp(d):
    """
    Returns a UTC timestamp for a C{datetime.datetime} object.

    @type d: C{datetime.datetime}
    @return: UTC timestamp.
    @rtype: C{float}
    @see: Inspiration taken from the U{Intertwingly blog
        <http://intertwingly.net/blog/2007/09/02/Dealing-With-Dates>}.
    """
    if isinstance(d, datetime.date) and not isinstance(d, datetime.datetime):
        d = datetime.datetime.combine(d, datetime.time(0, 0, 0, 0))

    return calendar.timegm(d.utctimetuple()) + d.microsecond * 1e-6


def get_datetime(secs):
    """
    Return a UTC date from a timestamp.

    @type secs: C{long} or C{float}
    @param secs: Seconds since 1970.
    @return: UTC timestamp.
    @rtype: C{datetime.datetime}
    """
    # Note: we don't use utcfromtimestamp(secs) here, because on some platforms
    # the underlying C gmtime() cannot handle values outside the range
    # 1970-01-01T00:00:00Z through 2038-01-19T03:14:07Z.  Also, this way
    # fractional seconds are handled seamlessly (secs can be a float).
    # return (datetime.datetime.utcfromtimestamp(0) + datetime.timedelta(seconds=secs))
    return datetime.datetime.fromtimestamp(-datetime.datetime.fromtimestamp(0).replace(tzinfo=datetime.timezone.utc).timestamp()) + datetime.timedelta(seconds=secs)


def get_properties(obj):
    """
    Returns a list of properties for L{obj}

    @since: 0.5
    """
    if hasattr(obj, 'keys'):
        return list(obj.keys())
    elif hasattr(obj, '__dict__'):
        return list(obj.__dict__.keys())

    return []


def set_attrs(obj, attrs):
    """
    Applies a collection of attributes C{attrs} to object C{obj} in the most
    generic way possible.

    @param obj: An instance implementing C{__setattr__}, or C{__setitem__}
    @param attrs: A collection implementing the C{iteritems} function
    @type attrs: Usually a dict
    """
    o = setattr

    if hasattr(obj, '__setitem__'):
        o = type(obj).__setitem__

    for k, v in attrs.items():
        o(obj, k, v)


def get_class_alias(klass):
    """
    Tries to find a suitable L{miniamf.ClassAlias} subclass for C{klass}.
    """
    for k, v in miniamf.ALIAS_TYPES.items():
        for kl in v:
            try:
                if issubclass(klass, kl):
                    return k
            except TypeError:
                # not a class
                if hasattr(kl, '__call__'):
                    if kl(klass) is True:
                        return k


def is_class_sealed(klass):
    """
    Returns a boolean indicating whether or not the supplied class can accept
    dynamic properties.

    @rtype: C{bool}
    @since: 0.5
    """
    mro = inspect.getmro(klass)
    new = False

    if mro[-1] is object:
        mro = mro[:-1]
        new = True

    for kls in mro:
        if new and '__dict__' in kls.__dict__:
            return False

        if not hasattr(kls, '__slots__'):
            return False

    return True


def get_class_meta(klass):
    """
    Returns a C{dict} containing meta data based on the supplied class, useful
    for class aliasing.

    @rtype: C{dict}
    @since: 0.5
    """
    if not isinstance(klass, type) or klass is object:
        raise TypeError('klass must be a class object, got %r' % type(klass))

    meta = {
        'static_attrs': None,
        'exclude_attrs': None,
        'readonly_attrs': None,
        'amf3': None,
        'dynamic': None,
        'alias': None,
        'external': None,
        'synonym_attrs': None
    }

    if not hasattr(klass, '__amf__'):
        return meta

    a = klass.__amf__

    if type(a) is dict:
        def in_func(x):
            return x in a

        get_func = a.__getitem__
    else:
        def in_func(x):
            return hasattr(a, x)

        def get_func(x):
            return getattr(a, x)

    for prop in ['alias', 'amf3', 'dynamic', 'external']:
        if in_func(prop):
            meta[prop] = get_func(prop)

    for prop in ['static', 'exclude', 'readonly', 'synonym']:
        if in_func(prop):
            meta[prop + '_attrs'] = get_func(prop)

    return meta


def get_module(mod_name):
    """
    Load and return a module based on C{mod_name}.
    """
    if mod_name == '':
        raise ImportError('Unable to import empty module')

    mod = __import__(mod_name)
    components = mod_name.split('.')

    for comp in components[1:]:
        mod = getattr(mod, comp)

    return mod
