from __future__ import absolute_import, division, unicode_literals

from six import text_type

from twisted.trial.unittest import SynchronousTestCase

from mimic.imimic import IExternalAPIMock
from mimic.test.dummy import ExampleAPI, ExampleExternalAPI
from mimic.test.fixtures import APIMockHelper, TenantAuthentication


class InvalidApiMock(object):
    pass


class TestValidationPoints(SynchronousTestCase):

    def test_core_gate_check(self):
        """
        Test that the gate check which ensures the submitted APIs
        are either :obj:`IAPIMock` or :obj:`IExternalAPIMock` works.
        """
        with self.assertRaises(TypeError):
            APIMockHelper(self, [InvalidApiMock()])

    def test_external_api_no_service_resource(self):
        self.eeapi_name = u"example-api"
        self.eeapi = ExampleExternalAPI(name=self.eeapi_name)
        self.helper = APIMockHelper(self, [self.eeapi])
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
        self.eeapi_name = u"example-api"
        self.eeapi = ExampleExternalAPI(name=self.eeapi_name)
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
        """
        tenant_data = TenantAuthentication(self, self.root, "other", "other")
        service_endpoint = tenant_data.get_service_endpoint(
            "externalServiceName", "EXTERNAL")
        self.assertTrue(
            service_endpoint.startswith(
                'https://api.external.example.com:8080'))


class TestDualModeApiMock(SynchronousTestCase):
    """
    Test cases to verify the :obj:`IExternalAPIMock`.
    """
    def setUp(self):
        self.eeapi_name = u"example-api"
        self.ieapi = ExampleAPI()
        self.eeapi = ExampleExternalAPI(name=self.eeapi_name)
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
