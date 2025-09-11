# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
C{django.db.models.fields} adapter module.

@see: U{Django Project<http://www.djangoproject.com>}
@since: 0.4
"""

from django.db.models import fields

import miniamf


def convert_NOT_PROVIDED(x, encoder):
    """
    @rtype: L{Undefined<miniamf.Undefined>}
    """
    return miniamf.Undefined


miniamf.add_type(lambda x: x is fields.NOT_PROVIDED, convert_NOT_PROVIDED)
