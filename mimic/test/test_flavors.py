"""
Tests for :mod:`nova_api` and :mod:`nova_objects` for flavors.
"""

from twisted.trial.unittest import SynchronousTestCase

from mimic.test.helpers import json_request, request
from mimic.rest.nova_api import NovaApi, NovaControlApi
from mimic.test.fixtures import APIMockHelper


class NovaAPIFlavorsTests(SynchronousTestCase):

    """
    Tests for Flavors using the Nova Api plugin.
    """

    def setUp(self):
        """
        Create a :obj:`MimicCore` with :obj:`NovaApi` as the only plugin.
        """
        nova_api = NovaApi(["ORD", "MIMIC"])
        self.helper = self.helper = APIMockHelper(
            self, [nova_api, NovaControlApi(nova_api=nova_api)]
        )
        self.root = self.helper.root
        self.uri = self.helper.uri

    def get_server_flavor(self, postfix):
        """
        Get flavors, assert response code is 200 and return response body.
        """
        (response, content) = self.successResultOf(json_request(
            self, self.root, "GET", self.uri + postfix))
        self.assertEqual(200, response.code)
        return content

    def test_get_server_flavor_negative(self):
        """
        Test to verify :func:`get_flavor` when invalid flavor from the
        :obj: `mimic_presets` is provided.
        """
        get_server_flavor = request(self, self.root, "GET", self.uri +
                                    '/flavors/1')
        get_server_flavor_response = self.successResultOf(get_server_flavor)
        self.assertEqual(get_server_flavor_response.code, 404)

    def test_get_server_flavor(self):
        """
        Test to verify :func:`get_image` on ``GET /v2.0/<tenant_id>/flavors/<flavor_id>``
        """
        get_server_flavor_response_body = self.get_server_flavor(
            '/flavors/test-flavor-id')

        self.assertEqual(
            get_server_flavor_response_body['flavor']['id'], 'test-flavor-id')

    def test_get_flavor_list(self):
        """
        Test to verify :func:`get_flavor_list` on ``GET /v2.0/<tenant_id>/flavors``
        """
        get_flavor_list_response_body = self.get_server_flavor('/flavors')
        flavor_list = get_flavor_list_response_body['flavors']
        self.assertTrue(len(flavor_list) > 1)
        for each_flavor in flavor_list:
            self.assertEqual(sorted(each_flavor.keys()), sorted(['id', 'name', 'links']))

    def test_get_flavor_list_with_details(self):
        """
        Test to verify :func:`test_get_flavor_list_with_details` on
        ``GET /v2.0/<tenant_id>/flavors/details``
        """
        get_flavor_list_response_body = self.get_server_flavor('/flavors/detail')
        flavor_list = get_flavor_list_response_body['flavors']
        self.assertTrue(len(flavor_list) > 1)
        for each_flavor in flavor_list:
            self.assertEqual(
                sorted(each_flavor.keys()),
                sorted(['id', 'name', 'links', 'ram', 'OS-FLV-WITH-EXT-SPECS:extra_specs',
                        'vcpus', 'swap', 'rxtx_factor', 'OS-FLV-EXT-DATA:ephemeral', 'disk']))

    def test_get_flavor_list_with_details_is_consistent(self):
        """
        Test to verify ``GET /v2.0/<tenant_id>/flavors/details`` returns
        consistent data on mutiple list calls
        """
        get_flavor_list_response_body = self.get_server_flavor('/flavors/detail')
        get_flavor_list2_response_body = self.get_server_flavor('/flavors/detail')
        self.assertEqual(get_flavor_list_response_body, get_flavor_list2_response_body)

    def test_get_flavor_list_after_list_flavors(self):
        """
        Test to verify :func:`get_flavor_list` on ``GET /v2.0/<tenant_id>/flavors``
        http://docs.rackspace.com/servers/api/v2/cs-devguide/content/List_Flavors-d1e4188.html
        """
        flavor_list = self.get_server_flavor('/flavors')['flavors']
        for each_flavor in flavor_list:
            flavor_id = each_flavor['id']
            name = each_flavor['name']
            get_server_flavor_response_body = self.get_server_flavor('/flavors/' + flavor_id)
            self.assertEqual(flavor_id, get_server_flavor_response_body['flavor']['id'])
            self.assertEqual(name, get_server_flavor_response_body['flavor']['name'])
