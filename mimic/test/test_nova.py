"""
Tests for :mod:`nova_api` and :mod:`nova_objects`.
"""
import json
from urllib import urlencode
from urlparse import parse_qs

from testtools.matchers import (
    ContainsDict, Equals, MatchesDict, MatchesListwise, StartsWith)

import treq

from twisted.trial.unittest import SynchronousTestCase

from mimic.test.helpers import json_request, request, request_with_content, validate_link_json
from mimic.rest.nova_api import NovaApi, NovaControlApi
from mimic.test.behavior_tests import (
    behavior_tests_helper_class,
    register_behavior)
from mimic.test.fixtures import APIMockHelper, TenantAuthentication
from mimic.util.helper import seconds_to_timestamp
from mimic.model.nova_objects import (
    RegionalServerCollection, Server, IPv4Address)


def status_of_server(test_case, server_id):
    """
    Retrieve the status of a server.
    """
    get_server = request(test_case, test_case.root, "GET",
                         test_case.uri + '/servers/' + server_id)
    get_server_response = test_case.successResultOf(get_server)
    get_server_response_body = test_case.successResultOf(
        treq.json_content(get_server_response))
    return get_server_response_body['server']['status']


def create_server(helper, name=None, imageRef=None, flavorRef=None,
                  metadata=None, diskConfig=None, body_override=None,
                  region="ORD", key_name=None, request_func=json_request):
    """
    Create a server with the given body and returns the response object and
    body.

    :param name: Name of the server - defaults to "test_server"
    :param imageRef: Image of the server - defaults to "test-image"
    :param flavorRef: Flavor size of the server - defaults to "test-flavor"
    :param metadata: Metadata of the server - optional
    :param diskConfig: the "OS-DCF:diskConfig" setting for the server -
        optional

    :param str body_override: String containing the server args to
        override the default server body JSON.
    :param str region: The region in which to create the server
    :param callable request_func: What function to use to make the request -
        defaults to json_request (alternately could be request_with_content)

    :return: either the response object, or the response object and JSON
        body if ``json`` is `True`.
    """
    body = body_override
    if body is None:
        data = {
            "name": name if name is not None else 'test_server',
            "key_name": key_name if key_name is not None else 'test_key',
            "imageRef": imageRef if imageRef is not None else "test-image",
            "flavorRef": flavorRef if flavorRef is not None else "test-flavor"
        }
        if metadata is not None:
            data['metadata'] = metadata
        if diskConfig is not None:
            data["OS-DCF:diskConfig"] = diskConfig
        body = json.dumps({"server": data})

    create_server = request_func(
        helper.test_case,
        helper.root,
        "POST",
        '{0}/servers'.format(helper.get_service_endpoint(
            "cloudServersOpenStack", region)),
        body
    )
    return helper.test_case.successResultOf(create_server)


def quick_create_server(helper, **create_server_kwargs):
    """
    Quickly create a server with a bunch of default parameters, retrieving its
    server ID.

    :param name: Optional name of the server

    :return: the server ID of the created server
    """
    resp, body = create_server(helper, request_func=json_request,
                               **create_server_kwargs)
    helper.test_case.assertEqual(resp.code, 202)
    return body["server"]["id"]


def delete_server(helper, server_id):
    """
    Delete server
    """
    d = request_with_content(
        helper.test_case, helper.root, "DELETE",
        '{0}/servers/{1}'.format(helper.uri, server_id))
    resp, body = helper.test_case.successResultOf(d)
    helper.test_case.assertEqual(resp.code, 204)


def update_metdata_item(helper, server_id, key, value):
    """
    Update metadata item
    """
    d = request_with_content(
        helper.test_case, helper.root, "PUT",
        '{0}/servers/{1}/metadata/{2}'.format(helper.uri, server_id, key),
        json.dumps({'meta': {key: value}}))
    resp, body = helper.test_case.successResultOf(d)
    helper.test_case.assertEqual(resp.code, 200)


def update_metdata(helper, server_id, metadata):
    """
    Update metadata
    """
    d = request_with_content(
        helper.test_case, helper.root, "PUT",
        '{0}/servers/{1}/metadata'.format(helper.uri, server_id),
        json.dumps({'metadata': metadata}))
    resp, body = helper.test_case.successResultOf(d)
    helper.test_case.assertEqual(resp.code, 200)


def update_status(helper, control_endpoint, server_id, status):
    """
    Update server status
    """
    d = request_with_content(
        helper.test_case, helper.root, "POST",
        control_endpoint + "/attributes/",
        json.dumps({"status": {server_id: status}}))
    resp, body = helper.test_case.successResultOf(d)
    helper.test_case.assertEqual(resp.code, 201)


def use_creation_behavior(helper, name, parameters, criteria):
    """
    Use the given behavior for server creation.
    """
    return register_behavior(
        helper.test_case, helper.root,
        "{0}/behaviors/creation".format(
            helper.auth.get_service_endpoint("cloudServersBehavior")),
        name, parameters, criteria)


