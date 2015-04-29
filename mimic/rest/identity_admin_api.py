# -*- test-case-name: mimic.test.test_identity_admin -*-
"""
Mocks for the identity admin API.
"""
from json import dumps, loads

from jsonschema import validate

from zope.interface import implementer

from mimic.imimic import IAPIMock
from mimic.rest.mimicapp import MimicApp
from mimic.util.helper import bad_request


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

    @app.route("/v2.0/OS-KSCATALOG/endpointTemplates", methods=("POST",))
    def add_endpoint_template(self, request):
        """
        Adds an endpoint template.
        """
        try:
            content = loads(request.content.read())
            content = content["OS_KSCATALOG:endpointTemplate"]
        except (ValueError, KeyError):
            request.setResponseCode(400)
            return dumps(bad_request("Invalid JSON request body"))



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
                "global": {
                    "type": "boolean",
                    "description": "Is this auto-enabled for all tenants?"
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
                "RAX-AUTH:tenantAlias": {
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
