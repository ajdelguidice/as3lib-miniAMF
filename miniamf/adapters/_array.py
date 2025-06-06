# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
U{array<http://docs.python.org/library/array.html>} adapter module.

Will convert all array.array instances to a python list before encoding. All
type information is lost (but degrades nicely).

@since: 0.5
"""

import array

import miniamf
from miniamf.adapters import util

miniamf.add_type(array.ArrayType, util.to_list)
