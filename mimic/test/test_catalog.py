from __future__ import absolute_import, division, unicode_literals

from twisted.trial.unittest import SynchronousTestCase

from mimic.catalog import Endpoint, Entry


class CatalogEntry(SynchronousTestCase):
    """
    Tests for creating a :class:`Entry` object
    """
    def setUp(self):
        self.tenant = u"some-tenant"
        self.service_type = u"some-type"
        self.service_name = u"some-service"

    def test_basic(self):
        """
        Absolute minimal creation of :obj:`Entry`
        """
        empty_iterable = []
        entry = Entry(
            self.tenant,
            self.service_type,
            self.service_name,
            empty_iterable
        )

        self.assertEqual(entry.tenant_id, self.tenant)
        self.assertEqual(entry.name, self.service_name)
        self.assertEqual(entry.type, self.service_type)
        self.assertEqual(entry.endpoints, empty_iterable)


class CatalogEndpoint(SynchronousTestCase):
    """
    Tests for creating a :class:`Endpoint` object
    """
    def setUp(self):
        self.tenant = u"some-tenant"
        self.region = u"some-region"
        self.endpointid = u"some-endpoint-id"
        self.internal_api_prefix = u"endpoint-api"
        self.request_prefix = u"http://internal.api/prefix"
        self.external_api_url = u"http://external.api/endpoint"

    def test_basic(self):
        """
        Absolute minimal creation of :obj:`Endpoint`
        """
        endpoint = Endpoint(
            self.tenant,
            self.region,
            self.endpointid
        )
        self.assertEqual(self.tenant, endpoint.tenant_id)
        self.assertEqual(self.region, endpoint.region)
        self.assertEqual(self.endpointid, endpoint.endpoint_id)
        self.assertIsNone(endpoint.prefix)
        self.assertFalse(endpoint.external)
        self.assertIsNone(endpoint.complete_url)

    def test_internal_endpoint(self):
        """
        Typical creation of :obj:`Endpoint` for an internal API
        """
        endpoint = Endpoint(
            self.tenant,
            self.region,
            self.endpointid,
            prefix=self.internal_api_prefix
        )
        self.assertEqual(self.tenant, endpoint.tenant_id)
        self.assertEqual(self.region, endpoint.region)
        self.assertEqual(self.endpointid, endpoint.endpoint_id)
        self.assertEqual(self.internal_api_prefix, endpoint.prefix)
        self.assertFalse(endpoint.external)
        self.assertIsNone(endpoint.complete_url)

        uri = endpoint.url_with_prefix(self.request_prefix)
        self.assertTrue(uri.startswith(self.request_prefix))

    def test_external_endpoint(self):
        """
        Typical creation of :obj:`Endpoint` for an external API
        """
        endpoint = Endpoint(
            self.tenant,
            self.region,
            self.endpointid,
            external=True,
            complete_url=self.external_api_url
        )
        self.assertEqual(self.tenant, endpoint.tenant_id)
        self.assertEqual(self.region, endpoint.region)
        self.assertEqual(self.endpointid, endpoint.endpoint_id)
        self.assertIsNone(endpoint.prefix)
        self.assertTrue(endpoint.external)
        self.assertIsNotNone(endpoint.complete_url)
        self.assertEqual(endpoint.complete_url, self.external_api_url)

        uri = endpoint.url_with_prefix(self.request_prefix)
        self.assertEqual(uri, self.external_api_url)

    def test_external_endpoint_invalid(self):
        """
        Invalid creation of :obj:`Endpoint` for an external API
        """
        with self.assertRaises(ValueError):
            Endpoint(
                self.tenant,
                self.region,
                self.endpointid,
                external=True,
                complete_url=None
            )
