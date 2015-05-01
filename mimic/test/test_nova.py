"""
Tests for :mod:`nova_api` and :mod:`nova_objects`.
"""

import json
from urllib import urlencode
from urlparse import parse_qs

from testtools.matchers import (
    Equals, MatchesDict, MatchesListwise, StartsWith)

import treq

from twisted.internet.defer import gatherResults
from twisted.trial.unittest import SynchronousTestCase

from mimic.test.helpers import json_request, request, validate_link_json
from mimic.rest.nova_api import NovaApi, NovaControlApi
from mimic.test.fixtures import APIMockHelper, TenantAuthentication


class NovaAPITests(SynchronousTestCase):

    """
    Tests for the Nova Api plugin.
    """

    def setUp(self):
        """
        Create a :obj:`MimicCore` with :obj:`NovaApi` as the only plugin,
        and create a server
        """
        helper = APIMockHelper(self, [NovaApi(["ORD", "MIMIC"])])
        self.root = helper.root
        self.uri = helper.uri
        self.server_name = 'test_server'
        create_server = request(
            self, self.root, "POST", self.uri + '/servers',
            json.dumps({
                "server": {
                    "name": self.server_name,
                    "imageRef": "test-image",
                    "flavorRef": "test-flavor"
                }
            }))
        self.create_server_response = self.successResultOf(create_server)
        self.create_server_response_body = self.successResultOf(
            treq.json_content(self.create_server_response))
        self.server_id = self.create_server_response_body['server']['id']
        self.nth_endpoint_public = helper.nth_endpoint_public

    def test_create_server_with_manual_diskConfig(self):
        """
        Servers should respect the provided OS-DCF:diskConfig setting if
        supplied.
        """
        create_server = request(
            self, self.root, "POST", self.uri + '/servers',
            json.dumps({
                "server": {
                    "name": self.server_name + "A",
                    "imageRef": "test-image",
                    "flavorRef": "test-flavor",
                    "OS-DCF:diskConfig": "MANUAL",
                }
            }))
        create_server_response = self.successResultOf(create_server)
        response_body = self.successResultOf(
            treq.json_content(create_server_response))
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
        create_server = request(
            self, self.root, "POST", self.uri + '/servers',
            json.dumps({
                "server": {
                    "name": self.server_name + "A",
                    "imageRef": "test-image",
                    "flavorRef": "test-flavor",
                    "OS-DCF:diskConfig": "AUTO-MANUAL",
                }
            }))
        create_server_response = self.successResultOf(create_server)
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

    def test_created_servers_have_dissimilar_admin_passwords(self):
        """
        Two (or more) servers created should not share passwords.
        """
        create_server = request(
            self, self.root, "POST", self.uri + '/servers',
            json.dumps({
                "server": {
                    "name": self.server_name,
                    "imageRef": "test-image",
                    "flavorRef": "test-flavor"
                }
            }))
        other_response = self.successResultOf(create_server)
        other_response_body = self.successResultOf(
            treq.json_content(other_response))
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

    def test_delete_server_negative(self):
        """
        Test to verify :func:`delete_server` on ``DELETE /v2.0/<tenant_id>/servers/<server_id>``,
        when the server_id does not exist
        """
        delete_server = request(
            self, self.root, "DELETE", self.uri + '/servers/test-server-id')
        delete_server_response = self.successResultOf(delete_server)
        self.assertEqual(delete_server_response.code, 404)

    def test_get_server_image(self):
        """
        Test to verify :func:`get_image` on ``GET /v2.0/<tenant_id>/images/<image_id>``
        """
        get_server_image = request(
            self, self.root, "GET", self.uri + '/images/test-image-id')
        get_server_image_response = self.successResultOf(get_server_image)
        get_server_image_response_body = self.successResultOf(
            treq.json_content(get_server_image_response))
        self.assertEqual(get_server_image_response.code, 200)
        self.assertEqual(
            get_server_image_response_body['image']['id'], 'test-image-id')
        self.assertEqual(
            get_server_image_response_body['image']['status'], 'ACTIVE')

    def test_get_server_flavor(self):
        """
        Test to verify :func:`get_image` on ``GET /v2.0/<tenant_id>/flavors/<flavor_id>``
        """
        get_server_flavor = request(
            self, self.root, "GET", self.uri + '/flavors/test-flavor-id')
        get_server_flavor_response = self.successResultOf(get_server_flavor)
        get_server_flavor_response_body = self.successResultOf(
            treq.json_content(get_server_flavor_response))
        self.assertEqual(get_server_flavor_response.code, 200)
        self.assertEqual(
            get_server_flavor_response_body['flavor']['id'], 'test-flavor-id')

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
        other_region_servers = self.successResultOf(
            treq.json_content(
                self.successResultOf(request(self, self.root, "GET",
                                             self.nth_endpoint_public(1)
                                             + "/servers/")))
        )["servers"]
        self.assertEqual(other_region_servers, [])

    def test_different_tenants_same_region(self):
        """
        Creating a server for one tenant in a particular region should not
        create it for other tenants in the same region.
        """
        other_tenant = TenantAuthentication(self, self.root, "other", "other")

        response, response_body = self.successResultOf(
            json_request(
                self, self.root, "GET",
                other_tenant.nth_endpoint_public(0) + '/servers'))

        self.assertEqual(response.code, 200)
        self.assertEqual(response_body, {'servers': []})


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
        helper = APIMockHelper(self, [NovaApi(["ORD", "MIMIC"])])
        self.root = helper.root
        self.uri = helper.uri

    def create_servers(self, n, name_generation=None):
        """
        Create ``n`` servers, returning a list of their server IDs.
        """
        resps = self.successResultOf(gatherResults([
            json_request(
                self, self.root, "POST", self.uri + '/servers',
                json.dumps({
                    "server": {
                        "name": ("{0}".format(i)if name_generation is None
                                 else name_generation(i)),
                        "imageRef": "test-image",
                        "flavorRef": "test-flavor"
                    }
                }))
            for i in range(n)
        ]))
        return [body['server']['id'] for resp, body in resps]

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

    def test_with_invalid_limit(self):
        """
        If a limit that can't be converted into an integer is passed, no
        matter what other parameters there are, return with a 400 bad request.
        """
        self.make_nova_app()
        self.create_servers(2, lambda i: 'server')
        servers = self.list_servers('/servers')['servers']

        combos = ({}, {'marker': servers[0]['id']}, {'name': 'server'},
                  {'marker': servers[0]['id'], 'name': 'server'})

        for path in ('/servers', '/servers/detail'):
            for combo in combos:
                combo['limit'] = 'a'
                error_body = self.list_servers(path, combo, code=400)
                self.assertEqual(
                    {
                        "badRequest": {
                            "message": "limit param must be an integer",
                            "code": 400
                        }
                    },
                    error_body)

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
        helper = APIMockHelper(self, [nova_api, nova_control_api])
        self.nova_control_endpoint = helper.auth.get_service_endpoint(
            "cloudServersBehavior",
            "ORD")
        self.root = helper.root
        self.uri = helper.uri
        self.helper = helper

    def create_server(self, name=None, imageRef=None, flavorRef=None,
                      metadata=None, body='default'):
        """
        Creates a server with the given specifications and returns the response
        object

        :param name: Name of the server
        :param imageRef: Image of the server
        :param flavorRef: Flavor size of the server
        :param metadat: Metadata of the server
        """
        if body == 'default':
            json_request = json.dumps({
                "server": {
                    "name": name or 'test_server',
                    "imageRef": imageRef or "test-image",
                    "flavorRef": flavorRef or "test-flavor",
                    "metadata": metadata or {}
                }
            })
        elif body is None:
            json_request = ""
        else:
            json_request = body

        create_server = request(
            self, self.root, "POST", self.uri + '/servers', json_request
        )
        create_server_response = self.successResultOf(create_server)
        return create_server_response

    def test_create_server_request_with_no_body_causes_bad_request(self):
        """
        Test to verify :func:`create_server` does not fail when it receives a
        request with no body.
        """
        create_server_response = self.create_server(body=None)
        self.assertEquals(create_server_response.code, 400)

    def test_create_server_request_with_invalid_body_causes_bad_request(self):
        """
        Test to verify :func:`create_server` does not fail when it receives a
        request with no body.
        """
        create_server_response = self.create_server(body='{ bad request: }')
        self.assertEquals(create_server_response.code, 400)

    def test_create_server_failure(self):
        """
        Test to verify :func:`create_server` fails with given error message
        and response code in the metadata.
        """
        serverfail = {"message": "Create server failure", "code": 500}
        metadata = {"create_server_failure": json.dumps(serverfail)}
        create_server_response = self.create_server(metadata=metadata)
        self.assertEquals(create_server_response.code, 500)
        create_server_response_body = self.successResultOf(
            treq.json_content(create_server_response))
        self.assertEquals(create_server_response_body['message'],
                          "Create server failure")
        self.assertEquals(create_server_response_body['code'], 500)

    def test_create_server_failure_and_list_servers(self):
        """
        Test to verify :func:`create_server` fails with given error message
        and response code in the metadata and does not actually create a server.
        """
        serverfail = {"message": "Create server failure", "code": 500}
        metadata = {"create_server_failure": json.dumps(serverfail)}
        create_server_response = self.create_server(metadata=metadata)
        self.assertEquals(create_server_response.code, 500)
        create_server_response_body = self.successResultOf(
            treq.json_content(create_server_response))
        self.assertEquals(create_server_response_body['message'],
                          "Create server failure")
        self.assertEquals(create_server_response_body['code'], 500)
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
        self.use_creation_behavior("build", {"duration": 4.0}, [])
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
        self.use_creation_behavior("active-then-error", {"duration": 7.0}, [])
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
        create_server_response = self.create_server(metadata=metadata)
        # verify the create server was successful
        self.assertEquals(create_server_response.code, 202)
        server_id = (self.successResultOf(
            treq.json_content(create_server_response))["server"]["id"]
        )

        def get_server_status():
            get_server = request(self, self.root, "GET",
                                 self.uri + '/servers/' + server_id)
            get_server_response = self.successResultOf(get_server)
            get_server_response_body = self.successResultOf(
                treq.json_content(get_server_response))
            return get_server_response_body['server']['status']

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
        create_server_response = self.create_server(metadata=metadata)
        # verify the create server was successful
        self.assertEquals(create_server_response.code, 202)
        create_server_response_body = self.successResultOf(
            treq.json_content(create_server_response))
        # get server and verify status is ERROR
        get_server = request(self, self.root, "GET", self.uri + '/servers/' +
                             create_server_response_body["server"]["id"])
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
        create_server_response = self.create_server(metadata=metadata)
        self.assertEquals(create_server_response.code, 202)
        create_server_response_body = self.successResultOf(
            treq.json_content(create_server_response))
        # delete server and verify the response
        delete_server = request(self, self.root, "DELETE", self.uri + '/servers/'
                                + create_server_response_body["server"]["id"])
        delete_server_response = self.successResultOf(delete_server)
        self.assertEqual(delete_server_response.code, 500)
        # get server and verify the server was not deleted
        get_server = request(self, self.root, "GET", self.uri + '/servers/' +
                             create_server_response_body["server"]["id"])
        get_server_response = self.successResultOf(get_server)
        self.assertEquals(get_server_response.code, 200)
        # delete server again and verify the response
        delete_server = request(self, self.root, "DELETE", self.uri + '/servers/'
                                + create_server_response_body["server"]["id"])
        delete_server_response = self.successResultOf(delete_server)
        self.assertEqual(delete_server_response.code, 204)
        self.assertEqual(self.successResultOf(treq.content(delete_server_response)),
                         b"")
        # get server and verify the server was deleted this time
        get_server = request(self, self.root, "GET", self.uri + '/servers/' +
                             create_server_response_body["server"]["id"])
        get_server_response = self.successResultOf(get_server)
        self.assertEquals(get_server_response.code, 404)

    def test_get_invalid_image(self):
        """
        Test to verify :func:`get_image` when invalid image from the
        :obj: `mimic_presets` is provided or if image id ends with Z.
        """
        get_server_image = request(self, self.root, "GET", self.uri +
                                   '/images/test-image-idZ')
        get_server_image_response = self.successResultOf(get_server_image)
        self.assertEqual(get_server_image_response.code, 404)

    def test_get_server_flavor(self):
        """
        Test to verify :func:`get_flavor` when invalid flavor from the
        :obj: `mimic_presets` is provided.
        """
        get_server_flavor = request(self, self.root, "GET", self.uri +
                                    '/flavors/1')
        get_server_flavor_response = self.successResultOf(get_server_flavor)
        self.assertEqual(get_server_flavor_response.code, 404)

    def use_creation_behavior(self, name, parameters, criteria):
        """
        Use the given behavior for server creation.
        """
        criterion = {"name": name,
                     "parameters": parameters,
                     "criteria": criteria}
        set_criteria = request(self, self.root, "POST",
                               self.nova_control_endpoint +
                               "/behaviors/creation/",
                               json.dumps(criterion))
        set_criteria_response = self.successResultOf(set_criteria)
        self.assertEqual(set_criteria_response.code, 201)

    def test_create_server_failure_using_behaviors(self):
        """
        :func:`create_server` fails with given error message and response code
        when a behavior is registered that matches its hostname.
        """
        self.use_creation_behavior(
            "fail",
            {"message": "Create server failure", "code": 500},
            [{"server_name": "failing_server_name"}]
        )
        create_server_response = self.create_server(name="failing_server_name")
        self.assertEquals(create_server_response.code, 500)
        create_server_response_body = self.successResultOf(
            treq.json_content(create_server_response))
        self.assertEquals(create_server_response_body['message'],
                          "Create server failure")
        self.assertEquals(create_server_response_body['code'], 500)

    def test_create_server_failure_based_on_metadata(self):
        """
        :func:`create_server` fails with the given error message and response
        code when a behavior is registered that matches its metadata.
        """
        self.use_creation_behavior(
            "fail",
            {"message": "Sample failure message", "code": 503},
            [{"metadata": {"field1": "value1",
                           "field2": "reg.*ex"}}]
        )
        create_server_response = self.create_server(name="failing_server_name")
        self.assertEquals(create_server_response.code, 202)
        self.successResultOf(treq.json_content(create_server_response))

        failing_create_response = self.create_server(
            metadata={"field1": "value1",
                      "field2": "regular expression"}
        )

        failing_create_response_body = self.successResultOf(
            treq.json_content(failing_create_response)
        )

        self.assertEquals(failing_create_response_body['message'],
                          "Sample failure message")
        self.assertEquals(failing_create_response_body['code'], 503)


