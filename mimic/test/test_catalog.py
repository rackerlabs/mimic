from __future__ import absolute_import, division, unicode_literals

from twisted.trial.unittest import SynchronousTestCase

from mimic.catalog import Endpoint, Entry


class CatalogEntry(SynchronousTestCase):
    """
    Testing of the :class:`Entry` object
    """
    def setUp(self):
        self.tenant = u"some-tenant"
        self.service_type = u"some-type"
        self.service_name = u"some-service"

    def test_basic(self):
        """
        Validate the requirements for creating an :obj:`Entry` object.
        At minimum the tenant, service type, and service name are
        defined, and no endpoints (regions) are available.
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
    Testing of the :class:`Endpoint` object
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
        Validate the requirements for creating an :obj`Endpoint` object.
        At minimum, the tenant, region, and endpoint id are defined;
        default parameters must also be checked.
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
        Validate creating an :obj:`Endpoint` for an internal API. In addition
        to the tenant, region, and endpoint id the prefix must also be
        specified.
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
        Validate creating an :obj:`Endpoint` for an external API. In addition
        to the tenant, region, and endpoint id both `external` must be set to
        `True` and the `complete_url` must be set.
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
        Validate that trying to creating an :obj:`Endpoint` to host an
        External API (e.g settings `external` to `True`) without setting
        `complete_url` will raise a `ValueError` exception.
        """
        with self.assertRaises(ValueError):
            Endpoint(
                self.tenant,
                self.region,
                self.endpointid,
                external=True,
                complete_url=None
            )
