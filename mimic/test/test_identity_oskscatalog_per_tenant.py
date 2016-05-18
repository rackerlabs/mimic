"""
Tests for mimic identity :mod:`mimic.rest.identity_api`
"""

from __future__ import absolute_import, division, unicode_literals

import json
import uuid

from six import text_type

from twisted.trial.unittest import SynchronousTestCase
from twisted.internet.task import Clock

from mimic.core import MimicCore
from mimic.resource import MimicRoot
from mimic.test.dummy import (
    make_example_internal_api,
    make_example_external_api
)
from mimic.test.helpers import json_request, request, get_template_id


class TestIdentityOSKSCatalogTenantAdminEndpointTemplatesList(SynchronousTestCase):
    """
    Tests for ``/identity/v2.0/<tenant-id>/OS-KSCATALOG/endpointTemplates``,
    provided by :obj:`mimic.rest.idenity_api.IdentityApi`
    """
    def setUp(self):
        self.tenant_id = 'some_tenant'
        self.core = MimicCore(Clock(), [])
        self.root = MimicRoot(self.core).app.resource()
        self.uri = ("/identity/v2.0/tenants/" + self.tenant_id +
            "/OS-KSCATALOG/endpoints"
        )
        self.eeapi_name = u"externalServiceName"
        self.eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True
        )
        self.headers = {
            b'X-Auth-Token': [b'ABCDEF987654321']
        }
        self.verb = b"GET"

    def test_auth_fail(self):
        """
        Validate X-Auth-Token required to access endpoint.
        """
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri))

        self.assertEqual(response.code, 401)
        self.assertEqual(json_body['unauthorized']['code'], 401)

    def test_invalid_service_id(self):
        """
        Validate a service-id that does not map to an actual service generates
        a 404 failure.
        """
        self.headers.update({
            'serviceid': [b'some-id']
        })
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri,
                         headers=self.headers))

        self.assertEqual(response.code, 404)
        self.assertEqual(json_body['itemNotFound']['code'], 404)

    def test_list_only_internal_apis_available(self):
        """
        Validate that if only Internal APIs are available that no templates are
        listed; only an empty list is returned.
        """
        self.core.add_api(make_example_internal_api(self))
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri,
                         headers=self.headers))

        self.assertEqual(response.code, 200)
        self.assertEqual(len(json_body['endpoints']), 0)
        self.assertEqual(len(json_body['endpoints_links']), 0)

    def test_list_single_template(self):
        """
        Validate that if an external API is present that its template will show
        up in the listing.
        """
        self.core.add_api(self.eeapi)

        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri,
                         headers=self.headers))

        self.assertEqual(response.code, 200)
        self.assertEqual(len(json_body['endpoints']), 1)
        self.assertEqual(len(json_body['endpoints_links']), 0)

    def test_list_single_template_external_and_internal_apis(self):
        """
        Validate that if both an internal and and external API are present that
        only the External API shows up in the template listing.
        """
        self.core.add_api(self.eeapi)
        self.core.add_api(make_example_internal_api(self))

        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri,
                         headers=self.headers))

        self.assertEqual(response.code, 200)
        self.assertEqual(len(json_body['endpoints']), 1)
        self.assertEqual(len(json_body['endpoints_links']), 0)

    def test_multiple_external_apis(self):
        """
        """
        api_list = [self.eeapi]
        for _ in range(10):
            api_list.append(
                make_example_external_api(
                    self,
                    name=self.eeapi_name + text_type(uuid.uuid4()),
                    service_type='service-' + text_type(uuid.uuid4())
                )
            )
        for api in api_list:
            self.core.add_api(api)

        self.assertEqual(len(self.core._uuid_to_api_external),
                         len(api_list))

        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri,
                         headers=self.headers))

        def get_header(header_name):
            return response.headers.getRawHeaders(header_name)[0].decode("utf-8")

        self.assertEqual(response.code, 200)

        self.assertEqual(len(json_body['endpoints']),
                         len(api_list))
        self.assertEqual(len(json_body['endpoints_links']), 0)
