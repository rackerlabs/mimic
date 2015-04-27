# -*- test-case-name: mimic.test.test_identity_admin -*-
"""
Mocks for the identity admin API.
"""
from zope.interface import implementer

from mimic.imimic import IAPIMock
from mimic.rest.mimicapp import MimicApp


@implementer(IAPIMock)
class IdentityAdminAPI(object):
    """
    A mock of the OpenStack Identity Admin API.
    """
    def resource_for_region(self, region, uri_prefix, session_store):
        """
        Creates an identity admin resource.
        """
        return _IdentityAdminImpl().app.resource()


class _IdentityAdminImpl(object):
    """
    Klein resources for the Identiy admin API.

    TODO: come up with a way better name than identityadminimpl
    """
    app = MimicApp()
