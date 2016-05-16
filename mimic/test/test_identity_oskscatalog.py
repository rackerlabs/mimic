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
    make_example_external_api,
    ExampleAPI,
)
from mimic.test.helpers import json_request, request


class TestIdentityOSKSCatalogAdminEndpointTemplatesList(SynchronousTestCase):
    """
    Tests for ``/identity/v2.0/OS-KSCATALOG/endpointTemplates``, provided by
    :obj:`mimic.rest.idenity_api.IdentityApi`
    """
    def setUp(self):
        self.core = MimicCore(Clock(), [])
        self.root = MimicRoot(self.core).app.resource()
        self.uri = "/identity/v2.0/OS-KSCATALOG/endpointTemplates"
        self.eeapi_name = u"externalServiceName"
        self.eeapi = make_example_external_api(
            name=self.eeapi_name,
            set_enabled=True
        )
        self.headers = {
            b'X-Auth-Token': [b'ABCDEF987654321']
        }

    def test_auth_fail(self):
        """
        Validate X-Auth-Token required to access endpoint.
        """
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, b"GET",
                         self.uri))

        self.assertEqual(response.code, 401)
        self.assertEqual(json_body['unauthorized']['code'], 401)

    def test_invalid_service_id(self):
        """
        Validate a service-id that does not map to an actual service
        generates a 404 failure.
        """
        self.headers.update({
            'serviceid': [b'some-id']
        })
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, b"GET",
                         self.uri,
                         headers=self.headers))

        self.assertEqual(response.code, 404)
        self.assertEqual(json_body['itemNotFound']['code'], 404)

    def test_list_only_internal_apis_available(self):
        """
        Validate that if only Internal APIs are available that no
        templates are listed; only an empty list is returned.
        """
        self.core.add_api(ExampleAPI())
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, b"GET",
                         self.uri,
                         headers=self.headers))

        self.assertEqual(response.code, 200)
        self.assertEqual(len(json_body['OS-KSCATALOG']), 0)

    def test_list_single_template(self):
        """
        Validate that if an external API is present that its
        template will show up in the listing.
        """
        self.core.add_api(self.eeapi)

        (response, json_body) = self.successResultOf(
            json_request(self, self.root, b"GET",
                         self.uri,
                         headers=self.headers))

        self.assertEqual(response.code, 200)
        self.assertEqual(len(json_body['OS-KSCATALOG']), 1)

    def test_list_single_template_external_and_internal_apis(self):
        """
        Validate that if both an internal and and external API are
        present that only the External API shows up in the template
        listing.
        """
        self.core.add_api(self.eeapi)
        self.core.add_api(ExampleAPI())

        (response, json_body) = self.successResultOf(
            json_request(self, self.root, b"GET",
                         self.uri,
                         headers=self.headers))

        self.assertEqual(response.code, 200)
        self.assertEqual(len(json_body['OS-KSCATALOG']), 1)

    def test_multiple_external_apis(self):
        """
        """
        api_list = [self.eeapi]
        for _ in range(10):
            api_list.append(
                make_example_external_api(
                    name=self.eeapi_name + text_type(uuid.uuid4()),
                    service_type='service-' + text_type(uuid.uuid4())
                )
            )
        for api in api_list:
            self.core.add_api(api)

        self.assertEqual(len(self.core._uuid_to_api_external),
                         len(api_list))

        (response, json_body) = self.successResultOf(
            json_request(self, self.root, b"GET",
                         self.uri,
                         headers=self.headers))

        def get_header(header_name):
            return response.headers.getRawHeaders(header_name)[0].decode("utf-8")

        self.assertEqual(response.code, 200)
        self.assertEqual(int(get_header(b'x-core-api-count')), len(api_list))
        self.assertEqual(int(get_header(b'x-api-count')), len(api_list))
        self.assertEqual(int(get_header(b'x-service-count')), len(api_list))

        self.assertEqual(len(json_body['OS-KSCATALOG']),
                         len(api_list))