class NovaAPITests(SynchronousTestCase):

    """
    Tests for the Nova Api plugin.
    """

    def setUp(self):
        """
        Create a :obj:`MimicCore` with :obj:`NovaApi` as the only plugin,
        and create a server
        """
        nova_api = NovaApi(["ORD", "MIMIC"])
        self.helper = self.helper = APIMockHelper(
            self, [nova_api, NovaControlApi(nova_api=nova_api)]
        )
        self.root = self.helper.root
        self.clock = self.helper.clock
        self.uri = self.helper.uri
        self.server_name = 'test_server'

        self.create_server_response, self.create_server_response_body = (
            create_server(self.helper, name=self.server_name))
        self.server_id = self.create_server_response_body['server']['id']

    def test_create_server_with_manual_diskConfig(self):
        """
        Servers should respect the provided OS-DCF:diskConfig setting if
        supplied.
        """
        create_server_response, response_body = create_server(
            self.helper, name=self.server_name + "A", diskConfig="MANUAL")
        self.assertEqual(
            response_body['server']['OS-DCF:diskConfig'], 'MANUAL')

        # Make sure we report on proper state.
        server_id = response_body['server']['id']
        get_server = request(
            self, self.root, "GET", self.uri + '/servers/' + server_id
        )
        get_server_response = self.successResultOf(get_server)
        response_body = self.successResultOf(
            treq.json_content(get_server_response))
        self.assertEqual(
            response_body['server']['OS-DCF:diskConfig'], 'MANUAL')

    def test_create_server_with_bad_diskConfig(self):
        """
        When ``create_server`` is passed an invalid ``OS-DCF:diskImage``
        (e.g., one which is neither AUTO nor MANUAL), it should return an HTTP
        status code of 400.
        """
        create_server_response, _ = create_server(
            self.helper, name=self.server_name + "A",
            diskConfig="AUTO-MANUAL")
        self.assertEqual(create_server_response.code, 400)

    def validate_server_detail_json(self, server_json):
        """
        Tests to validate the server JSON.
        """
        validate_link_json(self, server_json)
        # id and links has already been checked, there are others that are not
        # yet implemented in mimic/optional
        response_keys = ("accessIPv4", "accessIPv6", "addresses", "created",
                         "flavor", "image", "metadata", "name", "status",
                         "tenant_id", "updated", "OS-EXT-STS:task_state",
                         "OS-DCF:diskConfig")
        for key in response_keys:
            self.assertIn(key, server_json)

        validate_link_json(self, server_json['image'])
        validate_link_json(self, server_json['flavor'])

        self.assertIsInstance(server_json['addresses'], dict)
        for addresses in server_json['addresses'].values():
            self.assertIsInstance(addresses, list)
            for address in addresses:
                self.assertIn('addr', address)
                self.assertIn('version', address)
                self.assertIn(address['version'], (4, 6),
                              "Address version must be 4 or 6: {0}"
                              .format(address))

    def test_create_server(self):
        """
        Test to verify :func:`create_server` on ``POST /v2.0/<tenant_id>/servers``
        """
        self.assertEqual(self.create_server_response.code, 202)
        self.assertTrue(type(self.server_id), unicode)
        self.assertNotEqual(
            self.create_server_response_body['server']['adminPass'],
            "testpassword"
        )
        validate_link_json(self, self.create_server_response_body['server'])

    def test_create_server_with_keypair_name(self):
        """
        Test to verify creating a server with a named keypair works
        """
        keypair_name = "server_keypair"
        resp, body = create_server(self.helper, key_name=keypair_name)
        self.assertEqual(resp.code, 202)
        server_id = body['server']['id']
        get_server = request(
            self, self.root, "GET", self.uri + '/servers/' + server_id
        )
        get_server_response = self.successResultOf(get_server)
        response_body = self.successResultOf(
            treq.json_content(get_server_response))
        self.assertEqual(
            response_body['server']['key_name'], keypair_name)

    def test_create_server_without_keypair_name(self):
        """
        Test to verify creating a server without a named keypair returns None
        """
        data = {
            "name": "fake_server",
            "imageRef": "test-image",
            "flavorRef": "test-flavor"
        }
        body = json.dumps({"server": data})
        create_resp, create_body = create_server(self.helper, body_override=body)
        server_id = create_body['server']['id']
        get_server = request(
            self, self.root, "GET", self.uri + '/servers/' + server_id
        )
        get_server_response = self.successResultOf(get_server)
        response_body = self.successResultOf(
            treq.json_content(get_server_response))
        self.assertEqual(
            response_body['server']['key_name'], None)

    def test_created_servers_have_dissimilar_admin_passwords(self):
        """
        Two (or more) servers created should not share passwords.
        """
        other_response, other_response_body = create_server(
            self.helper, name=self.server_name)
        self.assertNotEqual(
            self.create_server_response_body['server']['adminPass'],
            other_response_body['server']['adminPass']
        )

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
        validate_link_json(self, list_servers_response_body['servers'][0])

    def test_list_servers_with_args(self):
        """
        Test to verify :func:`list_servers` on ``GET /v2.0/<tenant_id>/servers?name<name>``,
        when a server with that name exists
        """
        list_servers = request(
            self, self.root, "GET", self.uri + '/servers?name=' + self.server_name)
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
        list_servers = request(
            self, self.root, "GET", self.uri + '/servers?name=no_server')
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
        get_server = request(
            self, self.root, "GET", self.uri + '/servers/' + self.server_id)
        get_server_response = self.successResultOf(get_server)
        get_server_response_body = self.successResultOf(
            treq.json_content(get_server_response))
        self.assertEqual(get_server_response.code, 200)
        self.assertEqual(get_server_response_body['server']['id'],
                         self.server_id)
        self.assertEqual(
            get_server_response_body['server']['status'], 'ACTIVE')
        admin_password = get_server_response_body['server'].get('adminPass', None)
        self.assertEqual(admin_password, None)
        self.validate_server_detail_json(get_server_response_body['server'])

    def test_get_server_negative(self):
        """
        Test to verify :func:`get_server` on ``GET /v2.0/<tenant_id>/servers/<server_id>``,
        when the server_id does not exist
        """
        response, body = self.successResultOf(json_request(
            self, self.root, "GET", self.uri + '/servers/test-server-id'))
        self.assertEqual(response.code, 404)
        self.assertEqual(body, {
            "itemNotFound": {
                "message": "Instance could not be found",
                "code": 404
            }
        })

    def test_list_servers_with_details(self):
        """
        Test to verify :func:`list_servers_with_details` on ``GET /v2.0/<tenant_id>/servers/detail``
        """
        list_servers_detail = request(
            self, self.root, "GET", self.uri + '/servers/detail')
        list_servers_detail_response = self.successResultOf(
            list_servers_detail)
        list_servers_detail_response_body = self.successResultOf(
            treq.json_content(list_servers_detail_response))
        self.assertEqual(list_servers_detail_response.code, 200)
        self.assertEqual(list_servers_detail_response_body['servers'][0]['id'],
                         self.server_id)
        self.assertEqual(len(list_servers_detail_response_body['servers']), 1)
        self.assertEqual(
            list_servers_detail_response_body['servers'][0]['status'], 'ACTIVE')

        self.validate_server_detail_json(
            list_servers_detail_response_body['servers'][0])

    def test_list_servers_with_details_with_args(self):
        """
        :func:`list_servers_with_details`, used by
        ``GET /v2.0/<tenant_id>/servers/detail``, returns the server details
        for only the servers of a given name
        """
        create_server(self.helper, name="non-matching-name")
        response, body = self.successResultOf(json_request(
            self, self.root, "GET",
            "{0}/servers/detail?name={1}".format(self.uri, self.server_name)))
        self.assertEqual(response.code, 200)
        self.assertIsNot(body['servers'], None)
        self.assertIsNot(body['servers'][0], None)
        self.assertEqual(body['servers'][0]['id'], self.server_id)
        self.assertEqual(len(body['servers']), 1)
        self.assertEqual(body['servers'][0]['status'], 'ACTIVE')
        self.validate_server_detail_json(body['servers'][0])

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
        delete_server = request(
            self, self.root, "DELETE", self.uri + '/servers/' + self.server_id)
        delete_server_response = self.successResultOf(delete_server)
        self.assertEqual(delete_server_response.code, 204)
        self.assertEqual(self.successResultOf(treq.content(delete_server_response)),
                         b"")
        # Get and see if server actually got deleted
        get_server = request(
            self, self.root, "GET", self.uri + '/servers/' + self.server_id)
        get_server_response = self.successResultOf(get_server)
        self.assertEqual(get_server_response.code, 404)

    def test_delete_server_negative(self):
        """
        Test to verify :func:`delete_server` on ``DELETE /v2.0/<tenant_id>/servers/<server_id>``,
        when the server_id does not exist
        """
        delete_server = request(
            self, self.root, "DELETE", self.uri + '/servers/test-server-id')
        delete_server_response = self.successResultOf(delete_server)
        self.assertEqual(delete_server_response.code, 404)

    def test_get_server_limits(self):
        """
        Test to verify :func:`get_limit` on ``GET /v2.0/<tenant_id>/limits``
        """
        get_server_limits = request(
            self, self.root, "GET", self.uri + '/limits')
        get_server_limits_response = self.successResultOf(get_server_limits)
        self.assertEqual(get_server_limits_response.code, 200)
        self.assertTrue(
            self.successResultOf(treq.json_content(get_server_limits_response)))

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
        list_servers_detail = request(
            self, self.root, "GET", self.uri + '/servers/detail')
        list_servers_detail_response = self.successResultOf(
            list_servers_detail)
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

    def test_different_region_same_server(self):
        """
        Creating a server in one nova region should not create it in other nova
        regions.
        """
        # NB: the setUp creates a server in ORD.
        service_uri = self.helper.get_service_endpoint("cloudServersOpenStack",
                                                       "MIMIC")
        other_region_servers = self.successResultOf(
            treq.json_content(
                self.successResultOf(request(self, self.root, "GET",
                                             service_uri + "/servers/")))
        )["servers"]
        self.assertEqual(other_region_servers, [])

    def test_different_tenants_same_region(self):
        """
        Creating a server for one tenant in a particular region should not
        create it for other tenants in the same region.
        """
        other_tenant = TenantAuthentication(self, self.root, "other", "other")
        service_endpoint = other_tenant.get_service_endpoint(
            "cloudServersOpenStack", "ORD")

        response, response_body = self.successResultOf(
            json_request(
                self, self.root, "GET",
                service_endpoint + '/servers'))

        self.assertEqual(response.code, 200)
        self.assertEqual(response_body, {'servers': []})

    def test_modify_existing_server_status(self):
        """
        An HTTP ``POST`` to ``.../<control-endpoint>/attributes/`` with a JSON
        mapping of attribute type to the server ID and its given server's
        status will change that server's status.
        """
        nova_control_endpoint = self.helper.auth.get_service_endpoint(
            "cloudServersBehavior", "ORD")
        server_id = self.create_server_response_body["server"]["id"]
        status_modification = {
            "status": {server_id: "ERROR"}
        }
        status = status_of_server(self, server_id)
        self.assertEqual(status, "ACTIVE")
        set_status = request(
            self, self.root, "POST",
            nova_control_endpoint + "/attributes/",
            json.dumps(status_modification)
        )
        set_status_response = self.successResultOf(set_status)
        self.assertEqual(set_status_response.code, 201)
        status = status_of_server(self, server_id)
        self.assertEqual(status, "ERROR")

    def test_modify_multiple_server_status(self):
        """
        An HTTP ``POST`` to ``.../<control-endpoint>/attributes/`` with a JSON
        mapping of attribute type to several server IDs and each given server's
        status will change each server's status.
        """
        nova_control_endpoint = self.helper.auth.get_service_endpoint(
            "cloudServersBehavior", "ORD")
        second_server_id = quick_create_server(self.helper, region="ORD")
        server_id = self.create_server_response_body["server"]["id"]
        status_modification = {
            "status": {server_id: "ERROR",
                       second_server_id: "BUILD"}
        }
        status = status_of_server(self, server_id)
        second_status = status_of_server(self, second_server_id)
        self.assertEqual(status, "ACTIVE")
        self.assertEqual(second_status, "ACTIVE")
        set_status = request(
            self, self.root, "POST",
            nova_control_endpoint + "/attributes/",
            json.dumps(status_modification)
        )
        set_status_response = self.successResultOf(set_status)
        self.assertEqual(set_status_response.code, 201)
        status = status_of_server(self, server_id)
        second_status = status_of_server(self, second_server_id)
        self.assertEqual(status, "ERROR")
        self.assertEqual(second_status, "BUILD")

    def test_server_resize(self):
        """
        Resizing a server that does not exist should respond with a 404 and
        resizing a server that does exist should respond with a 202 and the server
        should have an updated flavor
        http://docs.rackspace.com/servers/api/v2/cs-devguide/cs-devguide-20150727.pdf
        """
        resize_request = json.dumps({"resize": {"flavorRef": "2"}})
        response, body = self.successResultOf(json_request(
            self, self.root, "POST", self.uri + '/servers/nothing/action', resize_request))
        self.assertEqual(response.code, 404)
        self.assertEqual(body, {
            "itemNotFound": {
                "message": "Instance nothing could not be found",
                "code": 404
            }
        })

        existing_server = request(
            self, self.root, "POST",
            self.uri + '/servers/' + self.server_id + '/action', resize_request)
        existing_server_response = self.successResultOf(existing_server)
        self.assertEqual(existing_server_response.code, 202)

        get_resized_server = request(
            self, self.root, "GET", self.uri + '/servers/' + self.server_id)
        get_server_response = self.successResultOf(get_resized_server)
        get_server_response_body = self.successResultOf(
            treq.json_content(get_server_response))
        self.assertEqual(get_server_response_body['server']['flavor']['id'], '2')

        no_resize_request = json.dumps({"non_supported_action": {"flavorRef": "2"}})
        response, body = self.successResultOf(json_request(
            self, self.root, "POST",
            self.uri + '/servers/' + self.server_id + '/action', no_resize_request))
        self.assertEqual(response.code, 400)
        self.assertEqual(body, {
            "badRequest": {
                "message": "There is no such action currently supported",
                "code": 400
            }
        })

        no_flavorref_request = json.dumps({"resize": {"missingflavorRef": "5"}})
        response, body = self.successResultOf(json_request(
            self, self.root, "POST",
            self.uri + '/servers/' + self.server_id + '/action', no_flavorref_request))
        self.assertEqual(response.code, 400)
        self.assertEqual(body, {
            "badRequest": {
                "message": "Resize requests require 'flavorRef' attribute",
                "code": 400
            }
        })

    def test_confirm_and_revert_server_resize(self):
        """
        After a server finishes resizing, the size must be confirmed or reverted
        A confirmation action should make the server ACTIVE and return a 204
        A revert action should change the flavor and return a 202
        Attempting to revert or confirm that is not in VERIFY_RESIZE state returns a 409
        http://docs.rackspace.com/servers/api/v2/cs-devguide/cs-devguide-20150727.pdf
        """
        confirm_request = json.dumps({"confirmResize": "null"})
        revert_request = json.dumps({"revertResize": "null"})
        resize_request = json.dumps({"resize": {"flavorRef": "2"}})

        response, body = self.successResultOf(json_request(
            self, self.root, "POST",
            self.uri + '/servers/' + self.server_id + '/action', confirm_request))
        self.assertEqual(response.code, 409)
        self.assertEqual(body, {
            "conflictingRequest": {
                "message": "Cannot 'confirmResize' instance " + self.server_id +
                           " while it is in vm_state active",
                "code": 409
            }
        })

        response, body = self.successResultOf(json_request(
            self, self.root, "POST",
            self.uri + '/servers/' + self.server_id + '/action', revert_request))
        self.assertEqual(response.code, 409)
        self.assertEqual(body, {
            "conflictingRequest": {
                "message": "Cannot 'revertResize' instance " + self.server_id +
                           " while it is in vm_state active",
                "code": 409
            }
        })

        request(self, self.root, "POST",
                self.uri + '/servers/' + self.server_id + '/action', resize_request)
        confirm = request(
            self, self.root, "POST",
            self.uri + '/servers/' + self.server_id + '/action', confirm_request)
        confirm_response = self.successResultOf(confirm)
        self.assertEqual(confirm_response.code, 204)

        resize_request = json.dumps({"resize": {"flavorRef": "10"}})

        request(self, self.root, "POST",
                self.uri + '/servers/' + self.server_id + '/action', resize_request)

        resized_server = request(
            self, self.root, "GET", self.uri + '/servers/' + self.server_id)
        resized_server_response = self.successResultOf(resized_server)
        resized_server_response_body = self.successResultOf(
            treq.json_content(resized_server_response))
        self.assertEqual(resized_server_response_body['server']['flavor']['id'], '10')

        revert = request(
            self, self.root, "POST",
            self.uri + '/servers/' + self.server_id + '/action', revert_request)
        revert_response = self.successResultOf(revert)
        self.assertEqual(revert_response.code, 202)

        reverted_server = request(
            self, self.root, "GET", self.uri + '/servers/' + self.server_id)
        reverted_server_response = self.successResultOf(reverted_server)
        reverted_server_response_body = self.successResultOf(
            treq.json_content(reverted_server_response))
        self.assertEqual(reverted_server_response_body['server']['flavor']['id'], '2')

    def test_rescue(self):
        """
        Attempting to rescue a server that is not in ACTIVE state
            returns conflictingRequest with response code 409.
        If the server is in ACTIVE state, then a new password is returned
            for the server with a response code of 200.
        http://docs.rackspace.com/servers/api/v2/cs-devguide/content/rescue_mode.html
        """
        metadata = {"server_error": "1"}
        server_id = quick_create_server(self.helper, metadata=metadata)

        rescue_request = json.dumps({"rescue": "none"})

        response, body = self.successResultOf(json_request(
            self, self.root, "POST",
            self.uri + '/servers/' + server_id + '/action', rescue_request))
        self.assertEqual(response.code, 409)
        self.assertEqual(body, {
            "conflictingRequest": {
                "message": "Cannot 'rescue' instance " + server_id +
                           " while it is in task state other than active",
                "code": 409
            }
        })

        rescue = request(
            self, self.root, "POST",
            self.uri + '/servers/' + self.server_id + '/action', rescue_request)
        rescue_response = self.successResultOf(rescue)
        rescue_response_body = self.successResultOf(treq.json_content(rescue_response))
        self.assertEqual(rescue_response.code, 200)
        self.assertTrue('"adminPass":' in json.dumps(rescue_response_body))

    def test_unrescue(self):
        """
        Attempting to unrescue a server that is not in RESCUE state a response body
            of conflicting request and response code of 409
        Unsrescuing a server that is in ACTIVE state, returns a 200.
        http://docs.rackspace.com/servers/api/v2/cs-devguide/content/exit_rescue_mode.html
        """
        rescue_request = json.dumps({"rescue": "none"})
        unrescue_request = json.dumps({"unrescue": "null"})
        response, body = self.successResultOf(json_request(
            self, self.root, "POST",
            self.uri + '/servers/' + self.server_id + '/action', unrescue_request))
        self.assertEqual(response.code, 409)
        self.assertEqual(body, {
            "conflictingRequest": {
                "message": "Cannot 'unrescue' instance " + self.server_id +
                           " while it is in task state other than rescue",
                "code": 409
            }
        })
        # Put a server in rescue status
        request(
            self, self.root, "POST",
            self.uri + '/servers/' + self.server_id + '/action', rescue_request)

        unrescue = request(self, self.root, "POST",
                           self.uri + '/servers/' + self.server_id + '/action', unrescue_request)
        unrescue_response = self.successResultOf(unrescue)
        self.assertEqual(unrescue_response.code, 200)

    def test_reboot_server(self):
        """
        A hard reboot of a server sets the server status to HARD_REBOOT and returns a 202
        A soft reboot of a server sets the server status to REBOOT and returns a 202
        After some amount of time the server will go back to ACTIVE state
        The clock is being used to advance time and verify that status changes from the
            a reboot state to active.  The current time interval being used in hardcoded
            in the route for now. In the future we need to refactor to allow different
            durations to be set including a zero duration which would allow the server to
            skip the intermediary state of HARD_REBOOT or REBOOT and go straight to ACTIVE
        If the 'type' attribute is left out of the request, a response body is returned
            with code of 400
        http://docs.rackspace.com/servers/api/v2/cs-devguide/content/Reboot_Server-d1e3371.html
        """
        no_reboot_type_request = json.dumps({"reboot": {"missing_type": "SOFT"}})
        response, body = self.successResultOf(json_request(
            self, self.root, "POST",
            self.uri + '/servers/' + self.server_id + '/action', no_reboot_type_request))
        self.assertEqual(response.code, 400)
        self.assertEqual(body, {
            "badRequest": {
                "message": "Missing argument 'type' for reboot",
                "code": 400
            }
        })

        wrong_reboot_type_request = json.dumps({"reboot": {"type": "FIRM"}})
        response, body = self.successResultOf(json_request(
            self, self.root, "POST",
            self.uri + '/servers/' + self.server_id + '/action', wrong_reboot_type_request))
        self.assertEqual(response.code, 400)
        self.assertEqual(body, {
            "badRequest": {
                "message": "Argument 'type' for reboot is not HARD or SOFT",
                "code": 400
            }
        })

        # Soft reboot tests
        soft_reboot_request = json.dumps({"reboot": {"type": "SOFT"}})
        soft_reboot = request(
            self, self.root, "POST",
            self.uri + '/servers/' + self.server_id + '/action', soft_reboot_request)

        soft_reboot_response = self.successResultOf(soft_reboot)
        self.assertEqual(soft_reboot_response.code, 202)

        response, body = self.successResultOf(json_request(
            self, self.root, "GET", self.uri + '/servers/' + self.server_id))
        self.assertEqual(body['server']['status'], 'REBOOT')

        # Advance the clock 3 seconds and check status
        self.clock.advance(3)
        rebooted_server = request(
            self, self.root, "GET", self.uri + '/servers/' + self.server_id)
        rebooted_server_response = self.successResultOf(rebooted_server)
        rebooted_server_response_body = self.successResultOf(
            treq.json_content(rebooted_server_response))
        self.assertEqual(rebooted_server_response_body['server']['status'], 'ACTIVE')

        # Hard Reboot Tests
        hard_reboot_request = json.dumps({"reboot": {"type": "HARD"}})
        hard_reboot = request(
            self, self.root, "POST",
            self.uri + '/servers/' + self.server_id + '/action', hard_reboot_request)
        hard_reboot_response = self.successResultOf(hard_reboot)
        self.assertEqual(hard_reboot_response.code, 202)

        hard_reboot_server = request(
            self, self.root, "GET", self.uri + '/servers/' + self.server_id)
        hard_reboot_server_response = self.successResultOf(hard_reboot_server)
        hard_reboot_server_response_body = self.successResultOf(
            treq.json_content(hard_reboot_server_response))
        self.assertEqual(hard_reboot_server_response_body['server']['status'], 'HARD_REBOOT')

        # Advance clock 6 seconds and check server status
        self.clock.advance(6)
        rebooted_server = request(
            self, self.root, "GET", self.uri + '/servers/' + self.server_id)
        rebooted_server_response = self.successResultOf(rebooted_server)
        rebooted_server_response_body = self.successResultOf(
            treq.json_content(rebooted_server_response))
        self.assertEqual(rebooted_server_response_body['server']['status'], 'ACTIVE')

    def test_change_password(self):
        """
        Resetting the password on a non ACTIVE server responds with a
            conflictingRequest and response code 409
        adminPass is required as part of the request body, if missing a badRequest
            is returned with response code 400
        A successful password reset returns 202
        http://docs.rackspace.com/servers/api/v2/cs-devguide/content/Change_Password-d1e3234.html
        """
        password_request = json.dumps({"changePassword": {"adminPass": "password"}})
        bad_password_request = json.dumps({"changePassword": {"Pass": "password"}})
        response, body = self.successResultOf(json_request(
            self, self.root, "POST",
            self.uri + '/servers/' + self.server_id + '/action', bad_password_request))
        self.assertEqual(response.code, 400)
        self.assertEqual(body, {
            "badRequest": {
                "message": "No adminPass was specified",
                "code": 400
            }
        })
        password_reset = request(
            self, self.root, "POST",
            self.uri + '/servers/' + self.server_id + '/action', password_request)
        password_reset_response = self.successResultOf(password_reset)
        self.assertEqual(password_reset_response.code, 202)

        # Create server in error state and test response when changing password
        # in state other than ACTIVE
        metadata = {"server_error": "1"}
        server_id = quick_create_server(self.helper, metadata=metadata)
        response, body = self.successResultOf(json_request(
            self, self.root, "POST",
            self.uri + '/servers/' + server_id + '/action', password_request))
        self.assertEqual(response.code, 409)
        self.assertEqual(body, {
            "conflictingRequest": {
                "message": "Cannot 'changePassword' instance " + server_id +
                           " while it is in task state other than active",
                "code": 409
            }
        })

    def test_rebuild(self):
        rebuild_request = json.dumps({"rebuild": {"imageRef": "d5f916f8-03a4-4392-9ec2-cc6e5ad41cf0"}})
        no_imageRef_request = json.dumps({"rebuild": {"name": "new_server"}})

        response, body = self.successResultOf(json_request(
            self, self.root, "POST",
            self.uri + '/servers/' + self.server_id + '/action', no_imageRef_request))
        self.assertEqual(response.code, 400)
        self.assertEqual(body, {
            "badRequest": {
                "message": "Could not parse imageRef from request.",
                "code": 400
            }
        })

        response, body = self.successResultOf(json_request(
            self, self.root, "POST",
            self.uri + '/servers/' + self.server_id + '/action', rebuild_request))
        self.assertEqual(response.code, 202)
        self.assertTrue('adminPass' in json.dumps(body))
        self.assertEqual(body['server']['id'], self.server_id)
        self.assertEqual(body['server']['status'], 'REBUILD')

        self.clock.advance(5)
        rebuilt_server = request(
            self, self.root, "GET", self.uri + '/servers/' + self.server_id)
        rebuilt_server_response = self.successResultOf(rebuilt_server)
        rebuilt_server_response_body = self.successResultOf(
            treq.json_content(rebuilt_server_response))
        self.assertEqual(rebuilt_server_response_body['server']['status'], 'ACTIVE')

        # Create server in error state and test response when an attempt to
        # rebuild the server when it is in state other than ACTIVE
        metadata = {"server_error": "1"}
        server_id = quick_create_server(self.helper, metadata=metadata)
        response, body = self.successResultOf(json_request(
            self, self.root, "POST",
            self.uri + '/servers/' + server_id + '/action', rebuild_request))
        self.assertEqual(response.code, 409)
        self.assertEqual(body, {
            "conflictingRequest": {
                "message": "Cannot 'rebuild' instance " + server_id +
                           " while it is in task state other than active",
                "code": 409
            }
        })


