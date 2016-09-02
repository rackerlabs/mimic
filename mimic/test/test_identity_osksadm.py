"""
Tests for mimic identity :mod:`mimic.rest.identity_api`
"""

from __future__ import absolute_import, division, unicode_literals

import json
import uuid

import ddt
from six import text_type

from twisted.trial.unittest import SynchronousTestCase
from twisted.internet.task import Clock

from mimic.core import MimicCore
from mimic.resource import MimicRoot
from mimic.test.dummy import make_example_external_api, ExternalApiStore
from mimic.test.helpers import json_request, request
from mimic.test.mixins import IdentityAuthMixin, InvalidJsonMixin


@ddt.ddt
class TestIdentityMimicOSKSCatalogAdminListExternalServices(SynchronousTestCase, IdentityAuthMixin):
    """
    Tests for ``/identity/v2.0/services``, provided by
    :obj:`mimic.rest.idenity_api.IdentityApi`
    """
    def setUp(self):
        self.core = MimicCore(Clock(), [])
        self.root = MimicRoot(self.core).app.resource()
        self.uri = "/identity/v2.0/services"
        self.eeapi_name = u"externalServiceName"
        self.headers = {
            b'X-Auth-Token': [b'ABCDEF987654321']
        }
        self.verb = b"GET"

    @ddt.data(
        0, 1, 10
    )
    def test_listing(self, api_entry_count):
        """
        GET will list the registered services.
        """
        # create the desired number of services per test parameter
        api_list = [
            ExternalApiStore(
                text_type(uuid.uuid4()),
                self.eeapi_name + text_type(uuid.uuid4()),
                'service-' + text_type(uuid.uuid4()),
            )
            for ignored in range(api_entry_count)
        ]

        # add the services
        for api in api_list:
            self.core.add_api(api)

        # retrieve the listing using the REST interface
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri,
                         headers=self.headers))

        def validate_api(api_id, api_type, api_name):
            """
            Lookup the API in the test's set of APIs  and match the values
            """
            matching_apis = [
                api for api in api_list if api.uuid_key == api_id
            ]
            self.assertEqual(len(matching_apis), 1)
            [matching_api] = matching_apis
            self.assertEqual(api_id, matching_api.uuid_key)
            self.assertEqual(api_type, matching_api.type_key)
            self.assertEqual(api_name, matching_api.name_key)

        self.assertEqual(response.code, 200)
        self.assertEqual(len(json_body["OS-KSADM:services"]), len(api_list))
        # ensure all services in the response match one in the generated
        # initially generated set
        for entry in json_body["OS-KSADM:services"]:
            validate_api(entry['id'], entry['type'], entry['name'])


@ddt.ddt
class TestIdentityMimicOSKSCatalogAdminCreateExternalService(
        SynchronousTestCase, IdentityAuthMixin, InvalidJsonMixin):
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
            self,
            name=self.eeapi_name,
            set_enabled=True
        )
        self.headers = {
            b'X-Auth-Token': [b'ABCDEF987654321']
        }
        self.verb = b"POST"

    @ddt.data(
        'type', 'name'
    )
    def test_json_body_missing_required_field(self, remove_field):
        """
        POST requires 'name' field otherwise 400 is generated.
        """
        # normal JSON body
        data = {
            'type': 'some-type',
            'name': 'some-name'
        }
        # remove a portion of the body per the DDT data
        del data[remove_field]

        # POST the resulting JSON to the REST API
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri,
                         body=data,
                         headers=self.headers))

        # API should return 400 since a required field is missing
        self.assertEqual(response.code, 400)
        self.assertEqual(json_body['badRequest']['code'], 400)
        self.assertEqual(json_body['badRequest']['message'],
                         "Invalid Content. 'name' and 'type' fields are "
                         "required.")

    @ddt.data(
        (True, False, "Conflict: Service with the same name already exists."),
        (False, True, "Conflict: Service with the same uuid already exists."),
    )
    @ddt.unpack
    def test_service_name_or_id_already_exists(self, name_exists, id_exists, msg):
        """
        POST requires a unique UUID for the Service ID.
        """
        self.core.add_api(self.eeapi)
        data = {
            'id': self.eeapi.uuid_key if id_exists else text_type(uuid.uuid4()),
            'name': self.eeapi.name_key if name_exists else "some-other-name",
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
                         msg)

    @ddt.data(
        (True, True),
        (True, False),
        (False, True),
        (False, False)
    )
    @ddt.unpack
    def test_successfully_add_service(self, has_id_field, has_description):
        """
        POST accepts the service type and name regardless of whether
        an ID field is provided.
        """
        data = {
            'name': self.eeapi.name_key,
            'type': self.eeapi.type_key,
            'id': text_type(uuid.uuid4()),
            'description': 'testing external API'
        }
        if not has_id_field:
            del data['id']
        if not has_description:
            del data['description']

        req = request(self, self.root, self.verb,
                      "/identity/v2.0/services",
                      body=json.dumps(data).encode("utf-8"),
                      headers=self.headers)

        response = self.successResultOf(req)
        self.assertEqual(response.code, 201)


class TestIdentityMimicOSKSCatalogAdminDeleteExternalService(SynchronousTestCase, IdentityAuthMixin):
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
            self,
            name=self.eeapi_name,
            set_enabled=True
        )
        self.eeapi2 = make_example_external_api(
            self,
            name=self.eeapi_name + " alternate"
        )
        self.eeapi.uuid_key = self.eeapi_id
        self.headers = {
            b'X-Auth-Token': [b'ABCDEF987654321']
        }
        self.verb = b"DELETE"

    def test_invalid_service(self):
        """
        DELETE an unknown service will generate a 404.
        """
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
        """
        DELETE a service that still has a template results in 409.
        """
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
        """
        DELETE a service.
        """
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
