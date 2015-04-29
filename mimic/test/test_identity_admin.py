"""
Tests for the identity admin API.
"""
from jsonschema import validate

from pyrsistent import freeze

from twisted.plugin import IPlugin
from twisted.trial.unittest import SynchronousTestCase
from twisted.web.resource import IResource

from zope.interface.verify import verifyObject

from mimic.imimic import IAPIMock
from mimic.rest import identity_admin_api as api
from mimic.test.fixtures import APIMockHelper, TenantAuthentication
from mimic.test.helpers import json_request


class IdentityAdminAPITests(SynchronousTestCase):
    """
    Tests for the identity admin API mock.
    """
    def setUp(self):
        """
        Create a identity API mock instance for testing.
        """
        self.mock = api.IdentityAdminAPI()

    def test_interface(self):
        """
        The identity admin implements the IPlugin and IAPIMock interfaces
        faithfully.
        """
        verifyObject(IAPIMock, self.mock)
        verifyObject(IPlugin, self.mock)

    def _get_resource(self):
        """
        Gets the resource from the API mock.
        """
        store = None
        return self.mock.resource_for_region("REG", "prefix", store)

    def test_catalog_entires(self):
        """
        By default, :meth:`catalog_entries` returns an empty list.
        """
        self.assertEqual(self.mock.catalog_entries("1234"), [])

    def test_resource_for_region(self):
        """
        :meth:`resource_for_region` returns an identity admin resource.
        """
        resource = self._get_resource()
        verifyObject(IResource, resource)


class EndpointTemplateCreationTests(SynchronousTestCase):
    """
    Tests for endpoint template creation.
    """
    def setUp(self):
        self.helper = APIMockHelper(self, [api.IdentityAdminAPI()])

    def test_create_endpoint_template(self):
        """
        Creating an endpoint template adds it to the service catalog of
        new users.
        """
        before = self.helper.service_catalog_json
        entries = [e for e in before["access"]["serviceCatalog"]
                   if e["type"] == "mimic:added-by-admin-api"]
        self.assertEqual(len(entries), 0)

        # TODO: figure out how to get the admin URI here, which means solving


create_endpoint_template_example = freeze({
    "OS-KSCATALOG:endpointTemplate": {
        "region": "MIMIC",
        "name": "A thing added by the admin API",
        "type": "mimic:added-by-admin-api",
        "publicURL": "https://added-by-admin.mimic.public.com/v1",
        "internalURL": "https://added-by-admin.mimic.internal.com/v1",
        "adminURL": "https://added-by-admin.mimic.admin.com/v1",
        "RAX-AUTH:tenantAlias": "{tenant}"
    }
})

version_info_example = freeze({
    "versionId": "1",
    "versionInfo": "https://compute.north.public.com/v1/",
    "versionList": "https://compute.north.public.com/"
})

create_endpoint_template_example_with_version_info = (
    create_endpoint_template_example.transform(
        ["OS-KSCATALOG:endpointTemplate"],
        version_info_example.update))

class CreateEndpointTemplateSchemaTests(SynchronousTestCase):
    """
    Tests for the schema for endpoint template creation.
    """
    def test_validates(self):
        """
        Test simple schema validation.
        """
        validate(create_endpoint_template_example,
                 api.create_endpoint_template_schema)
        validate(create_endpoint_template_example_with_version_info,
                 api.create_endpoint_template_schema)
