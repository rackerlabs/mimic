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
from mimic.test.dummy import make_example_external_api, ExternalApiStore
from mimic.test.helpers import json_request, request


class TestIdentityMimicOSKSCatalogAdminListExternalServices(SynchronousTestCase):
    """
    Tests for ``/identity/v2.0/services``, provided by
    :obj:`mimic.rest.idenity_api.IdentityApi`
    """
    def setUp(self):
        self.core = MimicCore(Clock(), [])
        self.root = MimicRoot(self.core).app.resource()
        self.uri = "/identity/v2.0/services"
        self.eeapi_name = u"externalServiceName"
        self.eeapi = make_example_external_api(
            name=self.eeapi_name,
            set_enabled=True
        )
        self.headers = {
            b'X-Auth-Token': [b'ABCDEF987654321']
        }
        self.verb = b"GET"

    def test_auth_fail(self):
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri))

        self.assertEqual(response.code, 401)
        self.assertEqual(json_body['unauthorized']['code'], 401)

    def test_list_empty(self):
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri,
                         headers=self.headers))

        self.assertEqual(response.code, 200)
        self.assertEqual(len(json_body["OS-KSADM:services"]), 0)

    def test_list_single(self):
        self.core.add_api(self.eeapi)
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri,
                         headers=self.headers))

        self.assertEqual(response.code, 200)
        self.assertEqual(len(json_body["OS-KSADM:services"]), 1)
        self.assertEqual(json_body["OS-KSADM:services"][0]['id'],
                         self.eeapi.uuid_key)
        self.assertEqual(json_body["OS-KSADM:services"][0]['type'],
                         self.eeapi.type_key)
        self.assertEqual(json_body["OS-KSADM:services"][0]['name'],
                         self.eeapi.name_key)

    def test_list_multiple(self):
        api_list = [self.eeapi]
        for _ in range(10):
            api_list.append(
                ExternalApiStore(
                    text_type(uuid.uuid4()),
                    self.eeapi_name + text_type(uuid.uuid4()),
                    'service-' + text_type(uuid.uuid4()),
                )
            )
        for api in api_list:
            self.core.add_api(api)
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri,
                         headers=self.headers))

        def validate_api(api_id, api_type, api_name):
            for api in api_list:
                if api.uuid_key == api_id:
                    self.assertEqual(api_id, api.uuid_key)
                    self.assertEqual(api_type, api.type_key)
                    self.assertEqual(api_name, api.name_key)

        self.assertEqual(response.code, 200)
        self.assertEqual(len(json_body["OS-KSADM:services"]), len(api_list))
        for entry in json_body["OS-KSADM:services"]:
            validate_api(entry['id'], entry['type'], entry['name'])


