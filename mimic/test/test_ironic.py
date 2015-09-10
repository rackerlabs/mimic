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
            "instance_uuid", "target_power_state", "chassis_uuid",
            "properties", "uuid", "driver_info", "target_provision_state",
            "last_error", "console_enabled", "extra", "driver", "links",
            "maintenance_reason", "updated_at", "provision_updated_at",
            "maintenance", "provision_state", "reservation", "created_at",
            "power_state", "instance_info", "ports", "name", "driver_internal_info",
            "inspection_finished_at", "inspection_started_at", "clean_step"
        ]
        self.url = "/ironic/v1/nodes"
        self.create_request = {
            "chassis_uuid": str(uuid4()),
            "driver": "agent_ipmitool",
            "driver_info": {"ipmi_username": "mimic-user",
                            "ipmi_address": "127.0.0.0",
                            "ipmi_password": "******"},
            "name": "test_node",
            "properties": {
                "cpus": "1",
                "local_gb": "10",
                "memory_mb": "1024"
            }
        }

    def create_node(self, create_request=None):
        """
        Create a new node and return node.
        """
        request = create_request or self.create_request
        (response, content) = self.successResultOf(json_request(
            self, self.root, "POST", self.url, body=json.dumps(request)))
        self.assertEqual(response.code, 201)
        return content

    def get_nodes(self, postfix=None):
        """
        Get nodes and return content
        """
        url = self.url
        if postfix:
            url = self.url + postfix
        (response, content) = self.successResultOf(json_request(
            self, self.root, "GET", url))
        self.assertEqual(200, response.code)
        return content

    def test_create_node(self):
        """
        Create node returns 201 and the newly created node.
        """
        new_node = self.create_node(self.create_request)
        for key in self.create_request.keys():
            self.assertEqual(self.create_request[key], new_node[key])

    def test_create_node_failure(self):
        """
        Create node returns 400 if the request json is not
        as expected.
        """
        response = self.successResultOf(request(
            self, self.root, "POST", self.url, body=json.dumps("")))
        self.assertEqual(response.code, 400)

    def test_delete_node_when_node_does_not_exist(self):
        """
        Delete node returns 404 when the given node_id
        does not exist.
        """
        response = self.successResultOf(request(
            self, self.root, "DELETE", self.url + "/1234"))
        self.assertEqual(response.code, 404)

    def test_delete_node(self):
        """
        Delete node returns 204 deletes the given node_id.
        """
        content = self.create_node()
        node_id = str(content['uuid'])

        # delete node
        response = self.successResultOf(request(
            self, self.root, "DELETE", self.url + '/' + node_id))
        self.assertEqual(response.code, 204)

        # get node
        response = self.successResultOf(request(
            self, self.root, "GET", self.url + '/' + node_id))
        self.assertEqual(404, response.code)

    def test_create_then_get_node(self):
        """
        Test create node then get the node and verify attributes
        """
        create_request = {"properties": {"memory_mb": 32768}}
        content = self.create_node(create_request)
        node_id = str(content['uuid'])
        self.assertEqual(content['properties']['memory_mb'],
                         create_request['properties']['memory_mb'])

        # get node
        (response, get_content) = self.successResultOf(json_request(
            self, self.root, "GET", self.url + '/' + node_id))
        self.assertEqual(200, response.code)
        self.assertEqual(content, get_content)

    def test_create_then_get_node_with_default_attributes(self):
        """
        Test create node then get the node and verify attributes
        """
        content = self.create_node()
        node_id = str(content['uuid'])

        # get node
        (response, get_content) = self.successResultOf(json_request(
            self, self.root, "GET", self.url + '/' + node_id))
        self.assertEqual(200, response.code)
        self.assertEqual(content, get_content)

    def test_create_then_get_node_with_mimimum_attributes(self):
        """
        Test create node then get the node and verify attributes
        """
        (response, content) = self.successResultOf(json_request(
            self, self.root, "POST", self.url, body=json.dumps({})))
        self.assertEqual(response.code, 201)
        node_id = str(content['uuid'])
        self.assertFalse(content['properties']['memory_mb'])

        # get node
        (response, get_content) = self.successResultOf(json_request(
            self, self.root, "GET", self.url + '/' + node_id))
        self.assertEqual(200, response.code)
        self.assertEqual(content, get_content)

    def test_create_then_get_node_with_empty_properties_attributes(self):
        """
        Test create node when `properties` attribute is set to None
        """
        self.create_node({"properties": None})

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
        self.assertEqual(instance_nodes.count('onmetal-io1'), 30)
        self.assertEqual(instance_nodes.count('onmetal-compute1'), 32)
        self.assertEqual(instance_nodes.count('onmetal-memory1'), 30)
        provisioned = [node for node in content['nodes']
                       if node['instance_uuid']]
        self.assertEqual(len(provisioned), 2)

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
        # create a node
        content = self.create_node()
        node_id = content['uuid']

        # get node
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
            if each['properties']['memory_mb']:
                self.assertTrue(
                    (each['extra']['flavor'] in expected_flavor_memory.keys()) and
                    (each['properties']['memory_mb'] == expected_flavor_memory[each['extra']['flavor']]))

    def _validate_provisioning(self, new_provision_state):
        """
        Creates a node and verifies the node is 'available'.
        Changes the provision_state of the nodes to `new_provision_state`
        and verifies the state is set.
        Returns the node object after the update.
        """
        # create a node
        content = self.create_node()
        node_id = content['uuid']
        provision_state = content['provision_state']
        self.assertEqual(provision_state, 'available')

        # Change the provision_state
        url = self.url + "/{0}/states/provision".format(node_id)
        response = self.successResultOf(request(
            self, self.root, "PUT", url, body=json.dumps(
                {'target': new_provision_state})))
        self.assertEqual(response.code, 202)

        content = self.get_nodes('/' + str(node_id))
        return content

    def test_setting_provision_state_to_manage(self):
        """
        Test ``/nodes/<node-id>/states/provision`` returns a 200 and
        sets the `provision_state` to 'manage' on the node.
        """
        content = self._validate_provisioning('manage')
        self.assertEqual(content['provision_state'], 'manage')
        self.assertFalse(content['driver_info'].get('cache_image_id'))
        self.assertFalse(content['driver_info'].get('cache_status'))

    def test_setting_provision_state_to_provide(self):
        """
        Test ``/nodes/<node-id>/states/provision`` returns a 200 and
        sets the `provision_state` to 'available' on the node has
        provision_state set to 'provide'
        """
        content = self._validate_provisioning('provide')
        self.assertEqual(content['provision_state'], 'available')
        self.assertFalse(content['driver_info'].get('cache_image_id'))
        self.assertFalse(content['driver_info'].get('cache_status'))

    def test_setting_provision_state_to_active(self):
        """
        Test ``/nodes/<node-id>/states/provision`` returns a 200 and
        sets the `provision_state` to 'active' on the node and
        assigns a instance id.
        """
        content = self._validate_provisioning('active')
        self.assertEqual(content['provision_state'], 'active')
        self.assertTrue(content['instance_uuid'])

    def test_setting_provision_state_fails(self):
        """
        Test ``/nodes/<node-id>/states/provision`` returns a 404 when
        the node does not exist
        """
        url = self.url + "/111/states/provision"
        (response, content) = self.successResultOf(json_request(
            self, self.root, "PUT", url, body=json.dumps({'target': 'active'})))
        self.assertEqual(response.code, 404)
        self.assertTrue('111' in content['error_message']['faultstring'])

    def test_vendor_passthru_cache_image_fails_when_node_not_found(self):
        """
        Test ``/nodes/<node-id>/vendor_passthru/cache_image`` returns a 404 when
        the node does not exist
        """
        url = self.url + "/222/vendor_passthru/cache_image"
        (response, content) = self.successResultOf(json_request(
            self, self.root, "POST", url, body=json.dumps({})))
        self.assertEqual(response.code, 404)
        self.assertTrue('222' in content['error_message']['faultstring'])

    def test_vendor_passthru_cache_image_fails_when_method_not_found(self):
        """
        Test ``/nodes/<node-id>/vendor_passthru/cache_image`` returns a 400 when
        the the method is not `cache_image`
        """
        new_node = self.create_node()
        node_id = new_node['uuid']

        url = self.url + "/{0}/vendor_passthru/not_cache_image".format(node_id)
        response = self.successResultOf(request(
            self, self.root, "POST", url, body=json.dumps({})))
        self.assertEqual(response.code, 400)

    def test_vendor_passthru_cache_image_fails_when_args_invalid(self):
        """
        Test ``/nodes/<node-id>/vendor_passthru/cache_image`` returns a 400 when
        the body for the request is invalid
        """
        new_node = self.create_node()
        node_id = new_node['uuid']

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
        new_node = self.create_node({'properties': {'memory_mb': 131072}})
        node_id = new_node['uuid']

        self.assertFalse(new_node['driver_info'].get('cache_image_id'))
        self.assertFalse(new_node['driver_info'].get('cache_status'))

        image_id = str(uuid4())
        body = {"image_info": {"id": image_id}}
        url = self.url + "/{0}/vendor_passthru/cache_image".format(node_id)
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
        url = self.url + "/{0}/vendor_passthru/cache_image".format(node_id)
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
