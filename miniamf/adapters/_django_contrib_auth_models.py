"""
"""

from django.contrib.auth import models

import miniamf.adapters


models.User.__amf__ = {
    'exclude': ('message_set', 'password'),
    'readonly': ('username',)
}

# ensure that the adapter that we depend on is loaded ..
miniamf.get_adapter('django.db.models.base')

miniamf.register_package(models, models.__name__)
