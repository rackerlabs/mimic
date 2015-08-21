"""
Model objects for the Nova mimic.
"""
from characteristic import attributes, Attribute
from uuid import uuid4
from json import loads, dumps

from mimic.util.helper import random_hex_generator


@attributes(["node_id",
             Attribute("flavor_id", default_value="onmetal-io1"),
             Attribute("power_state", default_value="power on"),
             Attribute("provision_state", default_value="available"),
             Attribute("instance_uuid", default_value=None),
             Attribute("maintenance", default_value=False),
             Attribute("cache_image_id", default_value=None),
             Attribute("memory_mb", default_value=131072),
             Attribute("name", default_value=None)
             ])
class Node(object):
    """
    A :obj:`Node` is a representation of all the state associated with a ironic
    node.  It can produce JSON-serializable objects for various pieces of
    state that are required for API responses.
    """

    static_defaults = {
        "target_power_state": None,
        "target_provision_state": None,
        "updated_at": "2015-08-09T04:30:05+00:00",
        "last_error": None,
        "console_enabled": False,
        "driver": "agent_ipmitool",
        "maintenance_reason": None,
        "provision_updated_at": "2015-08-07T06:57:24+00:00",
        "reservation": None,
        "created_at": "2014-09-26T18:56:03+00:00",
        "instance_info": None,
        "inspection_finished_at": None,
        "inspection_started_at": None,
        "clean_step": {},
        "driver_internal_info": {
            "clean_steps": None,
            "hardware_manager_version":
            {
                "generic_hardware_manager": "1",
                "onmetal_hardware_manager": "1"
            },
                "is_whole_disk_image": True,
                "agent_erase_devices_iterations": 1,
                "agent_url": "http://127.0.0.1:8900",
                "cleaning_reboot": True,
                "agent_last_heartbeat": 1440117499
        }
    }

    static_instance_info = {
        "root_gb": "32",
        "image_source": str(uuid4()),
        "ephemeral_gb": "3200",
        "configdrive": str(random_hex_generator(100)),
        "image_url": "http://127.0.0.1/mimic-image-url",
        "image_container_format": "bare_mimic",
        "image_disk_format": "mimic",
        "image_checksum": str(random_hex_generator(6)),
        "swap_mb": "0"
    }

    def links_json(self):
        """
        Create a JSON-serializable data structure describing the links to this
        node.
        """
        return [
            {
                "href": "http://link-to-ironic/v1/nodes/".format(self.node_id),
                "rel": "self"
            },
            {
                "href": "http://link-to-ironic/nodes/".format(self.node_id),
                "rel": "bookmark"
            }
        ]

    def port_links_json(self):
        """
        Create a JSON-serializable data structure describing the port links to this
        node.
        """
        return [
            {
                "href": "http://link-to-ironic/v1/nodes/{0}/ports".format(self.node_id),
                "rel": "self"
            },
            {
                "href": "http://link-to-ironic/nodes/{0}/ports".format(self.node_id),
                "rel": "bookmark"
            }
        ]

    def brief_json(self):
        """
        Brief JSON-serializable version of this server, for the non-details
        list nodes request.
        """
        return {
            "instance_uuid": self.instance_uuid,
            "uuid": self.node_id,
            "links": self.links_json(),
            "maintenance": self.maintenance,
            "provision_state": self.provision_state,
            "power_state": self.power_state,
            "name": self.name
        }

    def detail_json(self):
        """
        Long-form JSON-serializable object representation of this node, as
        returned by either a GET on this individual node or a member in the
        list returned by the list-details request.
        """
        template = self.static_defaults.copy()
        template.update({
            "instance_uuid": self.instance_uuid,
            "name": self.name,
            "uuid": self.node_id,
            "links": self.links_json(),
            "maintenance": self.maintenance,
            "provision_state": self.provision_state,
            "power_state": self.power_state,
            "ports": self.port_links_json(),
            "extra": {
                "flavor": self.flavor_id,
                "hardware/inventory/disks/0/size": "31016853504",
                "hardware/interfaces/0/switch_port_id": "Mimic0/01",
                "rackid": "Mimic_rackid",
                "hardware/interfaces/1/switch_chassis_id": "mimic-chassis1",
                "core_id": "00000",
                "hardware/inventory/disks/2/size": "1861817990000",
                "uutsn": "Mimic-uutsn",
                "hardware/inventory/disks/1/size": "1861817990000",
                "hardware/inventory/cpu/count": "40",
                "hardware/inventory/memory/total": "135234740224",
                "hardware/inventory/disks/2/rotational": "False",
                "hardware/inventory/disks/0/rotational": "False",
                "hardware/inventory/disks/1/rotational": "False",
                "racklocation": "Mimic00",
                "hardware/interfaces/1/switch_port_id": "Mimic1/10",
                "hardware/interfaces/0/switch_chassis_id": "mimic-chassis1"
            },
            "properties": {
                "memory_mb": self.memory_mb,
                "cpu_arch": "amd64",
                "local_gb": 32,
                "cpus": 40
            },
            "driver_info": {
                "hardware_manager_version": None,
                "ipmi_username": "USERID",
                "ipmi_address": "127.0.0.0",
                "decommission_target_state": None,
                "ipmi_password": "******",
                "agent_url": "http://127.0.0.1:9999",
                "agent_last_heartbeat": 1427727371,
                "cache_image_id": self.cache_image_id,
                "cache_status": 'cached' if self.cache_image_id else None
            }
        })
        if self.instance_uuid:
            template["instance_info"] = self.static_instance_info
            template["provision_state"] = "active"
        return template


