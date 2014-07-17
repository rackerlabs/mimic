

import itertools
import json
import treq

from twisted.trial.unittest import SynchronousTestCase
from twisted.internet.task import Clock

from mimic.canned_responses.nova import server_template
from mimic.core import MimicCore
from mimic.resource import MimicRoot
from mimic.test.helpers import request
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
        self.uri = (self.json_body['access']['serviceCatalog'][0]['endpoints'][0]['publicURL']
                    + '/servers')
        self.server_name = 'test_server'
        self.create_server = request(
            self, self.root, "POST", self.uri,
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
        list_servers = request(self, self.root, "GET", self.uri)
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
        list_servers = request(self, self.root, "GET", self.uri + '?name=' + self.server_name)
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
        list_servers = request(self, self.root, "GET", self.uri + '?name=' + 'no_server')
        list_servers_response = self.successResultOf(list_servers)
        list_servers_response_body = self.successResultOf(
            treq.json_content(list_servers_response))
        self.assertEqual(list_servers_response.code, 200)
        self.assertEqual(len(list_servers_response_body['servers']), 0)

    def test_get_server(self):
        """
        Test to verify :func:`get_server` on ``GET /v2.0/<tenant_id>/servers/<server_id>``
        """
        get_server = request(self, self.root, "GET", self.uri + '/' + self.server_id)
        get_server_response = self.successResultOf(get_server)
        get_server_response_body = self.successResultOf(
            treq.json_content(get_server_response))
        self.assertEqual(get_server_response.code, 200)
        self.assertEqual(get_server_response_body['server']['id'],
                         self.server_id)
        self.assertEqual(get_server_response_body['server']['status'], 'ACTIVE')

    def test_list_servers_with_details(self):
        """
        Test to verify :func:`list_servers_with_details` on ``GET /v2.0/<tenant_id>/servers/detail``
        """
        list_servers_detail = request(self, self.root, "GET", self.uri + '/detail')
        list_servers_detail_response = self.successResultOf(list_servers_detail)
        list_servers_detail_response_body = self.successResultOf(
            treq.json_content(list_servers_detail_response))
        self.assertEqual(list_servers_detail_response.code, 200)
        self.assertEqual(list_servers_detail_response_body['servers'][0]['id'],
                         self.server_id)
        self.assertEqual(len(list_servers_detail_response_body['servers']), 1)
        self.assertEqual(list_servers_detail_response_body['servers'][0]['status'], 'ACTIVE')

    def test_delete_server(self):
        """
        Test to verify :func:`delete_server` on ``DELETE /v2.0/<tenant_id>/servers/<server_id>``
        """
        delete_server = request(self, self.root, "DELETE", self.uri + '/' + self.server_id)
        delete_server_response = self.successResultOf(delete_server)
        self.assertEqual(delete_server_response.code, 204)
        self.assertEqual(self.successResultOf(treq.content(delete_server_response)),
                         b"")
