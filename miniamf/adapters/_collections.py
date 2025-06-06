# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
U{collections<http://docs.python.org/library/collections.html>} adapter module.

@since: 0.5
"""

import collections

import miniamf
from miniamf.adapters import util

miniamf.add_type(collections.deque, util.to_list)
miniamf.add_type(collections.defaultdict, util.to_dict)
miniamf.add_type(collections.Counter, util.to_dict)
miniamf.add_type(collections.OrderedDict, util.to_dict)
