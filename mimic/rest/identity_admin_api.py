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
    def catalog_entries(self, tenant_id):
        """
        Return the catalog entries for this tenant.
        """
        return []

    def resource_for_region(self, region, uri_prefix, session_store):
        """
        Creates an identity admin resource.
        """
        return _IdentityAdminImpl().app.resource()


class _IdentityAdminImpl(object):
    """
    Klein resources for the Identiy admin API.

    TODO: come up with a way better name than IdentityAdminImpl
    """
    app = MimicApp()

create_endpoint_template_schema = {
    "title": "Identity admin create endpoint template",
    "type": "object",
    "properties": {
        "OS-KSCATALOG:endpointTemplate": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string"
                },
                "region": {
                    "type": "string"
                },
                "type": {
                    "type": "string"
                },
                "name": {
                    "type": "string"
                },
                "publicURL": {
                    "type": "string"
                },
                "internalURL": {
                    "type": "string"
                },
                "adminURL": {
                    "type": "string"
                },
                "tenantAlias": {
                    "type": "string"
                },
                "version": {
                    "type": "boolean"
                },
                "versioninfo": {
                    "type": "string"
                },
                "versionlist": {
                    "type": "string"
                },
            },
            "required": ["region"]
        }
    }
}