class TestIdentityOSKSCatalogAdminEndpointTemplatesAdd(SynchronousTestCase):
    """
    Tests for ``/identity/v2.0/OS-KSCATALOG/endpointTemplates``, provided by
    :obj:`mimic.rest.idenity_api.IdentityApi`
    """
    def setUp(self):
        self.core = MimicCore(Clock(), [])
        self.root = MimicRoot(self.core).app.resource()
        self.uri = "/identity/v2.0/OS-KSCATALOG/endpointTemplates"
        self.eeapi_name = u"externalServiceName"
        self.eeapi = make_example_external_api(
            name=self.eeapi_name,
            set_enabled=True
        )
        self.headers = {
            b'X-Auth-Token': [b'ABCDEF987654321']
        }

    def test_auth_fail(self):
        """
        Validate X-Auth-Token required to access endpoint.
        """
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, b"POST",
                         self.uri))

        self.assertEqual(response.code, 401)
        self.assertEqual(json_body['unauthorized']['code'], 401)

    def test_invalid_json_body(self):
        """
        Validate that a JSON message body is required.
        """
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, b"POST",
                         self.uri,
                         body=b'<xml>ensure json failure',
                         headers=self.headers))

        self.assertEqual(response.code, 400)
        self.assertEqual(json_body['badRequest']['code'], 400)
        self.assertEqual(json_body['badRequest']['message'],
                         'Invalid JSON request body')

    def test_json_body_missing_required_field_name(self):
        """
        Validate that the name field in the JSON body is required.
        """
        data = {
            'id': text_type(uuid.uuid4()),
            'type': 'some-type',
            'region': 'some-region'
        }
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, b"POST",
                         self.uri,
                         body=data,
                         headers=self.headers))

        self.assertEqual(response.code, 400)
        self.assertEqual(json_body['badRequest']['code'], 400)
        self.assertTrue(
            json_body['badRequest']['message'].startswith(
                "JSON body does not contain the required parameters:"
            )
        )

    def test_json_body_missing_required_field_id(self):
        """
        Validate that the id field in the JSON body is required.
        """
        data = {
            'name': 'some-name',
            'type': 'some-type',
            'region': 'some-region'
        }
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, b"POST",
                         self.uri,
                         body=data,
                         headers=self.headers))

        self.assertEqual(response.code, 400)
        self.assertEqual(json_body['badRequest']['code'], 400)
        self.assertTrue(
            json_body['badRequest']['message'].startswith(
                "JSON body does not contain the required parameters:"
            )
        )

    def test_json_body_missing_required_field_type(self):
        """
        Validate that the type field in the JSON body is required.
        """
        data = {
            'id': text_type(uuid.uuid4()),
            'name': 'some-name',
            'region': 'some-region'
        }
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, b"POST",
                         self.uri,
                         body=data,
                         headers=self.headers))

        self.assertEqual(response.code, 400)
        self.assertEqual(json_body['badRequest']['code'], 400)
        self.assertTrue(
            json_body['badRequest']['message'].startswith(
                "JSON body does not contain the required parameters:"
            )
        )

    def test_json_body_missing_required_field_region(self):
        """
        Validate that the region field in the JSON body is required.
        """
        data = {
            'id': text_type(uuid.uuid4()),
            'name': 'some-name',
            'type': 'some-type'
        }
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, b"POST",
                         self.uri,
                         body=data,
                         headers=self.headers))

        self.assertEqual(response.code, 400)
        self.assertEqual(json_body['badRequest']['code'], 400)
        self.assertTrue(
            json_body['badRequest']['message'].startswith(
                "JSON body does not contain the required parameters:"
            )
        )

    def test_invalid_service_name(self):
        """
        Validate a service-id that does not map to an actual service
        generates a 404 failure.
        """
        data = {
            'id': text_type(uuid.uuid4()),
            'name': 'some-name',
            'type': 'some-type',
            'region': 'some-region'
        }
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, b"POST",
                         self.uri,
                         body=data,
                         headers=self.headers))

        self.assertEqual(response.code, 404)
        self.assertEqual(json_body['itemNotFound']['code'], 404)

    def test_existing_endpoint_template(self):
        """
        Validate adding an endpoint template that matches an existing
        endpoint template generates a 409 failure.
        """
        self.core.add_api(self.eeapi)
        id_key = None
        for k, v in self.eeapi.endpoint_templates.items():
            id_key = k

        data = {
            'id': id_key,
            'name': self.eeapi_name,
            'type': 'some-type',
            'region': 'some-region'
        }
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, b"POST",
                         self.uri,
                         body=data,
                         headers=self.headers))

        self.assertEqual(response.code, 409)
        self.assertEqual(json_body['conflict']['code'], 409)

    def test_new_endpoint_template_wrong_service_type(self):
        """
        Validate that the service type must match between
        the service and the endpoint template.
        """
        self.core.add_api(self.eeapi)
        id_key = None
        for k, v in self.eeapi.endpoint_templates.items():
            id_key = k

        data = {
            'id': text_type(uuid.uuid4()),
            'name': self.eeapi_name,
            'type': 'some-type',
            'region': 'some-region'
        }
        self.assertNotEqual(id_key, data['id'])
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, b"POST",
                         self.uri,
                         body=data,
                         headers=self.headers))

        self.assertEqual(response.code, 409)
        self.assertEqual(json_body['conflict']['code'], 409)

    def test_new_endpoint_template(self):
        """
        Validate that a new endpoint template can be added.
        """
        self.core.add_api(self.eeapi)
        id_key = None
        for k, v in self.eeapi.endpoint_templates.items():
            id_key = k

        data = {
            'id': text_type(uuid.uuid4()),
            'name': self.eeapi_name,
            'type': self.eeapi.type_key,
            'region': 'some-region'
        }
        self.assertNotEqual(id_key, data['id'])

        req = request(self, self.root, b"POST",
                      self.uri,
                      body=json.dumps(data).encode("utf-8"),
                      headers=self.headers)

        response = self.successResultOf(req)
        self.assertEqual(response.code, 201)


