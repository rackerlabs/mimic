"""
Model objects for the Nova mimic.
"""
from characteristic import attributes, Attribute
from uuid import uuid4
from json import loads, dumps

from mimic.util.helper import random_hex_generator


@attributes(["node_id",
             Attribute("chassis_uuid", default_value=None),
             Attribute("driver", default_value=None),
             Attribute("driver_info", default_value=None),
             Attribute("properties", default_value=None),
             Attribute("flavor_id", default_value="onmetal-io1"),
             Attribute("power_state", default_value="power on"),
             Attribute("provision_state", default_value="available"),
             Attribute("instance_uuid", default_value=None),
             Attribute("maintenance", default_value=False),
             Attribute("cache_image_id", default_value=None),
             Attribute("memory_mb", default_value=None),
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
            "chassis_uuid": self.chassis_uuid,
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
            "properties": self.properties or {
                "memory_mb": self.memory_mb,
                "cpu_arch": "amd64",
                "local_gb": 32,
                "cpus": 40
            },
            "driver": self.driver or "fake",
            "driver_info": self.driver_info or {
                "ipmi_username": "USERID",
                "ipmi_address": "127.0.0.0",
                "ipmi_password": "******",
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

    memory_to_flavor_map = {131072: "onmetal-io1",
                            32768: "onmetal-compute1",
                            524288: "onmetal-memory1"
                            }

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
        if not attributes.get('chassis_uuid'):
            attributes['chassis_uuid'] = str(uuid4())
        if (attributes.get("flavor_id", None) is None and
                attributes.get("memory_mb")):
            attributes['flavor_id'] = self.memory_to_flavor_map.get(
                attributes['memory_mb'], "onmetal-mimic")
        node = Node(**attributes)
        self.ironic_node_store.append(node)
        return node

    def create_node(self, http_create_request):
        """
        Create a node
        http://bit.ly/1N0O9KM
        """
        content = loads(http_create_request.content.read())
        try:
            memory_mb = None
            if content.get('properties'):
                memory_mb = content['properties'].get('memory_mb')
            node = self.add_to_ironic_node_store(
                node_id=str(uuid4()),
                memory_mb=memory_mb,
                chassis_uuid=content.get('chassis_uuid'),
                driver=content.get('driver'),
                properties=content.get('properties'),
                driver_info=content.get('driver_info'),
                name=content.get('name'))
            http_create_request.setResponseCode(201)
            return dumps(node.detail_json())
        except:
            http_create_request.setResponseCode(400)
            return b''

    def delete_node(self, http_delete_request, node_id):
        """
        Delete the `node_id` from the :obj:`ironic_node_store` if
        the node exists and set response code to be 204.
        If node does not exist, return response code 404.
        """
        node = self.node_by_id(node_id)
        if node:
            self.ironic_node_store.remove(node)
            http_delete_request.setResponseCode(204)
            return b''
        http_delete_request.setResponseCode(404)
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
            for _ in range(30):
                self.add_to_ironic_node_store(node_id=str(uuid4()),
                                              memory_mb=131072)
            for _ in range(30):
                self.add_to_ironic_node_store(node_id=str(uuid4()),
                                              memory_mb=32768)
            for _ in range(30):
                self.add_to_ironic_node_store(node_id=str(uuid4()),
                                              memory_mb=524288)
            for _ in range(2):
                self.add_to_ironic_node_store(node_id=str(uuid4()),
                                              memory_mb=32768,
                                              instance_uuid=str(uuid4()))
        result = {
            "nodes": [
                node.brief_json() if not include_details
                else node.detail_json()
                for node in self.ironic_node_store
            ]
        }
        return dumps(result)

    def get_node_details(self, http_request, node_id):
        """
        Returns the :obj: `Node` for the corresponding `node_id`
        from the :obj:`ironic_node_store`.
        Returns 404 if `node_id` one does not exist in
        ``self.ironic_node_store``
        Docs:http://bit.ly/1NMIlGx
        """
        if not self.node_by_id(node_id):
            http_request.setResponseCode(404)
            return b''
        return dumps(self.node_by_id(node_id).detail_json())

    def set_node_provision_state(self, http_put_request, node_id):
        """
        Sets the provision state on the node and returns 202.
        If the `node_id` does not exist returns 404.
        Note: When the provision_state is set to `provide` the
        node is made 'available'.
        Docs: http://bit.ly/1ElELdU
        """
        content = loads(http_put_request.content.read())
        node = self.node_by_id(node_id)
        if node:
            http_put_request.setResponseCode(202)
            node.provision_state = content.get('target', 'available')
            if node.provision_state == 'provide':
                node.provision_state = 'available'
            if node.provision_state != 'active':
                node.instance_uuid = None
                node.cache_image_id = None
            if node.provision_state == 'active':
                node.instance_uuid = str(uuid4())
            return dumps(b'')
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
            return dumps(b'')
        http_request.setResponseCode(400)
        return b''
