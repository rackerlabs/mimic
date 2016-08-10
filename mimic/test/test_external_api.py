from __future__ import absolute_import, division, unicode_literals

from six import text_type

from twisted.trial.unittest import SynchronousTestCase

from mimic.imimic import IExternalAPIMock
from mimic.test.dummy import (
    exampleEndpointTemplate,
    make_example_internal_api,
    make_example_external_api
)
from mimic.test.fixtures import APIMockHelper, TenantAuthentication


class TestValidationPoints(SynchronousTestCase):

    def setUp(self):
        self.eeapi_name = u"externalServiceName"

    def test_external_api_no_service_resource(self):
        """
        Validate that an external API does not provide a Resource
        for Mimic to support that API within itself.
        """
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True
        )
        self.helper = APIMockHelper(self, [eeapi])
        self.core = self.helper.core

        # Find the UUID of the registered External API
        eeapi_id = None
        for uuid, api in self.core._uuid_to_api_external.items():
            eeapi_id = uuid

        self.assertIsNotNone(eeapi_id)

        self.assertIsNone(
            self.core.service_with_region(
                "EXTERNAL", eeapi_id, "fakebaseuri")
        )


class TestExternalApiMock(SynchronousTestCase):
    """
    Test cases to verify the :obj:`IExternalAPIMock`.
    """
    def setUp(self):
        self.eeapi_name = u"externalServiceName"
        self.eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True
        )
        self.helper = APIMockHelper(self, [self.eeapi])
        self.root = self.helper.root
        self.uri = self.helper.uri

    def test_external_api_attributes(self):
        """
        Validate that the :obj:`IExternalAPIMock` object.
        """
        self.assertTrue(IExternalAPIMock.providedBy(self.eeapi))
        self.assertIsInstance(self.eeapi.name_key, text_type)
        self.assertEqual(self.eeapi.name_key, self.eeapi_name)

    def test_external_api_mock_in_service_catalog(self):
        """
        Validate that the external API shows up in the service catalog
        when enabled globally for all tenants.
        """
        tenant_data = TenantAuthentication(self, self.root, "other", "other")
        service_endpoint = tenant_data.get_service_endpoint(
            "externalServiceName", "EXTERNAL")
        self.assertEqual(
            service_endpoint,
            'https://api.external.example.com:8080'
        )

    def test_external_api_mock_in_service_catalog_with_tenantid(self):
        """
        validate that the external API shows up in the service catalog
        when enabled globally and taht the tenantid will be properly
        in the URL.
        """
        for ept in self.eeapi.endpoint_templates.values():
            ept.internal_url = "http://internal.url/v1/%tenant_id%"
            ept.public_url = "http://public.url/v1/%tenant_id%"

        tenant_data = TenantAuthentication(self, self.root, "other", "other")

        ept_public_url = (
            "http://public.url/v1/" + tenant_data.get_tenant_id()
        )
        service_endpoint = tenant_data.get_service_endpoint(
            "externalServiceName", "EXTERNAL")
        self.assertEqual(
            service_endpoint,
            ept_public_url
        )


