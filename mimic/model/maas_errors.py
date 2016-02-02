"""
Errors like the error cases from Rackspace Monitoring.
"""

from __future__ import division, unicode_literals

import attr
from six import text_type


@attr.s
class ParentDoesNotExist(Exception):
    """
    Error that occurs when a parent object does not exist.

    For instance, trying to access or modify a Check under a
    non-existing Entity will cause this error.
    """
    object_type = attr.ib(validator=attr.validators.instance_of(text_type))
    key = attr.ib(validator=attr.validators.instance_of(text_type))
    code = attr.ib(validator=attr.validators.instance_of(int), default=404)

    def to_json(self):
        """
        Serializes this error to a JSON-encodable dict.
        """
        return {'type': 'notFoundError',
                'code': self.code,
                'txnId': '.fake.mimic.transaction.id.c-1111111.ts-123444444.v-12344frf',
                'message': 'Parent does not exist',
                'details': 'Object "{0}" with key "{1}" does not exist'.format(
                    self.object_type, self.key)}


@attr.s
class ObjectDoesNotExist(Exception):
    """
    Error that occurs when a required object does not exist.
    """
    object_type = attr.ib(validator=attr.validators.instance_of(text_type))
    key = attr.ib(validator=attr.validators.instance_of(text_type))
    code = attr.ib(validator=attr.validators.instance_of(int), default=404)

    def to_json(self):
        """
        Serializes this error to a JSON-encodable dict.
        """
        return {'type': 'notFoundError',
                'code': self.code,
                'txnId': '.fake.mimic.transaction.id.c-1111111.ts-123444444.v-12344frf',
                'message': 'Object does not exist',
                'details': 'Object "{0}" with key "{1}" does not exist'.format(
                    self.object_type, self.key)}
