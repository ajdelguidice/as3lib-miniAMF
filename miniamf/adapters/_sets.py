# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Adapter for the stdlib C{sets} module.

@since: 0.4
"""

import miniamf


def to_sorted_tuple(obj, encoder):
    return tuple(sorted(obj))


miniamf.add_type(frozenset, to_sorted_tuple)
miniamf.add_type(set, to_sorted_tuple)

# The sets module was removed in Python 3.
try:
    ModuleNotFoundError
except NameError:
    ModuleNotFoundError = ImportError

try:
    import sets
    miniamf.add_type(sets.ImmutableSet, to_sorted_tuple)
    miniamf.add_type(sets.Set, to_sorted_tuple)
except ModuleNotFoundError:
    pass
