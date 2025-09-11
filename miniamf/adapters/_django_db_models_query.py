# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Django query adapter module.

Sets up basic type mapping and class mappings for a
Django models.

@see: U{Django Project<http://www.djangoproject.com>}
@since: 0.1b
"""

from django.db.models import query

import miniamf
from miniamf.adapters import util


miniamf.add_type(query.QuerySet, util.to_list)
