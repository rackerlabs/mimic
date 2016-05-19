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
        self.assertEqual(len(json_body['OS-KSCATALOG']), 0)
        self.assertEqual(
            len(json_body['OS-KSCATALOG:endpointsTemplates_links']),
            0)

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
        self.assertEqual(len(json_body['OS-KSCATALOG']), 1)
        self.assertEqual(
            len(json_body['OS-KSCATALOG:endpointsTemplates_links']),
            0)

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
        self.assertEqual(len(json_body['OS-KSCATALOG']), 1)
        self.assertEqual(
            len(json_body['OS-KSCATALOG:endpointsTemplates_links']),
            0)

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

        self.assertEqual(len(json_body['OS-KSCATALOG']),
                         len(api_list))
        self.assertEqual(
            len(json_body['OS-KSCATALOG:endpointsTemplates_links']),
            0)


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
            self,
            name=self.eeapi_name,
            set_enabled=True
        )
        self.headers = {
            b'X-Auth-Token': [b'ABCDEF987654321']
        }
        self.verb = b"POST"

    def test_auth_fail(self):
        """
        Validate X-Auth-Token required to access endpoint.
        """
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri))

        self.assertEqual(response.code, 401)
        self.assertEqual(json_body['unauthorized']['code'], 401)

    def test_invalid_json_body(self):
        """
        Validate that a JSON message body is required.
        """
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
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
            json_request(self, self.root, self.verb,
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
            json_request(self, self.root, self.verb,
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
            json_request(self, self.root, self.verb,
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
            json_request(self, self.root, self.verb,
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
            json_request(self, self.root, self.verb,
                         self.uri,
                         body=data,
                         headers=self.headers))

        self.assertEqual(response.code, 404)
        self.assertEqual(json_body['itemNotFound']['code'], 404)
        self.assertEqual(
            json_body['itemNotFound']['message'],
            "Service API for endoint template not found"
        )

    def test_existing_endpoint_template(self):
        """
        Validate adding an endpoint template that matches an existing
        endpoint template generates a 409 failure.
        """
        self.core.add_api(self.eeapi)
        id_key = get_template_id(self, self.eeapi)

        data = {
            'id': id_key,
            'name': self.eeapi_name,
            'type': 'some-type',
            'region': 'some-region'
        }
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri,
                         body=data,
                         headers=self.headers))

        self.assertEqual(response.code, 409)
        self.assertEqual(json_body['conflict']['code'], 409)
        self.assertEqual(
            json_body['conflict']['message'],
            "ID value is already assigned to an existing template"
        )

    def test_new_endpoint_template_wrong_service_type(self):
        """
        Validate that the service type must match between
        the service and the endpoint template.
        """
        self.core.add_api(self.eeapi)
        id_key = get_template_id(self, self.eeapi)

        data = {
            'id': text_type(uuid.uuid4()),
            'name': self.eeapi_name,
            'type': 'some-type',
            'region': 'some-region'
        }
        self.assertNotEqual(id_key, data['id'])
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri,
                         body=data,
                         headers=self.headers))

        self.assertEqual(response.code, 409)
        self.assertEqual(json_body['conflict']['code'], 409)
        self.assertEqual(
            json_body['conflict']['message'],
            "Endpoint already exists or service type does not match."
        )

    def test_new_endpoint_template(self):
        """
        Validate that a new endpoint template can be added.
        """
        self.core.add_api(self.eeapi)
        id_key = get_template_id(self, self.eeapi)

        eeapi2 = make_example_external_api(
            self,
            name=self.eeapi_name + text_type(uuid.uuid4()),
            service_type='service-' + text_type(uuid.uuid4())
        )
        eeapi2.remove_template(id_key)
        self.core.add_api(eeapi2)

        data = {
            'id': text_type(uuid.uuid4()),
            'name': self.eeapi_name,
            'type': self.eeapi.type_key,
            'region': 'some-region'
        }
        self.assertNotEqual(id_key, data['id'])

        req = request(self, self.root, self.verb,
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
        self.eeapi_name = u"externalServiceName"
        self.eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True
        )
        self.headers = {
            b'X-Auth-Token': [b'ABCDEF987654321']
        }
        self.verb = b"PUT"
        self.ept_template_id = get_template_id(self, self.eeapi)
        self.uri = (
            "/identity/v2.0/OS-KSCATALOG/endpointTemplates/" +
            self.ept_template_id
        )

    def test_auth_fail(self):
        """
        Validate X-Auth-Token required to access endpoint
        """
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri))

        self.assertEqual(response.code, 401)
        self.assertEqual(json_body['unauthorized']['code'], 401)

    def test_invalid_json_body(self):
        """
        Validate that a JSON message body is required.
        """
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
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
            'id': self.ept_template_id,
            'type': 'some-type',
            'region': 'some-region'
        }
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
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
            json_request(self, self.root, self.verb,
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
            'id': self.ept_template_id,
            'name': 'some-name',
            'region': 'some-region'
        }
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
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
            'id': self.ept_template_id,
            'name': 'some-name',
            'type': 'some-type'
        }
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
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
            'id': self.ept_template_id,
            'name': 'some-name',
            'type': 'some-type',
            'region': 'some-region'
        }
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri,
                         body=data,
                         headers=self.headers))

        self.assertEqual(response.code, 404)
        self.assertEqual(json_body['itemNotFound']['code'], 404)
        self.assertEqual(
            json_body['itemNotFound']['message'],
            "Service API for endoint template not found"
        )

    def test_new_endpoint_template_wrong_service_type(self):
        """
        Validate that the service type must match between
        the service and the endpoint template.
        """
        self.core.add_api(self.eeapi)

        data = {
            'id': self.ept_template_id,
            'name': self.eeapi_name,
            'type': 'some-type',
            'region': 'some-region'
        }
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri,
                         body=data,
                         headers=self.headers))

        self.assertEqual(response.code, 409)
        self.assertEqual(json_body['conflict']['code'], 409)
        self.assertEqual(
            json_body['conflict']['message'],
            "Endpoint already exists and service id or service type does not "
            "match."
        )

    def test_update_endpoint_template(self):
        """
        Validate that a new endpoint template can be updated.
        """
        self.core.add_api(self.eeapi)
        id_key = get_template_id(self, self.eeapi)

        eeapi2 = make_example_external_api(
            self,
            name=self.eeapi_name + text_type(uuid.uuid4()),
            service_type='service-' + text_type(uuid.uuid4())
        )
        eeapi2.remove_template(id_key)
        self.core.add_api(eeapi2)

        data = {
            'id': id_key,
            'name': self.eeapi_name,
            'type': self.eeapi.type_key,
            'region': 'some-region'
        }

        req = request(self, self.root, self.verb,
                      self.uri,
                      body=json.dumps(data).encode("utf-8"),
                      headers=self.headers)

        response = self.successResultOf(req)
        self.assertEqual(response.code, 201)


