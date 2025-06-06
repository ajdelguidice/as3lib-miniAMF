# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
C{weakref} support.

@since: 0.6.2
"""

import weakref

import miniamf
from miniamf.adapters import util


def get_referent(reference, **kwargs):
    return reference()


miniamf.add_type(weakref.ref, get_referent)
miniamf.add_type(weakref.WeakValueDictionary, util.to_dict)
miniamf.add_type(weakref.WeakSet, util.to_list)