class TestIdentityOSKSCatalogAdminEndpointTemplatesUpdate(SynchronousTestCase):
    """
    Tests for ``/identity/v2.0/OS-KSCATALOG/endpointTemplates``, provided by
    :obj:`mimic.rest.idenity_api.IdentityApi`
    """
    def setUp(self):
        self.core = MimicCore(Clock(), [])
        self.root = MimicRoot(self.core).app.resource()
        self.uri = "/identity/v2.0/OS-KSCATALOG/endpointTemplates"
        self.eeapi_name = u"externalServiceName"
        self.eeapi = make_example_external_api(
            name=self.eeapi_name,
            set_enabled=True
        )
        self.headers = {
            b'X-Auth-Token': [b'ABCDEF987654321']
        }

    def test_auth_fail(self):
        """
        Validate X-Auth-Token required to access endpoint
        """
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, b"PUT",
                         self.uri))

        self.assertEqual(response.code, 401)
        self.assertEqual(json_body['unauthorized']['code'], 401)


class TestIdentityOSKSCatalogAdminEndpointTemplatesDelete(SynchronousTestCase):
    """
    Tests for ``/identity/v2.0/OS-KSCATALOG/endpointTemplates``, provided by
    :obj:`mimic.rest.idenity_api.IdentityApi`
    """
    def setUp(self):
        self.core = MimicCore(Clock(), [])
        self.root = MimicRoot(self.core).app.resource()
        self.uri = "/identity/v2.0/OS-KSCATALOG/endpointTemplates"
        self.eeapi_name = u"externalServiceName"
        self.eeapi = make_example_external_api(
            name=self.eeapi_name,
            set_enabled=True
        )
        self.headers = {
            b'X-Auth-Token': [b'ABCDEF987654321']
        }

    def test_auth_fail(self):
        """
        Validate X-Auth-Token required to access endpoint
        """
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, b"DELETE",
                         self.uri))

        self.assertEqual(response.code, 401)
        self.assertEqual(json_body['unauthorized']['code'], 401)
