
import json
import treq

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
        get_server = request(
            self, self.root, "GET", self.uri + '/servers/test-server-id')
        get_server_response = self.successResultOf(get_server)
        self.assertEqual(get_server_response.code, 404)

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