class TestIdentityOSKSCatalogAdminEndpointTemplatesDelete(SynchronousTestCase):
    """
    Tests for ``/identity/v2.0/OS-KSCATALOG/endpointTemplates``, provided by
    :obj:`mimic.rest.idenity_api.IdentityApi`
    """
    def setUp(self):
        self.core = MimicCore(Clock(), [])
        self.root = MimicRoot(self.core).app.resource()
        self.eeapi_name = u"externalServiceName"
        self.eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True
        )
        self.headers = {
            b'X-Auth-Token': [b'ABCDEF987654321']
        }
        self.verb = b"DELETE"
        self.ept_template_id = get_template_id(self, self.eeapi)
        self.uri = (
            "/identity/v2.0/OS-KSCATALOG/endpointTemplates/" +
            self.ept_template_id
        )

    def test_auth_fail(self):
        """
        Validate X-Auth-Token required to access endpoint.
        """
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri))

        self.assertEqual(response.code, 401)
        self.assertEqual(json_body['unauthorized']['code'], 401)

    def test_invalid_template_id(self):
        """
        Validate that removing a non-existent template will
        return a 404.
        """
        self.eeapi.remove_template(self.ept_template_id)
        self.core.add_api(self.eeapi)
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri,
                         headers=self.headers))

        self.assertEqual(response.code, 404)
        self.assertEqual(json_body['itemNotFound']['code'], 404)
        self.assertEqual(
            json_body['itemNotFound']['message'],
            "Unable to locate an External API with the given Template ID."
        )

    def test_invalid_template_id_with_service_header(self):
        """
        Validate that removing a non-existent template will
        return a 404.
        """
        self.eeapi.remove_template(self.ept_template_id)
        self.core.add_api(self.eeapi)
        self.headers[b'serviceid'] = [self.eeapi.uuid_key.encode('utf8')]
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri,
                         headers=self.headers))

        self.assertEqual(response.code, 404)
        self.assertEqual(json_body['itemNotFound']['code'], 404)
        self.assertEqual(
            json_body['itemNotFound']['message'],
            "Unable to locate an External API with the given Template ID."
        )

    def test_remove_template_id(self):
        """
        Validate removing an existing template will return a 204.
        """
        self.core.add_api(self.eeapi)
        req = request(self, self.root, self.verb,
                      self.uri,
                      headers=self.headers)
        response = self.successResultOf(req)
        self.assertEqual(response.code, 204)

    def test_remove_template_id_with_service_header(self):
        """
        Validate removing an existing template will return a 204.
        """
        self.core.add_api(self.eeapi)
        self.headers[b'serviceid'] = [self.eeapi.uuid_key.encode('utf8')]
        req = request(self, self.root, self.verb,
                      self.uri,
                      headers=self.headers)
        response = self.successResultOf(req)
        self.assertEqual(response.code, 204)