class NovaAPIChangesSinceTests(SynchronousTestCase):
    """
    Tests for listing servers with changes-since filter
    """

    def setUp(self):
        """
        Create a :obj:`MimicCore` with :obj:`NovaApi` as the only plugin,
        and create a server
        """
        nova_api = NovaApi(["ORD", "MIMIC"])
        helper = self.helper = APIMockHelper(
            self, [nova_api, NovaControlApi(nova_api=nova_api)]
        )
        self.root = helper.root
        self.uri = helper.uri
        self.clock = helper.clock
        self.control_endpoint = helper.auth.get_service_endpoint(
            "cloudServersBehavior",
            "ORD")
        self.server1 = quick_create_server(helper)
        self.clock.advance(1)
        self.server2 = quick_create_server(helper)

    def list_servers_detail(self, since):
        changes_since = seconds_to_timestamp(since)
        params = urlencode({"changes-since": changes_since})
        resp, body = self.successResultOf(
            json_request(
                self, self.root, "GET",
                '{0}/servers/detail?{1}'.format(self.uri, params)))
        self.assertEqual(resp.code, 200)
        return body['servers']

    def list_servers(self, since):
        servers = self.list_servers_detail(since)
        return [s['id'] for s in servers]

    def test_no_changes(self):
        """
        Returns no servers if nothing has changed since time given
        """
        self.clock.advance(3)
        self.assertEqual(self.list_servers(2), [])

    def test_returns_created_servers(self):
        """
        Returns servers created after given time
        """
        self.assertEqual(self.list_servers(0.5), [self.server2])
        self.assertEqual(self.list_servers(1.0), [self.server2])

    def test_returns_deleted_servers(self):
        """
        Returns DELETED servers if they've been deleted since the time given
        """
        self.clock.advance(1)
        delete_server(self.helper, self.server1)
        self.clock.advance(2)
        matcher = MatchesListwise(
            [ContainsDict({"status": Equals(u"DELETED"), "id": Equals(self.server1)})])
        mismatch = matcher.match(self.list_servers_detail(1.5))
        self.assertIs(mismatch, None)

    def test_returns_updated_status_servers(self):
        """
        Returns servers whose status has been updated since given time
        """
        self.clock.advance(1)
        update_status(self.helper, self.control_endpoint, self.server2, u"ERROR")
        self.assertEqual(self.list_servers(1.5), [self.server2])

    def test_returns_updated_metadata_servers(self):
        """
        Returns servers whose metadata has changes since given time
        """
        self.clock.advance(1)
        update_metdata_item(self.helper, self.server1, "a", "b")
        self.assertEqual(self.list_servers(1.5), [self.server1])

    def test_returns_replaced_metadata_servers(self):
        """
        Returns servers whose metadata has been replaced since given time
        """
        self.clock.advance(1)
        update_metdata(self.helper, self.server1, {"a": "b"})
        self.assertEqual(self.list_servers(1.5), [self.server1])


