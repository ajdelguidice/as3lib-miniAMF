# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
C{django.utils.translation} adapter module.

@see: U{Django Project<http://www.djangoproject.com>}
@since: 0.4.2
"""

# ugettext_lazy was replaced with gettext_lazy
from django.utils.translation import gettext_lazy
import miniamf


def convert_lazy(lazy, encoder=None):
    try:
        return str(lazy)
    except Exception as e:
        raise ValueError("Don't know how to convert lazy value " +
                         repr(lazy)) from e


miniamf.add_type(type(gettext_lazy('foo')), convert_lazy)
