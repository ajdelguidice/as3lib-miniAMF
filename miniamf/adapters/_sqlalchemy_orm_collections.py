# Copyright (c) The PyAMF Project.
# See LICENSE for details.

"""
SQLAlchemy adapter module.

@see: U{SQLAlchemy homepage<http://www.sqlalchemy.org>}

@since: 0.4
"""

from sqlalchemy.orm import collections

import miniamf
from miniamf.adapters import util


miniamf.add_type(collections.InstrumentedList, util.to_list)
miniamf.add_type(collections.InstrumentedDict, util.to_dict)
miniamf.add_type(collections.InstrumentedSet, util.to_set)


if hasattr(collections, 'CollectionAdapter'):
    miniamf.add_type(collections.CollectionAdapter, util.to_list)
