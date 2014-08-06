

import itertools
import json
import treq

from twisted.trial.unittest import SynchronousTestCase
from twisted.internet.task import Clock

from mimic.canned_responses.nova import server_template
from mimic.core import MimicCore
from mimic.resource import MimicRoot
from mimic.test.helpers import json_request, request
from mimic.rest.nova_api import NovaApi


class ResponseGenerationTests(SynchronousTestCase):

    """
    Tests for Nova response generation.
    """

    def test_server_template(self):
        """
        :obj:`server_template` generates a JSON object representing an
        individual Nova server.
        """

        input_server_info = {
            "flavorRef": "some_flavor",
            "imageRef": "some_image",
            "name": "some_server_name",
            "metadata": {
                "some_key": "some_value",
                "some_other_key": "some_other_value",
            }
        }

        counter = itertools.count(1)

        compute_service_uri_prefix = (
            "http://mimic.example.com/services/region/compute/"
        )

        actual = server_template("some_tenant", input_server_info,
                                 "some_server_id", "some_status",
                                 "the_current_time",
                                 lambda: next(counter),
                                 compute_service_uri_prefix)

        expectation = {
            "OS-DCF:diskConfig": "AUTO",
            "OS-EXT-STS:power_state": 1,
            "OS-EXT-STS:task_state": None,
            "OS-EXT-STS:vm_state": "active",
            "accessIPv4": "198.101.241.238",
            "accessIPv6": "2001:4800:780e:0510:d87b:9cbc:ff04:513a",
            "key_name": None,
            "addresses": {
                "private": [
                    {
                        "addr": "10.180.1.2",
                        "version": 4
                    }
                ],
                "public": [
                    {
                        "addr": "198.101.241.3",
                        "version": 4
                    },
                    {
                        "addr": "2001:4800:780e:0510:d87b:9cbc:ff04:513a",
                        "version": 6
                    }
                ]
            },
            "created": "the_current_time",
            "flavor": {
                "id": "some_flavor",
                "links": [
                    {
                        "href": ("http://mimic.example.com/services/region/"
                                 "compute/some_tenant/flavors/some_flavor"),
                        "rel": "bookmark"
                    }
                ]
            },
            "hostId": ("33ccb6c82f3625748b6f2338f54d8e9df07cc583251e001355569"
                       "056"),
            "id": "some_server_id",
            "image": {
                "id": "some_image",
                "links": [
                    {
                        "href": "http://mimic.example.com/services/region/"
                        "compute/some_tenant/images/some_image",
                        "rel": "bookmark"
                    }
                ]
            },
            "links": [
                {
                    "href": ("http://mimic.example.com/services/region/"
                             "compute/v2/some_tenant/servers/some_server_id"),
                    "rel": "self"
                },
                {
                    "href": "http://mimic.example.com/services/region/compute/"
                    "some_tenant/servers/some_server_id",
                    "rel": "bookmark"
                }
            ],
            "metadata": {"some_key": "some_value",
                         "some_other_key": "some_other_value"},
            "name": "some_server_name",
            "progress": 100,
            "status": "some_status",
            "tenant_id": "some_tenant",
            "updated": "the_current_time",
            "user_id": "170454"
        }
        self.assertEquals(json.dumps(expectation, indent=2),
                          json.dumps(actual, indent=2))