class NovaAPIListServerPaginationTests(SynchronousTestCase):
    """
    Tests for the Nova plugin API for paginating while listing servers,
    both with and without details.
    """
    def make_nova_app(self):
        """
        Create a :obj:`MimicCore` with :obj:`NovaApi` as the only plugin,
        and create a server
        """
        self.helper = APIMockHelper(self, [NovaApi(["ORD", "MIMIC"])])
        self.root = self.helper.root
        self.uri = self.helper.uri

    def create_servers(self, n, name_generation=None):
        """
        Create ``n`` servers, returning a list of their server IDs.
        """
        return [
            quick_create_server(
                self.helper,
                name=("{0}".format(i) if name_generation is None
                      else name_generation(i))
            ) for i in range(n)
        ]

    def list_servers(self, path, params=None, code=200):
        """
        List all servers using the given path and parameters.  Return the
        entire response body.
        """
        url = self.uri + path
        if params is not None:
            url = "{0}?{1}".format(url, urlencode(params))

        resp, body = self.successResultOf(
            json_request(self, self.root, "GET", url))

        self.assertEqual(resp.code, code)
        return body

    def match_body_with_links(self, result, expected_servers, expected_path,
                              expected_query_params):
        """
        Given the result from listing servers, matches it against an expected
        value that includes the next page links.
        """
        self.assertEqual(expected_servers, result['servers'])
        expected_matcher = MatchesDict({
            'servers': Equals(expected_servers),
            'servers_links': MatchesListwise([
                MatchesDict({
                    'rel': Equals('next'),
                    'href': StartsWith(
                        "{0}{1}?".format(self.uri, expected_path))
                })
            ])
        })
        mismatch = expected_matcher.match(result)
        if mismatch is not None:
            self.fail(mismatch.describe())

        link = result['servers_links'][0]['href']
        query_string = link.split('?', 1)[-1]
        self.assertEqual(expected_query_params, parse_qs(query_string))

    def test_with_invalid_marker(self):
        """
        If an invalid marker is passed, no matter what other parameters,
        return with a 400 bad request.
        """
        self.make_nova_app()
        self.create_servers(2)
        combos = ({}, {'limit': 1}, {'name': '0'}, {'limit': 1, 'name': '0'})

        for path in ('/servers', '/servers/detail'):
            for combo in combos:
                combo['marker'] = '9000'
                error_body = self.list_servers(path, combo, code=400)
                self.assertEqual(
                    {
                        "badRequest": {
                            "message": "marker [9000] not found",
                            "code": 400
                        }
                    },
                    error_body)

    def _check_invalid_limit(self, limit, message):
        """
        Make a request with an invalid limit against every possible
        combination of parameters, and assert that a 400 bad request is
        returned with the given message.
        """
        self.make_nova_app()
        self.create_servers(2, lambda i: 'server')
        servers = self.list_servers('/servers')['servers']

        combos = ({}, {'marker': servers[0]['id']}, {'name': 'server'},
                      {'marker': servers[0]['id'], 'name': 'server'})

        for path in ('/servers', '/servers/detail'):
            for combo in combos:
                combo['limit'] = limit
                error_body = self.list_servers(path, combo, code=400)
                self.assertEqual(
                    {
                        "badRequest": {
                            "message": message,
                            "code": 400
                        }
                    },
                    error_body)

    def test_with_non_int_limit(self):
        """
        If a limit that can't be converted into an integer is passed, no
        matter what other parameters there are, return with a 400 bad request.
        """
        for non_int in ('a', '0.1', '[]'):
            self._check_invalid_limit(
                non_int, "limit param must be an integer")

    def test_with_negative_limit(self):
        """
        If a negative limit is passed, no matter what other parameters there
        are, return 400 with a bad request.
        """
        self._check_invalid_limit('-1', "limit param must be positive")

    def test_with_limit_as_0(self):
        """
        If a limit of 0 is passed, no matter what other parameters there are,
        return no servers and do not include the next page link.
        """
        self.make_nova_app()
        self.create_servers(2, lambda i: 'server')
        servers = self.list_servers('/servers')['servers']

        combos = ({}, {'marker': servers[0]['id']}, {'name': 'server'},
                      {'marker': servers[0]['id'], 'name': 'server'})

        for path in ('/servers', '/servers/detail'):
            for combo in combos:
                combo['limit'] = 0
                with_params = self.list_servers(path, combo)
                self.assertEqual({'servers': []}, with_params)

    def test_with_valid_marker_only(self):
        """
        If just the marker is passed, and it's a valid marker, list all
        servers after that marker without any kind of limit.
        Do not return a next page link.
        """
        for path in ('/servers', '/servers/detail'):
            self.make_nova_app()
            self.create_servers(5)
            servers = self.list_servers(path)['servers']

            with_params = self.list_servers(path, {'marker': servers[0]['id']})
            self.assertEqual({'servers': servers[1:]}, with_params)

    def test_with_marker_and_name(self):
        """
        If just the marker and name are passed, list all servers after that
        marker that have that particular name.  There is no number of servers
        limit. Do not return a next page link.
        """
        for path in ('/servers', '/servers/detail'):
            self.make_nova_app()
            self.create_servers(5, lambda i: "{0}".format(0 if i == 1 else 1))
            servers = self.list_servers(path)['servers']
            self.assertEqual(['1', '0', '1', '1', '1'],
                             [server['name'] for server in servers],
                             "Assumption about server list ordering is wrong")
            with_params = self.list_servers(
                path, {'marker': servers[0]['id'], 'name': "1"})
            self.assertEqual({'servers': servers[2:]}, with_params)

    def test_with_limit_lt_servers_only(self):
        """
        If just the limit is passed, and the limit is less than the number of
        servers, list only that number of servers in the limit, starting with
        the first server in the list.  Include the next page link.
        """
        for path in ('/servers', '/servers/detail'):
            self.make_nova_app()
            self.create_servers(2)
            servers = self.list_servers(path)['servers']
            with_params = self.list_servers(path, {'limit': 1})
            self.match_body_with_links(
                with_params,
                expected_servers=[servers[0]],
                expected_path=path,
                expected_query_params={
                    'limit': ['1'], 'marker': [servers[0]['id']]
                }
            )

    def test_with_limit_eq_servers_only(self):
        """
        If just the limit is passed, and the limit is equal to the number
        of servers, list all the servers starting with the first server in
        the list.  Include the next page link.
        """
        for path in ('/servers', '/servers/detail'):
            self.make_nova_app()
            self.create_servers(2)
            servers = self.list_servers(path)['servers']
            with_params = self.list_servers(path, {'limit': 2})
            self.match_body_with_links(
                with_params,
                expected_servers=servers,
                expected_path=path,
                expected_query_params={
                    'limit': ['2'], 'marker': [servers[1]['id']]
                }
            )

    def test_with_limit_gt_servers_only(self):
        """
        If just the limit is passed, and the limit is greater than the number
        of servers, list all the servers starting with the first server in
        the list.  Do not include the next page link.
        """
        for path in ('/servers', '/servers/detail'):
            self.make_nova_app()
            self.create_servers(2)
            servers = self.list_servers(path)['servers']
            with_params = self.list_servers(path, {'limit': 5})
            self.assertEqual({'servers': servers}, with_params)

    def test_with_limit_lt_servers_with_name(self):
        """
        If the limit and name are passed, and the limit is less than the
        number of servers that match that name, list only that number of
        servers with that name in the limit, starting with
        the first server with that name.  Include the next page link.
        """
        for path in ('/servers', '/servers/detail'):
            self.make_nova_app()
            self.create_servers(3, lambda i: "{0}".format(0 if i == 0 else 1))
            servers = self.list_servers(path)['servers']
            self.assertEqual(['0', '1', '1'],
                             [server['name'] for server in servers],
                             "Assumption about server list ordering is wrong")

            with_params = self.list_servers(path, {'limit': 1, 'name': '1'})
            self.match_body_with_links(
                with_params,
                expected_servers=[servers[1]],
                expected_path=path,
                expected_query_params={
                    'limit': ['1'],
                    'marker': [servers[1]['id']],
                    'name': ['1']
                }
            )

    def test_with_limit_eq_servers_with_name(self):
        """
        If the limit and name are passed, and the limit is equal to the
        number of servers that match the name, list all the servers that match
        that name starting with the first server that matches.  Include the
        next page link.
        """
        for path in ('/servers', '/servers/detail'):
            self.make_nova_app()
            self.create_servers(3, lambda i: "{0}".format(0 if i == 0 else 1))
            servers = self.list_servers(path)['servers']
            self.assertEqual(['0', '1', '1'],
                             [server['name'] for server in servers],
                             "Assumption about server list ordering is wrong")
            with_params = self.list_servers(path, {'limit': 2, 'name': '1'})
            self.match_body_with_links(
                with_params,
                expected_servers=servers[1:],
                expected_path=path,
                expected_query_params={
                    'limit': ['2'],
                    'marker': [servers[2]['id']],
                    'name': ['1']
                }
            )

    def test_with_limit_gt_servers_with_name(self):
        """
        If the limit and name are passed, and the limit is greater than the
        number of servers that match the name, list all the servers that match
        that name starting with the first server that matches.  Do not
        include the next page link.
        """
        for path in ('/servers', '/servers/detail'):
            self.make_nova_app()
            self.create_servers(3, lambda i: "{0}".format(0 if i == 0 else 1))
            servers = self.list_servers(path)['servers']
            self.assertEqual(['0', '1', '1'],
                             [server['name'] for server in servers],
                             "Assumption about server list ordering is wrong")
            with_params = self.list_servers(path, {'limit': 5, 'name': '1'})
            self.assertEqual({'servers': servers[1:]}, with_params)

    def test_with_limit_lt_servers_with_marker(self):
        """
        If the limit and marker are passed, and the limit is less than the
        number of servers, list only that number of servers after the one
        with the marker ID.  Include the next page link.
        """
        for path in ('/servers', '/servers/detail'):
            self.make_nova_app()
            self.create_servers(3)
            servers = self.list_servers(path)['servers']
            with_params = self.list_servers(
                path, {'limit': 1, 'marker': servers[0]['id']})
            self.match_body_with_links(
                with_params,
                expected_servers=[servers[1]],
                expected_path=path,
                expected_query_params={
                    'limit': ['1'], 'marker': [servers[1]['id']]
                }
            )

    def test_with_limit_eq_servers_with_marker(self):
        """
        If the limit and marker are passed, and the limit is equal to the
        number of servers, list all the servers after the one with the marker
        ID.  Include the next page link.
        """
        for path in ('/servers', '/servers/detail'):
            self.make_nova_app()
            self.create_servers(3)
            servers = self.list_servers(path)['servers']
            with_params = self.list_servers(
                path, {'limit': 2, 'marker': servers[0]['id']})
            self.match_body_with_links(
                with_params,
                expected_servers=servers[1:],
                expected_path=path,
                expected_query_params={
                    'limit': ['2'], 'marker': [servers[2]['id']]
                }
            )

    def test_with_limit_gt_servers_with_marker(self):
        """
        If the limit and marker are passed, and the limit is greater than the
        number of servers, list all the servers after the one with the marker
        ID.  Do not include the next page link.
        """
        for path in ('/servers', '/servers/detail'):
            self.make_nova_app()
            self.create_servers(3)
            servers = self.list_servers(path)['servers']
            with_params = self.list_servers(
                path, {'limit': 5, 'marker': servers[0]['id']})
            self.assertEqual({'servers': servers[1:]}, with_params)

    def test_with_limit_lt_servers_with_marker_and_name(self):
        """
        If the limit, marker, and name are passed, and the limit is less than
        the number of servers that match that name, list only that number of
        servers with that name in the limit, after the one with the marker ID.

        The marker ID does not even have to belong to a server that matches
        the given name.

        Include the next page link.
        """
        for path in ('/servers', '/servers/detail'):
            self.make_nova_app()
            self.create_servers(6, lambda i: "{0}".format(i % 2))
            servers = self.list_servers(path)['servers']
            self.assertEqual(['0', '1', '0', '1', '0', '1'],
                             [server['name'] for server in servers],
                             "Assumption about server list ordering is wrong")

            with_params = self.list_servers(
                path, {'limit': 1, 'name': '1', 'marker': servers[2]['id']})
            self.match_body_with_links(
                with_params,
                expected_servers=[servers[3]],
                expected_path=path,
                expected_query_params={
                    'limit': ['1'],
                    'marker': [servers[3]['id']],
                    'name': ['1']
                }
            )

    def test_with_limit_eq_servers_with_marker_and_name(self):
        """
        If the limit, marker, and name are passed, and the limit is equal to
        the number of servers that match the name, list all the servers that
        match that name after the one with the marker ID.

        The marker ID does not even have to belong to a server that matches
        the given name.

        Include the next page link.
        """
        for path in ('/servers', '/servers/detail'):
            self.make_nova_app()
            self.create_servers(6, lambda i: "{0}".format(i % 2))
            servers = self.list_servers(path)['servers']
            self.assertEqual(['0', '1', '0', '1', '0', '1'],
                             [server['name'] for server in servers],
                             "Assumption about server list ordering is wrong")

            with_params = self.list_servers(
                path, {'limit': 2, 'name': '1', 'marker': servers[2]['id']})
            self.match_body_with_links(
                with_params,
                expected_servers=[servers[3], servers[5]],
                expected_path=path,
                expected_query_params={
                    'limit': ['2'],
                    'marker': [servers[5]['id']],
                    'name': ['1']
                }
            )

    def test_with_limit_gt_servers_with_marker_and_name(self):
        """
        If the limit, marker, and name are passed, and the limit is greater
        than the number of servers that match the name, list all the servers
        that match that name after the one with the marker ID.

        The marker ID does not even have to belong to a server that matches
        the given name.

        Do not include the next page link.
        """
        for path in ('/servers', '/servers/detail'):
            self.make_nova_app()
            self.create_servers(6, lambda i: "{0}".format(i % 2))
            servers = self.list_servers(path)['servers']
            self.assertEqual(['0', '1', '0', '1', '0', '1'],
                             [server['name'] for server in servers],
                             "Assumption about server list ordering is wrong")

            with_params = self.list_servers(
                path, {'limit': 5, 'name': '1', 'marker': servers[2]['id']})
            self.assertEqual({'servers': [servers[3], servers[5]]},
                             with_params)

    def test_deleted_servers_do_not_affect_pagination_no_changes_since(self):
        """
        If a bunch of servers are deleted, they do not impact pagination if
        changes-since is not passed.
        """
        for path in ('/servers', '/servers/detail'):
            self.make_nova_app()
            server_ids = self.create_servers(5)
            for server_id in server_ids:
                delete_server(self.helper, server_id)

            server_ids = self.create_servers(5)
            servers = self.list_servers(path, {'limit': 5})
            self.assertEqual(set([s['id'] for s in servers['servers']]),
                             set(server_ids))
            self.assertIn('servers_links', servers)