@attributes([Attribute("ironic_node_store", default_factory=list)])
class IronicNodeStore(object):
    """
    A collection of ironic :obj:`Node` objects.
    """

    def node_not_found(self, node_id):
        """
        Error returned by the API calls when the node the action is
        requested upon, does not exist
        """
        return dumps({
            "error_message": {
                "debuginfo": None,
                "faultcode": "Client",
                "faultstring": "Invalid input for field/attribute node_ident. " +
                "Value: 'node={0}'. unable to convert to uuid_or_name".format(node_id)}})

    def node_by_id(self, node_id):
        """
        Retrieve a :obj:`Node` object by its ID.
        """
        for node in self.ironic_node_store:
            if node.node_id == node_id:
                return node

    def add_to_ironic_node_store(self, **attributes):
        """
        Create a new Node object and add it to the
        :obj: `ironic_node_store`
        """
        node = Node(**attributes)
        self.ironic_node_store.append(node)
        return b''

    def list_nodes(self, include_details):
        """
        List Ironic nodes.
        If no nodes were added to the :obj:`ironic_node_store`, then adds nodes
        of different onmetal flavors.

        Supports both:
        http://docs.openstack.org/developer/ironic/webapi/v1.html#get--v1-nodes and
        http://docs.openstack.org/developer/ironic/webapi/v1.html#get--v1-nodes-detail
        """
        if not self.ironic_node_store:
            for each in range(3):
                self.add_to_ironic_node_store(node_id=str(uuid4()),
                                              flavor_id="onmetal-io1",
                                              memory_mb=131072)
            for each in range(3):
                self.add_to_ironic_node_store(node_id=str(uuid4()),
                                              flavor_id="onmetal-compute1",
                                              memory_mb=32768)
            for each in range(3):
                self.add_to_ironic_node_store(node_id=str(uuid4()),
                                              flavor_id="onmetal-memory1",
                                              memory_mb=524288)
            for each in range(2):
                self.add_to_ironic_node_store(node_id=str(uuid4()),
                                              instance_uuid=str(uuid4()))
        result = {
            "nodes": [
                node.brief_json() if not include_details
                else node.detail_json()
                for node in self.ironic_node_store
            ]
        }
        return dumps(result)

    def get_node_details(self, node_id):
        """
        Creates a node for the given `node_id` if one does not exist in
        ``self.ironic_node_store`` and returns it. Else returns the :obj: `Node` for the
        corresponding `node_id`.
        Docs: http://docs.openstack.org/developer/ironic/webapi/v1.html#get--v1-nodes-(node_ident)
        """
        if not self.node_by_id(node_id):
            self.add_to_ironic_node_store(node_id=node_id)
        return dumps(self.node_by_id(node_id).detail_json())

    def set_node_provision_state(self, http_put_request, node_id):
        """
        Sets the provision state on the node and returns 202.
        If the `node_id` does not exist returns 404.
        Docs: http://bit.ly/1ElELdU
        """
        content = loads(http_put_request.content.read())
        node = self.node_by_id(node_id)
        if node:
            node.provision_state = content.get('target', 'available')
            http_put_request.setResponseCode(202)
            return b''
        http_put_request.setResponseCode(404)
        return self.node_not_found(node_id)

    def cache_image_using_vendor_passthru(self, http_request, node_id, method):
        """
        Cache the image on the node.
        """
        content = loads(http_request.content.read())
        node = self.node_by_id(node_id)
        if not node:
            http_request.setResponseCode(404)
            return self.node_not_found(node_id)
        if method != 'cache_image':
            http_request.setResponseCode(400)
            return b''
        if content.get('image_info') and content['image_info'].get('id'):
            node.cache_image_id = content['image_info']['id']
            http_request.setResponseCode(202)
            return b''
        http_request.setResponseCode(400)
        return b''