class TestIdentityMimicOSKSCatalogAdminCreateExternalService(SynchronousTestCase):
    """
    Tests for ``/identity/v2.0/services``, provided by
    :obj:`mimic.rest.idenity_api.IdentityApi`
    """
    def setUp(self):
        self.core = MimicCore(Clock(), [])
        self.root = MimicRoot(self.core).app.resource()
        self.uri = "/identity/v2.0/services"
        self.eeapi_name = u"externalServiceName"
        self.eeapi = make_example_external_api(
            name=self.eeapi_name,
            set_enabled=True
        )
        self.headers = {
            b'X-Auth-Token': [b'ABCDEF987654321']
        }
        self.verb = b"POST"

    def test_auth_fail(self):
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri))

        self.assertEqual(response.code, 401)
        self.assertEqual(json_body['unauthorized']['code'], 401)

    def test_invalid_json_body(self):
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
        data = {
            'type': 'some-type'
        }
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri,
                         body=data,
                         headers=self.headers))

        self.assertEqual(response.code, 400)
        self.assertEqual(json_body['badRequest']['code'], 400)
        self.assertEqual(json_body['badRequest']['message'],
                         "Invalid Content. 'name' and 'type' fields are "
                         "required.")

    def test_json_body_missing_required_field_type(self):
        data = {
            'name': 'some-name'
        }
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri,
                         body=data,
                         headers=self.headers))

        self.assertEqual(response.code, 400)
        self.assertEqual(json_body['badRequest']['code'], 400)
        self.assertEqual(json_body['badRequest']['message'],
                         "Invalid Content. 'name' and 'type' fields are "
                         "required.")

    def test_service_name_already_exists(self):
        self.core.add_api(self.eeapi)
        data = {
            'name': self.eeapi.name_key,
            'type': self.eeapi.type_key
        }
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri,
                         body=data,
                         headers=self.headers))

        self.assertEqual(response.code, 409)
        self.assertEqual(json_body['conflict']['code'], 409)
        self.assertEqual(json_body['conflict']['message'],
                         "Conflict: Service with the same name already "
                         "exists.")

    def test_successfully_add_service_no_id(self):
        data = {
            'name': self.eeapi.name_key,
            'type': self.eeapi.type_key
        }
        req = request(self, self.root, self.verb,
                      "/identity/v2.0/services",
                      body=json.dumps(data).encode("utf-8"),
                      headers=self.headers)

        response = self.successResultOf(req)
        self.assertEqual(response.code, 201)

    def test_successfully_add_service_with_id(self):
        data = {
            'name': self.eeapi.name_key,
            'type': self.eeapi.type_key,
            'id': text_type(uuid.uuid4())
        }
        req = request(self, self.root, self.verb,
                      self.uri,
                      body=json.dumps(data).encode("utf-8"),
                      headers=self.headers)

        response = self.successResultOf(req)
        self.assertEqual(response.code, 201)

    def test_successfully_add_service_with_description(self):
        data = {
            'name': self.eeapi.name_key,
            'type': self.eeapi.type_key,
            'description': 'testing external API'
        }
        req = request(self, self.root, self.verb,
                      self.uri,
                      body=json.dumps(data).encode("utf-8"),
                      headers=self.headers)

        response = self.successResultOf(req)
        self.assertEqual(response.code, 201)


class TestIdentityMimicOSKSCatalogAdminDeleteExternalService(SynchronousTestCase):
    """
    Tests for ``/identity/v2.0/services/<service-id>``, provided by
    :obj:`mimic.rest.idenity_api.IdentityApi`
    """
    def setUp(self):
        self.core = MimicCore(Clock(), [])
        self.root = MimicRoot(self.core).app.resource()
        self.eeapi_id = u"some-id"
        self.uri = "/identity/v2.0/services/" + self.eeapi_id
        self.eeapi_name = u"externalServiceName"
        self.eeapi = make_example_external_api(
            name=self.eeapi_name,
            set_enabled=True
        )
        self.eeapi2 = make_example_external_api(
            name=self.eeapi_name + " alternate"
        )
        self.eeapi.uuid_key = self.eeapi_id
        self.headers = {
            b'X-Auth-Token': [b'ABCDEF987654321']
        }
        self.verb = b"DELETE"

    def test_auth_fail(self):
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri))

        self.assertEqual(response.code, 401)
        self.assertEqual(json_body['unauthorized']['code'], 401)

    def test_invalid_service(self):
        data = {
            'name': 'some-name',
            'type': 'some-type',
            'id': 'some-id'
        }
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri,
                         body=data,
                         headers=self.headers))

        self.assertEqual(response.code, 404)
        self.assertEqual(json_body['itemNotFound']['code'], 404)
        self.assertEqual(json_body['itemNotFound']['message'],
                         "Service not found. Unable to remove.")

    def test_service_has_template(self):
        self.core.add_api(self.eeapi)
        data = {
            'name': self.eeapi.name_key,
            'type': self.eeapi.type_key,
            'id': self.eeapi.uuid_key
        }
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri,
                         body=data,
                         headers=self.headers))

        self.assertEqual(response.code, 409)
        self.assertEqual(json_body['conflict']['code'], 409)
        self.assertEqual(json_body['conflict']['message'],
                         "Service still has endpoint templates.")

    def test_remove_service(self):
        templates_to_remove = list(self.eeapi.endpoint_templates.keys())
        for template_id in templates_to_remove:
            self.eeapi.remove_template(template_id)

        self.core.add_api(self.eeapi)
        self.core.add_api(self.eeapi2)
        data = {
            'name': self.eeapi.name_key,
            'type': self.eeapi.type_key,
            'id': self.eeapi.uuid_key
        }

        req = request(self, self.root, self.verb,
                      self.uri,
                      body=json.dumps(data).encode("utf-8"),
                      headers=self.headers)

        response = self.successResultOf(req)
        self.assertEqual(response.code, 204)