class NovaAPINegativeTests(SynchronousTestCase):
    """
    Tests for the Nova plugin api for error injections
    """

    def setUp(self):
        """
        Create a :obj:`MimicCore` with :obj:`NovaApi` as the only plugin,
        and create a server
        """
        nova_api = NovaApi(["ORD", "MIMIC"])
        nova_control_api = NovaControlApi(nova_api=nova_api)
        self.helper = APIMockHelper(self, [nova_api, nova_control_api])
        self.nova_control_endpoint = self.helper.auth.get_service_endpoint(
            "cloudServersBehavior",
            "ORD")
        self.root = self.helper.root
        self.uri = self.helper.uri
        self.helper = self.helper

    def test_create_server_request_with_no_body_causes_bad_request(self):
        """
        Test to verify :func:`create_server` does not fail when it receives a
        request with no body.
        """
        create_server_response, _ = create_server(
            self.helper, body_override="")
        self.assertEquals(create_server_response.code, 400)

    def test_create_server_request_with_invalid_body_causes_bad_request(self):
        """
        Test to verify :func:`create_server` does not fail when it receives a
        request with no body.
        """
        create_server_response, _ = create_server(
            self.helper, body_override='{ bad request: }')
        self.assertEquals(create_server_response.code, 400)

    def test_create_server_failure(self):
        """
        Test to verify :func:`create_server` fails with given error message
        and response code in the metadata, and the given failure type.
        """
        serverfail = {"message": "Create server failure", "code": 500,
                      "type": "specialType"}
        metadata = {"create_server_failure": json.dumps(serverfail)}
        create_server_response, create_server_response_body = create_server(
            self.helper, metadata=metadata)
        self.assertEquals(create_server_response.code, 500)
        self.assertEquals(
            create_server_response_body['specialType']['message'],
            "Create server failure")
        self.assertEquals(
            create_server_response_body['specialType']['code'], 500)

    def test_create_server_failure_string_type(self):
        """
        Test to verify :func:`create_server` fails with string body
        and response code in the metadata, if the failure type is "string".
        """
        serverfail = {"message": "Create server failure", "code": 500,
                      "type": "string"}
        metadata = {"create_server_failure": json.dumps(serverfail)}
        create_server_response, create_server_response_body = create_server(
            self.helper, metadata=metadata, request_func=request_with_content)
        self.assertEquals(create_server_response.code, 500)
        self.assertEquals(create_server_response_body,
                          "Create server failure")

    def test_create_server_failure_and_list_servers(self):
        """
        Test to verify :func:`create_server` fails with given error message
        and response code in the metadata and does not actually create a server.
        """
        serverfail = {"message": "Create server failure", "code": 500}
        metadata = {"create_server_failure": json.dumps(serverfail)}
        create_server_response, create_server_response_body = create_server(
            self.helper, metadata=metadata)
        self.assertEquals(create_server_response.code, 500)
        self.assertEquals(
            create_server_response_body['computeFault']['message'],
            "Create server failure")
        self.assertEquals(
            create_server_response_body['computeFault']['code'], 500)
        # List servers
        list_servers = request(self, self.root, "GET", self.uri + '/servers')
        list_servers_response = self.successResultOf(list_servers)
        self.assertEquals(list_servers_response.code, 200)
        list_servers_response_body = self.successResultOf(
            treq.json_content(list_servers_response))
        self.assertEquals(list_servers_response_body['servers'], [])

    def test_server_in_building_state_for_specified_time(self):
        """
        Test to verify :func:`create_server` creates a server in BUILD
        status for the time specified in the metadata.
        """
        self.do_timing_test(metadata={"server_building": "1"},
                            before=u"BUILD",
                            delay=2.0,
                            after=u"ACTIVE")

    def test_server_building_behavior(self):
        """
        Like :obj:`test_server_in_building_state_for_specified_time`, but by
        creating a behavior via the behaviors API ahead of time, rather than
        passing metadata.
        """
        use_creation_behavior(self.helper, "build", {"duration": 4.0}, [])
        self.do_timing_test(metadata={},
                            before=u"BUILD",
                            delay=5.0,
                            after=u"ACTIVE")

    def test_server_active_then_error_behavior(self):
        """
        When a server is created with the :obj:`active-then-error` behavior, it
        will go into the "error" state after the specified ``duration`` number
        of seconds.
        """
        use_creation_behavior(
            self.helper, "active-then-error", {"duration": 7.0}, [])
        self.do_timing_test(metadata={},
                            before=u"ACTIVE",
                            delay=8.0,
                            after=u"ERROR")

    def do_timing_test(self, metadata, before, delay, after):
        """
        Do a test where a server starts in one status and then transitions to
        another after a period of time.
        """
        # create server with metadata to keep the server in building state for
        # 3 seconds
        server_id = quick_create_server(self.helper, metadata=metadata)

        def get_server_status():
            return status_of_server(self, server_id)

        # get server and verify status is BUILD
        self.assertEquals(get_server_status(), before)

        # List servers with details and verify the server is in BUILD status
        list_servers = request(
            self, self.root, "GET", self.uri + '/servers/detail')
        list_servers_response = self.successResultOf(list_servers)
        self.assertEquals(list_servers_response.code, 200)
        list_servers_response_body = self.successResultOf(
            treq.json_content(list_servers_response))
        self.assertEquals(len(list_servers_response_body['servers']), 1)
        building_server = list_servers_response_body['servers'][0]
        self.assertEquals(building_server['status'], before)
        # Time Passes...
        self.helper.clock.advance(delay)
        # get server and verify status changed to active
        self.assertEquals(get_server_status(), after)

    def test_server_in_error_state(self):
        """
        Test to verify :func:`create_server` creates a server in ERROR state.
        """
        metadata = {"server_error": "1"}
        # create server with metadata to set status in ERROR
        server_id = quick_create_server(self.helper, metadata=metadata)
        # get server and verify status is ERROR
        get_server = request(self, self.root, "GET", self.uri + '/servers/' +
                             server_id)
        get_server_response = self.successResultOf(get_server)
        get_server_response_body = self.successResultOf(
            treq.json_content(get_server_response))
        self.assertEquals(
            get_server_response_body['server']['status'], "ERROR")

    def test_delete_server_fails_specified_number_of_times(self):
        """
        Test to verify :func: `delete_server` does not delete the server,
        and returns the given response code, the number of times specified
        in the metadata
        """
        deletefail = {"times": 1, "code": 500}
        metadata = {"delete_server_failure": json.dumps(deletefail)}
        # create server and verify it was successful
        server_id = quick_create_server(self.helper, metadata=metadata)
        # delete server and verify the response
        delete_server = request(
            self, self.root, "DELETE", self.uri + '/servers/' + server_id)
        delete_server_response = self.successResultOf(delete_server)
        self.assertEqual(delete_server_response.code, 500)
        # get server and verify the server was not deleted
        get_server = request(self, self.root, "GET", self.uri + '/servers/' +
                             server_id)
        get_server_response = self.successResultOf(get_server)
        self.assertEquals(get_server_response.code, 200)
        # delete server again and verify the response
        delete_server = request(
            self, self.root, "DELETE", self.uri + '/servers/' + server_id)
        delete_server_response = self.successResultOf(delete_server)
        self.assertEqual(delete_server_response.code, 204)
        self.assertEqual(self.successResultOf(treq.content(delete_server_response)),
                         b"")
        # get server and verify the server was deleted this time
        get_server = request(
            self, self.root, "GET", self.uri + '/servers/' + server_id)
        get_server_response = self.successResultOf(get_server)
        self.assertEquals(get_server_response.code, 404)

    def test_create_server_failure_using_behaviors(self):
        """
        :func:`create_server` fails with given error message and response code
        when a behavior is registered that matches its hostname.
        """
        use_creation_behavior(
            self.helper,
            "fail",
            {"message": "Create server failure", "code": 500},
            [{"server_name": "failing_server_name"}]
        )
        create_server_response, create_server_response_body = create_server(
            self.helper, name="failing_server_name")
        self.assertEquals(create_server_response.code, 500)
        self.assertEquals(
            create_server_response_body['computeFault']['message'],
            "Create server failure")
        self.assertEquals(
            create_server_response_body['computeFault']['code'], 500)

    def test_create_server_failure_based_on_metadata(self):
        """
        :func:`create_server` fails with the given error message and response
        code when a behavior is registered that matches its metadata.
        """
        use_creation_behavior(
            self.helper,
            "fail",
            {"message": "Sample failure message",
             "type": "specialType", "code": 503},
            [{"metadata": {"field1": "value1",
                           "field2": "reg.*ex"}}]
        )
        create_server_response, _ = create_server(
            self.helper, name="failing_server_name")
        self.assertEquals(create_server_response.code, 202)

        failing_create_response, failing_create_response_body = create_server(
            self.helper,
            metadata={"field1": "value1",
                      "field2": "regular expression"}
        )

        self.assertEquals(
            failing_create_response_body['specialType']['message'],
            "Sample failure message")
        self.assertEquals(
            failing_create_response_body['specialType']['code'], 503)

    def _try_false_negative_failure(self, failure_type=None):
        """
        Helper function to list servers and verify that there are no servers,
        then trigger a false-negative create and verify that it created a
        server.  Returns the failure response so it can be further verified.
        """
        # List servers with details and verify there are no servers
        resp, list_body = self.successResultOf(json_request(
            self, self.root, "GET", self.uri + '/servers'))
        self.assertEqual(resp.code, 200)
        self.assertEqual(len(list_body['servers']), 0)

        params = {"message": "Create server failure", "code": 500}
        if failure_type is not None:
            params["type"] = failure_type

        # Get a 500 creating a server
        use_creation_behavior(
            self.helper,
            "false-negative", params, [{"server_name": "failing_server_name"}]
        )

        create_server_response, body = create_server(
            self.helper,
            name="failing_server_name",
            request_func=request_with_content)
        self.assertEquals(create_server_response.code, 500)

        # List servers with details and verify there are no servers
        resp, list_body = self.successResultOf(json_request(
            self, self.root, "GET", self.uri + '/servers'))
        self.assertEqual(resp.code, 200)
        self.assertEqual(len(list_body['servers']), 1)
        return create_server_response, body

    def test_create_false_negative_failure_using_behaviors(self):
        """
        :func:`create_server` fails with given error message, type, and
        response code, but creates the server anyway, when a behavior is
        registered that matches its hostname.  The type is 'computeFault'
        by default.
        """
        response, body = self._try_false_negative_failure()
        body = json.loads(body)
        self.assertEquals(body['computeFault']['message'],
                          "Create server failure")
        self.assertEquals(body['computeFault']['code'], 500)

    def test_create_false_negative_failure_with_specific_type(self):
        """
        :func:`create_server` fails with given error message, type, and
        response code, but creates the server anyway, when a behavior is
        registered that matches its hostname.  The type is whatever is
        specified if it's not "string".
        """
        response, body = self._try_false_negative_failure('specialType')
        body = json.loads(body)
        self.assertEquals(body['specialType']['message'],
                          "Create server failure")
        self.assertEquals(body['specialType']['code'], 500)

    def test_create_false_negative_failure_with_string_type(self):
        """
        :func:`create_server` fails with given error body and
        response code, but creates the server anyway, when a behavior is
        registered that matches its hostname.  The body is just a string
        when the type is "string".
        """
        response, body = self._try_false_negative_failure("string")
        self.assertEquals(body, "Create server failure")

    def test_modify_status_non_existent_server(self):
        """
        When using the ``.../attributes`` endpoint, if a non-existent server is
        specified, the server will respond with a "bad request" status code and
        not modify the status of any server.
        """
        nova_control_endpoint = self.helper.auth.get_service_endpoint(
            "cloudServersBehavior", "ORD")
        server_id_1 = quick_create_server(self.helper)
        server_id_2 = quick_create_server(self.helper)
        server_id_3 = quick_create_server(self.helper)

        status_modification = {
            "status": {
                server_id_1: "ERROR",
                server_id_2: "ERROR",
                server_id_3: "ERROR",
                "not_a_server_id": "BUILD",
            }
        }
        set_status = request(
            self, self.root, "POST",
            nova_control_endpoint + "/attributes/",
            json.dumps(status_modification)
        )
        set_status_response = self.successResultOf(set_status)
        self.assertEqual(status_of_server(self, server_id_1), "ACTIVE")
        self.assertEqual(status_of_server(self, server_id_2), "ACTIVE")
        self.assertEqual(status_of_server(self, server_id_3), "ACTIVE")
        self.assertEqual(set_status_response.code, 400)