class TestTenantSpecificAPIs(SynchronousTestCase):
    """
    Test cases where the external API is disabled globally but
    enabled for a specific tenant
    """
    def setUp(self):
        self.eeapi_name = u"externalServiceName"
        self.eeapi_template_id = u"uuid-endpoint-template"
        self.eeapi_template = exampleEndpointTemplate(
            name=self.eeapi_name,
            endpoint_uuid=self.eeapi_template_id
        )
        self.eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            endpoint_templates=[self.eeapi_template],
            set_enabled=False
        )
        self.helper = APIMockHelper(self, [make_example_internal_api(self)])
        self.core = self.helper.core
        self.root = self.helper.root
        self.uri = self.helper.uri

        self.tenant_enabled_for = u"tenantWithApi"
        self.tenant_enabled_for_password = "udrowssap"
        self.tenant_data = TenantAuthentication(
            self,
            self.root,
            self.tenant_enabled_for,
            self.tenant_enabled_for_password
        )
        self.eeapi.enable_endpoint_for_tenant(
            self.tenant_data.get_tenant_id(),
            self.eeapi_template_id
        )
        self.core.add_api(self.eeapi)

    def test_single_endpoint_enabled_for_tenant(self):
        """
        Validate an endpoint can be enabled for a single tenant
        while being disabled globally for all tenants.
        """
        tenant_data = TenantAuthentication(
            self,
            self.root,
            self.tenant_enabled_for,
            self.tenant_enabled_for_password
        )
        externalService_endpoint = tenant_data.get_service_endpoint(
            "externalServiceName", "EXTERNAL")
        self.assertTrue(
            externalService_endpoint.startswith(
                'https://api.external.example.com:8080'))

    def test_disabled_globally_disabled(self):
        """
        Validate that even though an endpoint is enabled for one
        tenant that it remains globally disabled for all other tenants.
        """
        tenant_data = TenantAuthentication(self, self.root, "other", "other")
        with self.assertRaises(KeyError):
            tenant_data.get_service_endpoint(
                "serviceName", "EXTERNAL")

    def test_multiple_endpoints_enabled_for_tenant(self):
        """
        Validate when there are multiple endpoints enabled for a single
        tenant.
        """
        new_url = "https://api.new_region.example.com:9090"
        new_region = "NEW_REGION"
        new_eeapi_template_id = u"uuid-alternate-endpoint-template"
        new_eeapi_template = exampleEndpointTemplate(
            name=self.eeapi_name,
            endpoint_uuid=new_eeapi_template_id,
            region=new_region,
            url=new_url
        )
        self.eeapi.add_template(new_eeapi_template)
        self.eeapi.enable_endpoint_for_tenant(
            self.tenant_data.get_tenant_id(),
            new_eeapi_template_id
        )

        tenant_data = TenantAuthentication(
            self,
            self.root,
            self.tenant_enabled_for,
            self.tenant_enabled_for_password
        )
        externalService_endpoint = tenant_data.get_service_endpoint(
            "externalServiceName", new_region)
        self.assertTrue(
            externalService_endpoint.startswith(
                new_url))

    def test_multiple_endpoint_templates_only_one_enabled_for_tenant(self):
        """
        Code coverage for multiple templates when a disabled template
        is enabled for a specific tenant while another template remains
        in its default state.
        """
        new_url = "https://api.new_region.example.com:9090"
        new_region = "NEW_REGION"
        new_eeapi_template_id = u"uuid-alternate-endpoint-template"
        new_eeapi_template = exampleEndpointTemplate(
            name=self.eeapi_name,
            endpoint_uuid=new_eeapi_template_id,
            region=new_region,
            url=new_url
        )
        self.eeapi.add_template(new_eeapi_template)

        tenant_data = TenantAuthentication(
            self,
            self.root,
            self.tenant_enabled_for,
            self.tenant_enabled_for_password
        )
        with self.assertRaises(KeyError):
            tenant_data.get_service_endpoint("externalServiceName", new_region)


class TestDualModeApiMock(SynchronousTestCase):
    """
    Test cases to verify the :obj:`IExternalAPIMock`.
    """
    def setUp(self):
        self.eeapi_name = u"externalServiceName"
        self.ieapi = make_example_internal_api(self)
        self.eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True
        )
        self.helper = APIMockHelper(self, [self.ieapi, self.eeapi])
        self.root = self.helper.root
        self.uri = self.helper.uri

    def test_internal_vs_external_api_in_service_catalog(self):
        """
        Check both :obj:`IAPIMock` and :obj:`IExternalAPIMock`
        exist in the same service catalog.
        """
        tenant_data = TenantAuthentication(self, self.root, "other", "other")

        # there shouldn't an internal entry in the external region
        with self.assertRaises(KeyError):
            tenant_data.get_service_endpoint(
                "serviceName", "EXTERNAL")

        # pull both regions and verify they don't match
        externalService_endpoint = tenant_data.get_service_endpoint(
            "externalServiceName", "EXTERNAL")
        internalService_endpoint = tenant_data.get_service_endpoint(
            "serviceName", "ORD")
        self.assertNotEqual(externalService_endpoint, internalService_endpoint)
