import json
from uuid import uuid4

from twisted.trial.unittest import SynchronousTestCase
from twisted.internet.task import Clock

from mimic.core import MimicCore
from mimic.resource import MimicRoot
from mimic.test.helpers import json_request, request
from mimic.model.ironic_objects import IronicNodeStore, Node


class IronicNodeStoreUnitTests(SynchronousTestCase):
    """
    Unit test for `node_by_id` in :obj:`IronicNodeStore`
    """

    def test_node_by_id(self):
        """
        Test for :func:`node_by_id`
        """
        node_list = [Node(node_id=str(uuid4())) for each in range(2)]
        node_store = IronicNodeStore(ironic_node_store=node_list)
        self.assertFalse(node_store.node_by_id('111'))


class IronicAPITests(SynchronousTestCase):

    """
    Tests for the Ironic api
    """

    def setUp(self):
        """
        Initialize core and root
        """
        self.core = MimicCore(Clock(), [])
        self.root = MimicRoot(self.core).app.resource()
        self.node_details_attributes = [
            "instance_uuid", "target_power_state",
            "properties", "uuid", "driver_info", "target_provision_state",
            "last_error", "console_enabled", "extra", "driver", "links",
            "maintenance_reason", "updated_at", "provision_updated_at",
            "maintenance", "provision_state", "reservation", "created_at",
            "power_state", "instance_info", "ports", "name", "driver_internal_info",
            "inspection_finished_at", "inspection_started_at", "clean_step"
        ]

    def get_nodes(self, postfix=None):
        """
        Get nodes and return content
        """
        url = "/ironic/v1/nodes"
        if postfix:
            url = "/ironic/v1/nodes" + postfix
        (response, content) = self.successResultOf(json_request(
            self, self.root, "GET", url))
        self.assertEqual(200, response.code)
        return content

    def test_list_nodes(self):
        """
        Test ``/nodes`` to return response code 200 and validate the
        attributes of the json response body
        """
        content = self.get_nodes()
        for each_node in content['nodes']:
            self.assertEqual(
                sorted(each_node.keys()),
                sorted(['instance_uuid', 'uuid', 'links', 'maintenance',
                        'provision_state', 'power_state', 'name']))

    def test_list_nodes_with_details(self):
        """
        Test ``/nodes/detail`` to return response code 200 and validate a
        response body exists.
        """
        content = self.get_nodes('/detail')
        self.assertTrue(len(content['nodes']) > 1)
        for each_node in content['nodes']:
            self.assertEqual(
                sorted(each_node.keys()),
                sorted(self.node_details_attributes))
        instance_nodes = [node['extra']['flavor'] if node['extra'].get('flavor')
                          else None
                          for node in content['nodes']]
        self.assertEqual(instance_nodes.count('onmetal-io1'), 32)
        self.assertEqual(instance_nodes.count('onmetal-compute1'), 30)
        self.assertEqual(instance_nodes.count('onmetal-memory1'), 30)

    def test_list_nodes_with_details_is_consistent(self):
        """
        Test ``/nodes/detail`` to return response code 200 and validate a
        response body is the consistent.
        """
        content1 = self.get_nodes('/detail')
        content2 = self.get_nodes('/detail')
        self.assertTrue(content1, content2)

    def test_get_node_details(self):
        """
        Test ``/nodes/<node_id>`` to return response code 200 and validate the
        attributes of the json response body
        """
        node_id = uuid4()
        content = self.get_nodes('/' + str(node_id))
        self.assertEqual(
            sorted(content.keys()),
            sorted(self.node_details_attributes))

    def test_list_node_details_for_onmetal_flavors(self):
        """
        Test ``/nodes/detail`` to return response code 200 and validate the
        onmetal flavors have the corresponding memory associated on a node.
        """
        expected_flavor_memory = {"onmetal-io1": 131072, "onmetal-compute1": 32768,
                                  "onmetal-memory1": 524288}
        content = self.get_nodes('/detail')
        for each in content['nodes']:
            self.assertTrue(
                (each['extra']['flavor'] in expected_flavor_memory.keys()) and
                (each['properties']['memory_mb'] == expected_flavor_memory[each['extra']['flavor']]))

    def test_setting_provision_state(self):
        """
        Test ``/nodes/<node-id>/states/provision`` returns a 200 and
        sets the `provision_state` on the node.
        """
        node_id = uuid4()
        # GET node essentially creates a node
        content = self.get_nodes('/' + str(node_id))
        provision_state = content['provision_state']
        self.assertEqual(provision_state, 'available')

        # Change the provision_state to 'active'
        url = "/ironic/v1/nodes/{0}/states/provision".format(node_id)
        response = self.successResultOf(request(
            self, self.root, "PUT", url, body=json.dumps({'target': 'active'})))
        self.assertEqual(response.code, 202)

        content = self.get_nodes('/' + str(node_id))
        provision_state = content['provision_state']
        self.assertEqual(provision_state, 'active')

    def test_setting_provision_state_fails(self):
        """
        Test ``/nodes/<node-id>/states/provision`` returns a 404 when
        the node does not exist
        """
        url = "/ironic/v1/nodes/111/states/provision"
        (response, content) = self.successResultOf(json_request(
            self, self.root, "PUT", url, body=json.dumps({'target': 'active'})))
        self.assertEqual(response.code, 404)
        self.assertTrue('111' in content['error_message']['faultstring'])

    def test_vendor_passthru_cache_image_fails_when_node_not_found(self):
        """
        Test ``/nodes/<node-id>/vendor_passthru/cache_image`` returns a 404 when
        the node does not exist
        """
        url = "/ironic/v1/nodes/222/vendor_passthru/cache_image"
        (response, content) = self.successResultOf(json_request(
            self, self.root, "POST", url, body=json.dumps({})))
        self.assertEqual(response.code, 404)
        self.assertTrue('222' in content['error_message']['faultstring'])

    def test_vendor_passthru_cache_image_fails_when_method_not_found(self):
        """
        Test ``/nodes/<node-id>/vendor_passthru/cache_image`` returns a 400 when
        the the method is not `cache_image`
        """
        node_id = uuid4()
        # GET node essentially creates the node with the given node_id
        self.get_nodes('/' + str(node_id))

        url = "/ironic/v1/nodes/{0}/vendor_passthru/not_cache_image".format(node_id)
        response = self.successResultOf(request(
            self, self.root, "POST", url, body=json.dumps({})))
        self.assertEqual(response.code, 400)

    def test_vendor_passthru_cache_image_fails_when_args_invalid(self):
        """
        Test ``/nodes/<node-id>/vendor_passthru/cache_image`` returns a 400 when
        the body for the request is invalid
        """
        node_id = uuid4()
        # GET node essentially creates the node with the given node_id
        self.get_nodes('/' + str(node_id))

        body_list = [{"image_info": {}}, {"image": {"id": "111"}},
                     {"image_invalid": {"inv": None}}, {"image_info": {"id": None}}]
        for each in body_list:
            url = "/ironic/v1/nodes/{0}/vendor_passthru/cache_image".format(node_id)
            response = self.successResultOf(request(
                self, self.root, "POST", url, body=json.dumps(each)))
            self.assertEqual(response.code, 400)

    def test_vendor_passthru_cache_image(self):
        """
        Test ``/nodes/<node-id>/vendor_passthru/cache_image`` returns a 202 and
        sets the cache_image_id and cache_status on the node
        """
        node_id = uuid4()
        # GET node essentially creates the node with the given node_id
        content = self.get_nodes('/' + str(node_id))
        self.assertFalse(content['driver_info'].get('cache_image_id'))
        self.assertFalse(content['driver_info'].get('cache_status'))

        image_id = str(uuid4())
        body = {"image_info": {"id": image_id}}
        url = "/ironic/v1/nodes/{0}/vendor_passthru/cache_image".format(node_id)
        response = self.successResultOf(request(
            self, self.root, "POST", url, body=json.dumps(body)))
        self.assertEqual(response.code, 202)

        # GET node and verify the cache attributes on `driver_info`
        content = self.get_nodes('/' + str(node_id))
        self.assertEqual(content['driver_info']['cache_image_id'], image_id)
        self.assertEqual(content['driver_info']['cache_status'], 'cached')

    def test_vendor_passthru_cache_image_list_nodes(self):
        """
        Test ``/nodes/<node-id>/vendor_passthru/cache_image`` returns a 202 and
        sets the cache_image_id and cache_status on the node, and not the other nodes.
        """
        content1 = self.get_nodes('/detail')
        node_id = content1['nodes'].pop()['uuid']

        image_id = str(uuid4())
        body = {"image_info": {"id": image_id}}
        url = "/ironic/v1/nodes/{0}/vendor_passthru/cache_image".format(node_id)
        response = self.successResultOf(request(
            self, self.root, "POST", url, body=json.dumps(body)))
        self.assertEqual(response.code, 202)

        # GET node and verify the cache attributes on `driver_info`
        content = self.get_nodes('/' + str(node_id))
        self.assertEqual(content['driver_info']['cache_image_id'], image_id)
        self.assertEqual(content['driver_info']['cache_status'], 'cached')

        # verify the other nodes are not cached
        content2 = self.get_nodes('/detail')
        self.assertTrue(content1, content2)
        non_cached_nodes = [each for each in content2['nodes']]
        non_cached_nodes.pop()
        for each in non_cached_nodes:
            self.assertFalse(each['driver_info']['cache_image_id'])
            self.assertFalse(each['driver_info']['cache_status'])