@behavior_tests_helper_class
class NovaCreateServerBehaviorControlPlane(object):
    """
    Helper object used to generate tests for Nova create server behavior
    CRUD operations.
    """
    criteria = [{"server_name": "failing_server_name"}]
    names_and_params = (
        ("fail",
         {"message": "Create server failure", "code": 500, "type": "string"}),
        ("fail",
         {"message": "Invalid creation", "code": 400, "type": "string"})
    )

    def __init__(self, test_case):
        """
        Set up the criteria, api mock, etc.
        """
        nova_api = NovaApi(["ORD", "MIMIC"])
        self.api_helper = APIMockHelper(
            test_case, [nova_api, NovaControlApi(nova_api=nova_api)])
        self.root = self.api_helper.root

        self.behavior_api_endpoint = "{0}/behaviors/creation".format(
            self.api_helper.get_service_endpoint("cloudServersBehavior"))

    def trigger_event(self):
        """
        Create server with with the name "failing_server_name".
        """
        return create_server(self.api_helper, name="failing_server_name",
                             request_func=request_with_content)

    def validate_injected_behavior(self, name_and_params, response, body):
        """
        Given the behavior that is expected, validate the response and body.
        """
        name, params = name_and_params
        self.api_helper.test_case.assertEquals(response.code, params['code'])
        self.api_helper.test_case.assertEquals(body, params['message'])

    def validate_default_behavior(self, response, body):
        """
        Validate the response and body of a successful server create.
        """
        self.api_helper.test_case.assertEquals(response.code, 202)
        body = json.loads(body)
        self.api_helper.test_case.assertIn('server', body)


