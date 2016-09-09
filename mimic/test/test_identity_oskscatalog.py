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
from mimic.test.dummy import (
    make_example_internal_api,
    make_example_external_api
)
from mimic.test.helpers import json_request, request, get_template_id
from mimic.test.mixins import IdentityAuthMixin, InvalidJsonMixin, ServiceIdHeaderMixin


class TestIdentityOSKSCatalogAdminEndpointTemplatesList(
        SynchronousTestCase, IdentityAuthMixin, ServiceIdHeaderMixin):
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

    def test_list_only_internal_apis_available(self):
        """
        GET will return an empty listing when there are no External API
        endpoint templates.
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
        GET will return a endpoint template when there are External API
        endpoint templates.
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
        GET will only return the External API endpoint templates when they
        are available,
        even if there are also Internal APIs.
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
        GET can retrieve numerous External APIs that have External API Templates.
        """
        api_list = [
            make_example_external_api(
                self,
                name=self.eeapi_name + text_type(uuid.uuid4()),
                service_type='service-' + text_type(uuid.uuid4())
            )
            for ignored in range(10)
        ]
        #  eeapi needs to be the first in the list
        api_list.insert(0, self.eeapi)
        for api in api_list:
            self.core.add_api(api)

        self.assertEqual(len(self.core._uuid_to_api_external),
                         len(api_list))

        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri,
                         headers=self.headers))

        self.assertEqual(response.code, 200)

        self.assertEqual(len(json_body['OS-KSCATALOG']),
                         len(api_list))
        self.assertEqual(
            len(json_body['OS-KSCATALOG:endpointsTemplates_links']),
            0)


@ddt.ddt
class TestIdentityOSKSCatalogAdminEndpointTemplatesAdd(
        SynchronousTestCase, IdentityAuthMixin, InvalidJsonMixin):
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

    @ddt.data(
        'name', 'id', 'type', 'region'
    )
    def test_json_body_missing_required_field(self, remove_field):
        """
        POST - required fields must be present otherwise 400 is generated.
        """
        data = {
            'id': text_type(uuid.uuid4()),
            'name': 'some-name',
            'type': 'some-type',
            'region': 'some-region'
        }
        del data[remove_field]
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

    def test_invalid_service_id_in_json_body(self):
        """
        POST - Service ID must be valid, otherwise results in 404.
        """
        # Add a second API
        eeapi2 = make_example_external_api(
            self,
            name='d' + self.eeapi_name + text_type(uuid.uuid4()),
            service_type='service-' + text_type(uuid.uuid4())
        )
        eeapi2.id_key = '0'

        # ensure only one instance of the API has the endpoint template
        eeapi2.remove_template(get_template_id(self, eeapi2))
        self.core.add_api(eeapi2)
        self.core.add_api(self.eeapi)

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
        POST does not overwrite an existing endpoint template, 409 is
        generated instead.
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
        POST requires that the endpoint template and service have the same
        service types.
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

    @ddt.data(
        True, False
    )
    def test_new_endpoint_template(self, has_service_header):
        """
        POST to add a endpoint template results in 201, service-id header is
        optional.
        """
        self.core.add_api(self.eeapi)
        id_key = get_template_id(self, self.eeapi)

        eeapi2 = make_example_external_api(
            self,
            name=self.eeapi_name + text_type(uuid.uuid4()),
            service_type='service-' + text_type(uuid.uuid4())
        )
        eeapi2.remove_template(get_template_id(self, eeapi2))
        self.core.add_api(eeapi2)

        data = {
            'id': text_type(uuid.uuid4()),
            'name': self.eeapi_name,
            'type': self.eeapi.type_key,
            'region': 'some-region'
        }
        self.assertNotEqual(id_key, data['id'])

        if has_service_header:
            self.headers[b'serviceid'] = [self.eeapi.uuid_key.encode('utf8')]

        req = request(self, self.root, self.verb,
                      self.uri,
                      body=json.dumps(data).encode("utf-8"),
                      headers=self.headers)

        response = self.successResultOf(req)
        self.assertEqual(response.code, 201)


