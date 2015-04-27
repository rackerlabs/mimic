# -*- test-case-name: mimic.test.test_identity_admin -*-
"""
Mocks for the identity admin API.
"""
from zope.interface import implementer

from mimic.imimic import IAPIMock


@implementer(IAPIMock)
class IdentityAdminAPI(object):
    """
    A mock of the OpenStack Identity Admin API.
    """