class NovaAPIMetadataTests(SynchronousTestCase):
    """
    Tests for the Nova Api plugin handling metadata.
    """

    def setUp(self):
        """
        Create a :obj:`MimicCore` with :obj:`NovaApi` as the only plugin,
        and create a server
        """
        self.helper = APIMockHelper(self, [NovaApi(["ORD", "MIMIC"])])
        self.root = self.helper.root
        self.uri = self.helper.uri

    def get_server_url(self, metadata):
        """
        Create a server with the given metadata, and return the URL of
        the server.
        """
        response, body = create_server(self.helper, metadata=metadata)
        self.assertEqual(response.code, 202)
        return [
            link['href'] for link in body['server']['links']
            if link['rel'] == 'self'][0]

    def set_metadata(self, request_body):
        """
        Create a server with null metadata, then hit the set metadata endpoint
        with the given request body.
        """
        return self.successResultOf(json_request(
            self, self.root, "PUT", self.get_server_url(None) + '/metadata',
            request_body))

    def set_metadata_item(self, create_metadata, key, request_body):
        """
        Create a server with given metadata, then hit the set metadata item
        endpoint with the given request body.
        """
        return self.successResultOf(json_request(
            self, self.root, "PUT",
            self.get_server_url(create_metadata) + '/metadata/' + key,
            request_body))

    def get_created_server_metadata(self):
        """
        Ok, we've lost the link to the original server.  But there should
        just be the one.  Get its metadata.
        """
        resp, body = self.successResultOf(json_request(
            self, self.root, "GET", self.uri + '/servers/detail'))
        self.assertEqual(resp.code, 200)

        return body['servers'][0]['metadata']

    def assert_malformed_body(self, response, body):
        """
        Assert that the response and body are 400:malformed request body.
        """
        self.assertEqual(response.code, 400)
        self.assertEqual(body, {"badRequest": {
            "message": "Malformed request body",
            "code": 400
        }})

    def assert_maximum_metadata(self, response, body):
        """
        Assert that the response and body are 403:max metadata.
        """
        self.assertEqual(response.code, 403)
        self.assertEqual(body, {"forbidden": {
            "message": "Maximum number of metadata items exceeds 40",
            "code": 403
        }})

    def assert_metadata_not_string(self, response, body):
        """
        Assert that the response and body are 400:metadata value not string.
        """
        self.assertEqual(response.code, 400)
        self.assertEqual(body, {"badRequest": {
            "message": (
                "Invalid metadata: The input is not a string or unicode"),
            "code": 400
        }})

    def assert_no_such_server(self, response, body):
        """
        Assert that the response and body are 404:server does not exist.
        """
        self.assertEqual(response.code, 404)
        self.assertEqual(body, {
            'itemNotFound': {
                'message': 'Server does not exist',
                'code': 404
            }
        })

    def test_create_server_with_invalid_metadata_object(self):
        """
        When ``create_server`` with an invalid metadata object (a string), it
        should return an HTTP status code of 400:malformed body.
        """
        self.assert_malformed_body(
            *create_server(self.helper, metadata="not metadata"))

    def test_create_server_with_too_many_metadata_items(self):
        """
        When ``create_server`` is passed metadata with too many items, it
        should return an HTTP status code of 403 and an error message saying
        there are too many items.
        """
        metadata = dict(("key{0}".format(i), "value{0}".format(i))
                        for i in xrange(100))
        self.assert_maximum_metadata(
            *create_server(self.helper, metadata=metadata))

    def test_create_server_with_invalid_metadata_values(self):
        """
        When ``create_server`` is passed metadata with non-string-type values,
        it should return an HTTP status code of 400 and an error message
        saying that values must be strings or unicode.
        """
        self.assert_metadata_not_string(
            *create_server(self.helper, metadata={"key": []}))

    def test_create_server_too_many_metadata_items_takes_precedence(self):
        """
        When ``create_server`` is passed metadata with too many items and
        invalid metadata values, the too many items error takes precedence.
        """
        metadata = dict(("key{0}".format(i), []) for i in xrange(100))
        self.assert_maximum_metadata(
            *create_server(self.helper, metadata=metadata))

    def test_create_server_null_metadata_succeeds(self):
        """
        When ``create_server`` is passed null metadata, it successfully
        creates a server.
        """
        response, body = create_server(self.helper, metadata=None)
        self.assertEqual(response.code, 202)

    def test_get_metadata(self):
        """
        Getting metadata gets whatever metadata the server has.
        """
        metadata = {'key': 'value', 'key2': 'anothervalue'}
        response, body = self.successResultOf(json_request(
            self, self.root, "GET",
            self.get_server_url(metadata) + '/metadata'))
        self.assertEqual(response.code, 200)
        self.assertEqual(body, {'metadata': metadata})

        # double check against server details
        self.assertEqual(
            body, {'metadata': self.get_created_server_metadata()})

    def test_get_metadata_on_nonexistant_server_404(self):
        """
        Getting metadata on a non-existing server results in a 404.
        """
        response, body = self.successResultOf(json_request(
            self, self.root, "GET",
            self.uri + '/servers/1234/metadata'))
        self.assert_no_such_server(response, body)

    def test_set_metadata_on_nonexistant_server_404(self):
        """
        Setting metadata on a non-existing server results in a 404.
        """
        response, body = self.successResultOf(json_request(
            self, self.root, "PUT",
            self.uri + '/servers/1234/metadata',
            {'metadata': {}}))
        self.assert_no_such_server(response, body)

    def test_set_metadata_with_only_metadata_body_succeeds(self):
        """
        When setting metadata with a body that looks like
        ``{'metadata': {<valid metadata>}}``, a 200 is received with a valid
        response body.
        """
        response, body = self.set_metadata({"metadata": {}})
        self.assertEqual(response.code, 200)
        self.assertEqual(body, {'metadata': {}})
        self.assertEqual(self.get_created_server_metadata(), {})

    def test_set_metadata_with_extra_keys_succeeds(self):
        """
        When setting metadata with a body that contains extra garbage keys,
        a 200 is received with a valid response body.
        """
        response, body = self.set_metadata({"metadata": {}, "extra": "junk"})
        self.assertEqual(response.code, 200)
        self.assertEqual(body, {'metadata': {}})
        self.assertEqual(self.get_created_server_metadata(), {})

    def test_set_metadata_to_null_fails(self):
        """
        When setting metadata to null, a 400 with a specific message is
        received.
        """
        response, body = self.set_metadata({"metadata": None})
        self.assertEqual(response.code, 400)
        self.assertEqual(body, {
            "badRequest": {
                "message": "Malformed request body. metadata must be object",
                "code": 400
            }
        })

    def test_set_metadata_with_invalid_json_body_fails(self):
        """
        When setting metadata with an invalid request body (not a dict), it
        should return an HTTP status code of 400:malformed request body
        """
        self.assert_malformed_body(*self.set_metadata('meh'))

    def test_set_metadata_with_invalid_metadata_object(self):
        """
        When ``set_metadata`` is passed a dictionary with the metadata key,
        but the metadata is not a dict, it should return an HTTP status code
        of 400: malformed request body.
        """
        self.assert_malformed_body(
            *self.set_metadata({"metadata": "not metadata"}))

    def test_set_metadata_without_metadata_key(self):
        """
        When ``set_metadata`` is passed metadata with the wrong key, it
        should return an HTTP status code of 400: malformed request body.
        """
        self.assert_malformed_body(
            *self.set_metadata({"meta": {"wrong": "metadata key"}}))

    def test_set_metadata_with_too_many_metadata_items(self):
        """
        When ``set_metadata`` is passed metadata with too many items, it
        should return an HTTP status code of 403 and an error message saying
        there are too many items.
        """
        metadata = dict(("key{0}".format(i), "value{0}".format(i))
                        for i in xrange(100))
        self.assert_maximum_metadata(
            *self.set_metadata({"metadata": metadata}))

    def test_set_metadata_with_invalid_metadata_values(self):
        """
        When ``set_metadata`` is passed metadata with non-string-type values,
        it should return an HTTP status code of 400 and an error message
        saying that values must be strings or unicode.
        """
        self.assert_metadata_not_string(
            *self.set_metadata({"metadata": {"key": []}}))

    def test_set_metadata_on_nonexistant_server_404_takes_precedence(self):
        """
        Setting metadata on a non-existing server results in a 404, no matter
        how broken the metadata is.
        """
        response, body = self.successResultOf(json_request(
            self, self.root, "PUT",
            self.uri + '/servers/1234/metadata',
            'meh'))
        self.assert_no_such_server(response, body)

    def test_set_metadata_too_many_metadata_items_takes_precedence(self):
        """
        When ``set_metadata`` is passed metadata with too many items and
        invalid metadata values, the too many items error takes precedence.
        """
        metadata = dict(("key{0}".format(i), []) for i in xrange(100))
        self.assert_maximum_metadata(
            *self.set_metadata({"metadata": metadata}))

    def test_set_metadata_item_on_nonexistant_server_404(self):
        """
        Setting metadata item on a non-existing server results in a 404.
        """
        response, body = self.successResultOf(json_request(
            self, self.root, "PUT",
            self.uri + '/servers/1234/metadata/key',
            {'meta': {'key': 'value'}}))
        self.assert_no_such_server(response, body)

    def test_set_metadata_item_with_only_meta_body_succeeds(self):
        """
        When setting a metadata item with a body that looks like
        ``{'meta': {<valid key>: <valid value>}}``, a 200 is received with a
        valid response body.
        """
        response, body = self.set_metadata_item(
            {}, 'key', {"meta": {'key': 'value'}})
        self.assertEqual(response.code, 200)
        self.assertEqual(body, {'meta': {'key': 'value'}})
        self.assertEqual(self.get_created_server_metadata(), {'key': 'value'})

    def test_set_metadata_item_with_extra_keys_succeeds(self):
        """
        When setting metadata with a body that contains extra garbage keys,
        a 200 is received with a valid response body.
        """
        response, body = self.set_metadata_item(
            {}, 'key', {"meta": {'key': 'value'}, "extra": "junk"})
        self.assertEqual(response.code, 200)
        self.assertEqual(body, {'meta': {'key': 'value'}})
        self.assertEqual(self.get_created_server_metadata(), {'key': 'value'})

    def test_set_metadata_item_with_invalid_json_body_fails(self):
        """
        When setting metadata item with an invalid request body, it should
        return an HTTP status code of 400:malformed request body
        """
        self.assert_malformed_body(*self.set_metadata_item({}, "meh", "meh"))

    def test_set_metadata_item_with_wrong_key_fails(self):
        """
        When setting metadata item without a 'meta' key should
        return an HTTP status code of 400:malformed request body
        """
        self.assert_malformed_body(
            *self.set_metadata_item({}, "meh",
                                        {"metadata": {"meh": "value"}}))

    def test_set_metadata_item_with_mismatching_key_and_body(self):
        """
        When setting metadata item, the key in the 'meta' dictionary needs to
        match the key in the URL, or a special 400 response is returned.
        """
        response, body = self.set_metadata_item(
            {}, "key", {"meta": {"notkey": "value"}})
        self.assertEqual(response.code, 400)
        self.assertEqual(body, {
            "badRequest": {
                "message": "Request body and URI mismatch",
                "code": 400
            }
        })

    def test_set_metadata_item_with_wrong_meta_type_fails(self):
        """
        When setting metadata item without a 'meta' key mapped to not a
        dictionary should return an HTTP status code of 400:malformed request
        body
        """
        self.assert_malformed_body(
            *self.set_metadata_item({}, "meh", {"meta": "wrong"}))

    def test_set_metadata_item_with_too_many_keys_and_values(self):
        """
        When ``set_metadata_item`` is passed too many keys and values, it
        should return an HTTP status code of 400 and a special
        metadata-item-only error message saying there are too many items.
        """
        response, body = self.set_metadata_item(
            {}, 'key', {"meta": {"key": "value", "otherkey": "otherval"}})
        self.assertEqual(response.code, 400)
        self.assertEqual(body, {
            "badRequest": {
                "message": "Request body contains too many items",
                "code": 400
            }
        })

    def test_set_metadata_item_with_too_many_metadata_items_already(self):
        """
        When ``set_metadata_item`` is called with a new key and there are
        already the maximum number of metadata items on the server already,
        it should return an HTTP status code of 403 and an error message
        saying there are too many items.
        """
        metadata = dict(("key{0}".format(i), "value{0}".format(i))
                        for i in xrange(40))
        self.assert_maximum_metadata(
            *self.set_metadata_item(metadata, 'newkey',
                                    {"meta": {"newkey": "newval"}}))

    def test_set_metadata_item_replace_existing_metadata(self):
        """
        If there are already the maximum number of metadata items on the
        server, but ``set_metadata_item`` is called with an already existing
        key, it should succeed (because it replaces the original metadata
        item).
        """
        metadata = dict(("key{0}".format(i), "value{0}".format(i))
                        for i in xrange(40))
        response, body = self.set_metadata_item(
            metadata, 'key0', {"meta": {"key0": "newval"}})
        self.assertEqual(response.code, 200)
        self.assertEqual(body, {"meta": {"key0": "newval"}})

        expected = dict(("key{0}".format(i), "value{0}".format(i))
                        for i in xrange(1, 40))
        expected['key0'] = 'newval'
        self.assertEqual(self.get_created_server_metadata(), expected)

    def test_set_metadata_item_with_invalid_metadata_values(self):
        """
        When ``set_metadata_item`` is passed metadata with non-string-type values,
        it should return an HTTP status code of 400 and an error message
        saying that values must be strings or unicode.
        """
        self.assert_metadata_not_string(
            *self.set_metadata_item({}, 'key', {"meta": {"key": []}}))

    def test_set_metadata_item_on_nonexistant_server_404_takes_precedence(
            self):
        """
        Setting metadata item on a non-existing server results in a 404, and
        takes precedence over other errors.
        """
        response, body = self.successResultOf(json_request(
            self, self.root, "PUT",
            self.uri + '/servers/1234/metadata/key',
            'meh'))
        self.assert_no_such_server(response, body)

    def test_set_metadata_item_too_many_metadata_items_takes_precedence(self):
        """
        When ``set_metadata_item`` is passed metadata with too many items and
        invalid metadata values, the too many items error takes precedence.
        """
        metadata = dict(("key{0}".format(i), "value{0}".format(i))
                        for i in xrange(40))
        self.assert_maximum_metadata(
            *self.set_metadata_item(metadata, 'key', {"meta": {"key": []}}))


class NovaServerTests(SynchronousTestCase):
    def test_unique_ips(self):
        """
        The private IP address of generated servers will be unique even if
        the given ``ipsegment`` factory generates non-unique pairs.
        """
        nova_api = NovaApi(["ORD", "MIMIC"])
        self.helper = self.helper = APIMockHelper(
            self, [nova_api, NovaControlApi(nova_api=nova_api)]
        )
        coll = RegionalServerCollection(
            tenant_id='abc123', region_name='ORD', clock=self.helper.clock,
            servers=[])
        creation_json = {
            'server': {'name': 'foo', 'flavorRef': 'bar', 'imageRef': 'baz'}}

        def ipsegment():
            yield 1
            yield 1
            yield 2
            yield 2
            yield 3
            yield 3

        Server.from_creation_request_json(coll, creation_json,
                                          ipsegment=ipsegment().next)
        Server.from_creation_request_json(coll, creation_json,
                                          ipsegment=ipsegment().next)
        self.assertEqual(coll.servers[0].private_ips,
                         [IPv4Address(address='10.180.1.1')])
        self.assertEqual(coll.servers[1].private_ips,
                         [IPv4Address(address='10.180.2.2')])