@ddt.ddt
class TestIdentityOSKSCatalogAdminEndpointTemplatesUpdate(
        SynchronousTestCase, IdentityAuthMixin, InvalidJsonMixin):
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

    @ddt.data(
        'id', 'name', 'type', 'region'
    )
    def test_json_body_missing_required_field_name(self, remove_field):
        """
        PUT - required fields must be present otherwise 400 is generated.
        """
        data = {
            'id': self.ept_template_id,
            'name': 'some-name',
            'type': 'some-type',
            'region': 'some-region'
        }
        del data[remove_field]

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

    def test_invalid_service_id_in_json_body(self):
        """
        PUT requires that the service id map to an existing service,
        otherwise results in a 404.
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
        PUT requires that the service matches, otherwise results in 409.
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

    def test_json_body_id_value_not_matching_url(self):
        """
        PUT requires that the endpoint template id in the URL and JSON data
        match, otherwise results in 409.
        """
        self.core.add_api(self.eeapi)

        eeapi2 = make_example_external_api(
            self,
            name=self.eeapi_name + text_type(uuid.uuid4()),
            service_type='service-' + text_type(uuid.uuid4())
        )
        eeapi2.remove_template(get_template_id(self, eeapi2))
        self.core.add_api(eeapi2)

        data = {
            'id': 'some-random-key',
            'name': self.eeapi_name,
            'type': self.eeapi.type_key,
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
            "Template ID in URL does not match that of the JSON body"
        )

    def test_invalid_template_id(self):
        """
        PUT requires the endpoint template id to match an existing endpoint
        template, otherwise results in 404.
        """
        self.core.add_api(self.eeapi)
        id_key = get_template_id(self, self.eeapi)
        self.eeapi.remove_template(id_key)

        data = {
            'id': id_key,
            'name': self.eeapi_name,
            'type': self.eeapi.type_key,
            'region': 'some-region'
        }

        self.headers[b'serviceid'] = [self.eeapi.uuid_key.encode('utf8')]

        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri,
                         body=data,
                         headers=self.headers))

        self.assertEqual(response.code, 404)
        self.assertEqual(json_body['itemNotFound']['code'], 404)
        self.assertEqual(
            json_body['itemNotFound']['message'],
            "Unable to update non-existent template. Template must "
            "first be added before it can be updated.",
        )

    @ddt.data(
        True, False
    )
    def test_update_endpoint_template(self, has_service_header):
        """
        PUT to update an endpoint template results in 201, service-id
        header is optional.
        """
        self.core.add_api(self.eeapi)
        id_key = get_template_id(self, self.eeapi)

        eeapi2 = make_example_external_api(
            self,
            name=self.eeapi_name + text_type(uuid.uuid4()),
            service_type='service-' + text_type(uuid.uuid4())
        )
        eeapi2.remove_template(get_template_id(self, eeapi2))
        self.core.add_api(eeapi2)

        data = {
            'id': id_key,
            'name': self.eeapi_name,
            'type': self.eeapi.type_key,
            'region': 'some-region'
        }

        if has_service_header:
            self.headers[b'serviceid'] = [self.eeapi.uuid_key.encode('utf8')]

        req = request(self, self.root, self.verb,
                      self.uri,
                      body=json.dumps(data).encode("utf-8"),
                      headers=self.headers)

        response = self.successResultOf(req)
        self.assertEqual(response.code, 201)


@ddt.ddt
class TestIdentityOSKSCatalogAdminEndpointTemplatesDelete(SynchronousTestCase, IdentityAuthMixin):
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

    def test_invalid_template_id(self):
        """
        DELTE requires a valid endpoint template id, otherwise results in 404.
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
        DELETE requires the endpoint template to exist, otherwise results
        in 404.
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

    @ddt.data(
        True, False
    )
    def test_remove_template_id(self, has_service_header):
        """
        DELETE removes an existing endpoint template, service id header is
        optional.
        """
        self.core.add_api(self.eeapi)
        if has_service_header:
            self.headers[b'serviceid'] = [self.eeapi.uuid_key.encode('utf8')]
        req = request(self, self.root, self.verb,
                      self.uri,
                      headers=self.headers)
        response = self.successResultOf(req)
        self.assertEqual(response.code, 204)