class NovaAPIMetadataTests(SynchronousTestCase):
    """
    Tests for the Nova Api plugin handling metadata.
    """

    def setUp(self):
        """
        Create a :obj:`MimicCore` with :obj:`NovaApi` as the only plugin,
        and create a server
        """
        helper = APIMockHelper(self, [NovaApi(["ORD", "MIMIC"])])
        self.root = helper.root
        self.uri = helper.uri

    def create_server(self, metadata):
        """
        Create a server with the given metadata.
        """
        return self.successResultOf(json_request(
            self, self.root, "POST", self.uri + '/servers',
            {
                "server": {
                    "name": "A",
                    "imageRef": "test-image",
                    "flavorRef": "test-flavor",
                    "metadata": metadata
                }
            }))

    def get_server_url(self, metadata):
        """
        Create a server with the given metadata, and return the URL of
        the server.
        """
        response, body = self.create_server(metadata)
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
        self.assert_malformed_body(*self.create_server("not metadata"))

    def test_create_server_with_too_many_metadata_items(self):
        """
        When ``create_server`` is passed metadata with too many items, it
        should return an HTTP status code of 403 and an error message saying
        there are too many items.
        """
        metadata = dict(("key{0}".format(i), "value{0}".format(i))
                        for i in xrange(100))
        self.assert_maximum_metadata(*self.create_server(metadata))

    def test_create_server_with_invalid_metadata_values(self):
        """
        When ``create_server`` is passed metadata with non-string-type values,
        it should return an HTTP status code of 400 and an error message
        saying that values must be strings or unicode.
        """
        self.assert_metadata_not_string(*self.create_server({"key": []}))

    def test_create_server_too_many_metadata_items_takes_precedence(self):
        """
        When ``create_server`` is passed metadata with too many items and
        invalid metadata values, the too many items error takes precedence.
        """
        metadata = dict(("key{0}".format(i), []) for i in xrange(100))
        self.assert_maximum_metadata(*self.create_server(metadata))

    def test_create_server_null_metadata_succeeds(self):
        """
        When ``create_server`` is passed null metadata, it successfully
        creates a server.
        """
        response, body = self.create_server(None)
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
            {}, 'key',
            {"meta": {"key": "value", "otherkey": "otherval"}})
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