class NovaAPITests(SynchronousTestCase):

    """
    Tests for the Nova plugin api
    """

    def setUp(self):
        """
        Create a :obj:`MimicCore` with :obj:`NovaApi` as the only plugin,
        and create a server
        """
        self.core = MimicCore(Clock(), [NovaApi()])
        self.root = MimicRoot(self.core).app.resource()
        self.response = request(
            self, self.root, "POST", "/identity/v2.0/tokens",
            json.dumps({
                "auth": {
                    "passwordCredentials": {
                        "username": "test1",
                        "password": "test1password",
                    },
                }
            })
        )
        self.auth_response = self.successResultOf(self.response)
        self.json_body = self.successResultOf(
            treq.json_content(self.auth_response))
        self.uri = self.json_body['access']['serviceCatalog'][0]['endpoints'][0]['publicURL']
        self.server_name = 'test_server'
        self.create_server = request(
            self, self.root, "POST", self.uri + '/servers',
            json.dumps({
                "server": {
                    "name": self.server_name,
                    "imageRef": "test-image",
                    "flavorRef": "test-flavor"
                }
            }))
        self.create_server_response = self.successResultOf(self.create_server)
        self.create_server_response_body = self.successResultOf(
            treq.json_content(self.create_server_response))
        self.server_id = self.create_server_response_body['server']['id']

    def test_create_server(self):
        """
        Test to verify :func:`create_server` on ``POST /v2.0/<tenant_id>/servers``
        """
        self.assertEqual(self.create_server_response.code, 202)
        self.assertTrue(type(self.server_id), unicode)

    def test_list_servers(self):
        """
        Test to verify :func:`list_servers` on ``GET /v2.0/<tenant_id>/servers``
        """
        list_servers = request(self, self.root, "GET", self.uri + '/servers')
        list_servers_response = self.successResultOf(list_servers)
        list_servers_response_body = self.successResultOf(
            treq.json_content(list_servers_response))
        self.assertEqual(list_servers_response.code, 200)
        self.assertEqual(list_servers_response_body['servers'][0]['id'],
                         self.server_id)
        self.assertEqual(len(list_servers_response_body['servers']), 1)

    def test_list_servers_with_args(self):
        """
        Test to verify :func:`list_servers` on ``GET /v2.0/<tenant_id>/servers?name<name>``,
        when a server with that name exists
        """
        list_servers = request(self, self.root, "GET", self.uri + '/servers?name=' + self.server_name)
        list_servers_response = self.successResultOf(list_servers)
        list_servers_response_body = self.successResultOf(
            treq.json_content(list_servers_response))
        self.assertEqual(list_servers_response.code, 200)
        self.assertEqual(list_servers_response_body['servers'][0]['id'],
                         self.server_id)
        self.assertEqual(len(list_servers_response_body['servers']), 1)

    def test_list_servers_with_args_negative(self):
        """
        Test to verify :func:`list_servers` on ``GET /v2.0/<tenant_id>/servers?name<name>``
        when a server with that name does not exist
        """
        list_servers = request(self, self.root, "GET", self.uri + '/servers?name=no_server')
        list_servers_response = self.successResultOf(list_servers)
        list_servers_response_body = self.successResultOf(
            treq.json_content(list_servers_response))
        self.assertEqual(list_servers_response.code, 200)
        self.assertEqual(len(list_servers_response_body['servers']), 0)

    def test_get_server(self):
        """
        Test to verify :func:`get_server` on ``GET /v2.0/<tenant_id>/servers/<server_id>``,
        when the server_id exists
        """
        get_server = request(self, self.root, "GET", self.uri + '/servers/' + self.server_id)
        get_server_response = self.successResultOf(get_server)
        get_server_response_body = self.successResultOf(
            treq.json_content(get_server_response))
        self.assertEqual(get_server_response.code, 200)
        self.assertEqual(get_server_response_body['server']['id'],
                         self.server_id)
        self.assertEqual(get_server_response_body['server']['status'], 'ACTIVE')

    def test_get_server_negative(self):
        """
        Test to verify :func:`get_server` on ``GET /v2.0/<tenant_id>/servers/<server_id>``,
        when the server_id does not exist
        """
        get_server = request(self, self.root, "GET", self.uri + '/servers/test-server-id')
        get_server_response = self.successResultOf(get_server)
        self.assertEqual(get_server_response.code, 404)

    def test_list_servers_with_details(self):
        """
        Test to verify :func:`list_servers_with_details` on ``GET /v2.0/<tenant_id>/servers/detail``
        """
        list_servers_detail = request(self, self.root, "GET", self.uri + '/servers/detail')
        list_servers_detail_response = self.successResultOf(list_servers_detail)
        list_servers_detail_response_body = self.successResultOf(
            treq.json_content(list_servers_detail_response))
        self.assertEqual(list_servers_detail_response.code, 200)
        self.assertEqual(list_servers_detail_response_body['servers'][0]['id'],
                         self.server_id)
        self.assertEqual(len(list_servers_detail_response_body['servers']), 1)
        self.assertEqual(list_servers_detail_response_body['servers'][0]['status'], 'ACTIVE')

    def test_list_servers_with_details_with_args(self):
        """
        :func:`list_servers_with_details`, used by
        ``GET /v2.0/<tenant_id>/servers/detail``, returns the server details
        for only the servers of a given name
        """
        request(
            self, self.root, "POST", self.uri + '/servers',
            json.dumps({
                "server": {
                    "name": 'non-matching-name',
                    "imageRef": "test-image",
                    "flavorRef": "test-flavor"
                }
            }))

        response, body = self.successResultOf(json_request(
            self, self.root, "GET",
            "{0}/servers/detail?name={1}".format(self.uri, self.server_name)))
        self.assertEqual(response.code, 200)
        self.assertEqual(body['servers'][0]['id'], self.server_id)
        self.assertEqual(len(body['servers']), 1)
        self.assertEqual(body['servers'][0]['status'], 'ACTIVE')

    def test_list_servers_with_details_with_args_negative(self):
        """
        :func:`list_servers_with_details`, used by
        ``GET /v2.0/<tenant_id>/servers/detail``, returns no servers when
        there aren't any that match the given name
        """
        response, body = self.successResultOf(json_request(
            self, self.root, "GET",
            '{0}/servers/detail?name=no_server'.format(self.uri)))
        self.assertEqual(response.code, 200)
        self.assertEqual(len(body['servers']), 0)

    def test_delete_server(self):
        """
        Test to verify :func:`delete_server` on ``DELETE /v2.0/<tenant_id>/servers/<server_id>``
        """
        delete_server = request(self, self.root, "DELETE", self.uri + '/servers/' + self.server_id)
        delete_server_response = self.successResultOf(delete_server)
        self.assertEqual(delete_server_response.code, 204)
        self.assertEqual(self.successResultOf(treq.content(delete_server_response)),
                         b"")

    def test_delete_server_negative(self):
        """
        Test to verify :func:`delete_server` on ``DELETE /v2.0/<tenant_id>/servers/<server_id>``,
        when the server_id does not exist
        """
        delete_server = request(self, self.root, "DELETE", self.uri + '/servers/test-server-id')
        delete_server_response = self.successResultOf(delete_server)
        self.assertEqual(delete_server_response.code, 404)

    def test_get_server_image(self):
        """
        Test to verify :func:`get_image` on ``GET /v2.0/<tenant_id>/images/<image_id>``
        """
        get_server_image = request(self, self.root, "GET", self.uri + '/images/test-image-id')
        get_server_image_response = self.successResultOf(get_server_image)
        get_server_image_response_body = self.successResultOf(
            treq.json_content(get_server_image_response))
        self.assertEqual(get_server_image_response.code, 200)
        self.assertEqual(get_server_image_response_body['image']['id'], 'test-image-id')
        self.assertEqual(get_server_image_response_body['image']['status'], 'ACTIVE')

    def test_get_server_flavor(self):
        """
        Test to verify :func:`get_image` on ``GET /v2.0/<tenant_id>/flavors/<flavor_id>``
        """
        get_server_flavor = request(self, self.root, "GET", self.uri + '/flavors/test-flavor-id')
        get_server_flavor_response = self.successResultOf(get_server_flavor)
        get_server_flavor_response_body = self.successResultOf(
            treq.json_content(get_server_flavor_response))
        self.assertEqual(get_server_flavor_response.code, 200)
        self.assertEqual(get_server_flavor_response_body['flavor']['id'], 'test-flavor-id')

    def test_get_server_limits(self):
        """
        Test to verify :func:`get_limit` on ``GET /v2.0/<tenant_id>/limits``
        """
        get_server_limits = request(self, self.root, "GET", self.uri + '/limits')
        get_server_limits_response = self.successResultOf(get_server_limits)
        self.assertEqual(get_server_limits_response.code, 200)
        self.assertTrue(self.successResultOf(treq.json_content(get_server_limits_response)))

    def test_get_server_ips(self):
        """
        Test to verify :func:`get_ips` on ``GET /v2.0/<tenant_id>/servers/<server_id>/ips``
        """
        get_server_ips = request(self, self.root, "GET",
                                 self.uri + '/servers/' + self.server_id + '/ips')
        get_server_ips_response = self.successResultOf(get_server_ips)
        get_server_ips_response_body = self.successResultOf(
            treq.json_content(get_server_ips_response))
        self.assertEqual(get_server_ips_response.code, 200)
        list_servers_detail = request(self, self.root, "GET", self.uri + '/servers/detail')
        list_servers_detail_response = self.successResultOf(list_servers_detail)
        list_servers_detail_response_body = self.successResultOf(
            treq.json_content(list_servers_detail_response))
        self.assertEqual(get_server_ips_response_body['addresses'],
                         list_servers_detail_response_body['servers'][0]['addresses'])

    def test_get_server_ips_negative(self):
        """
        Test to verify :func:`get_ips` on ``GET /v2.0/<tenant_id>/servers/<server_id>/ips``,
        when the server_id does not exist
        """
        get_server_ips = request(self, self.root, "GET",
                                 self.uri + '/servers/non-existant-server/ips')
        get_server_ips_response = self.successResultOf(get_server_ips)
        self.assertEqual(get_server_ips_response.code, 404)
