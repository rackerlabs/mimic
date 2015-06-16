"""
Model objects for the CLB mimic.  Please see the `Rackspace Cloud Load
Balancer API docs
<http://docs.rackspace.com/loadbalancers/api/v1.0/clb-devguide/content/API_Operations.html>`
 for more information.
"""
from random import randrange

import attr

from characteristic import attributes, Attribute

from six import string_types

from twisted.python import log

from mimic.canned_responses.loadbalancer import (load_balancer_example,
                                                 _verify_and_update_lb_state,
                                                 _lb_without_tenant,
                                                 _delete_node)
from mimic.model.clb_errors import considered_immutable_error
from mimic.util.helper import (not_found_response, seconds_to_timestamp,
                               EMPTY_RESPONSE,
                               invalid_resource)


@attr.s
class Node(object):
    """
    An object representing a CLB node, which is a unique combination of
    IP-address and port.  Please see section 4.4 (Nodes) of the CLB
    documentation for more information.

    :ivar int id: The ID of the node
    :ivar str address: The IP address of the node
    :ivar int port: The port of the node
    :ivar str type: One of (PRIMARY, SECONDARY).  Defaults to PRIMARY.
    :ivar int weight: Between 1 and 100 inclusive.  Defaults to 1.
    :ivar str condition: One of (ENABLED, DISABLED, DRAINING).  Defaults to
    :ivar str status: "Online"
        ENABLED.
    """
    address = attr.ib(validator=attr.validators.instance_of(string_types))
    port = attr.ib(validator=attr.validators.instance_of(int))
    type = attr.ib(validator=lambda _1, _2, t: t in ("PRIMARY", "SECONDARY"),
                   default="PRIMARY")
    weight = attr.ib(validator=lambda _1, _2, w: 1 <= w <= 100, default=1)
    condition = attr.ib(
        validator=lambda _1, _2, c: c in ("ENABLED", "DISABLED", "DRAINING"),
        default="ENABLED")
    id = attr.ib(validator=attr.validators.instance_of(int),
                 default=attr.Factory(lambda: randrange(999999)))
    status = attr.ib(validator=attr.validators.instance_of(str),
                     default="ONLINE")

    @classmethod
    def from_json(cls, json_blob, old_node=None):
        """
        Create a new node from JSON.

        :param dict json_blob: the JSON dictionary containing node information
        :param old_node: If provided, will return a new node containing all
            the information from the old node, updated with the given JSON
            information.

        :return: a :class:`Node` object
        :raises: :class:`TypeError` or :class:`ValueError` if the values
            are incorrect.
        """
        json_blob['port'] = int(json_blob['port'])
        if 'weight' in json_blob:
            json_blob['weight'] = int(json_blob['weight'])

        params = json_blob
        if old_node is not None:
            params = attr.asdict(old_node)
            params.update(json_blob)

        return Node(**params)

    def as_json(self):
        """
        :return: a JSON dictionary representing the node.
        """
        return attr.asdict(self)

    def same_as(self, other):
        """
        :return: `True` if the other node has the same IP address and port
            as this node (but compares nothing else), `False` otherwise.
        """
        return self.address == other.address and self.port == other.port


@attributes(["keys"])
class BadKeysError(Exception):
    """
    When trying to alter the settings of a load balancer, this exception will
    be raised if you attempt to alter an attribute which doesn't exist.
    """


@attributes(["value", "accepted_values"])
class BadValueError(Exception):
    """
    When trying to alter the settings of a load balancer, this exception will
    be raised if you attempt to set a valid attribute to an invalid setting.
    """


def _prep_for_list(lb_list):
    """
    Removes tenant id and changes the nodes list to 'nodeCount' set to the
    number of node on the LB
    """
    entries_to_keep = ('name', 'protocol', 'id', 'port', 'algorithm', 'status', 'timeout',
                       'created', 'virtualIps', 'updated', 'nodeCount')
    filtered_lb_list = []
    for each in lb_list:
        filtered_lb_list.append(
            dict((entry, each[entry]) for entry in entries_to_keep)
        )
    return filtered_lb_list


class RegionalCLBCollection(object):
    """
    A collection of CloudLoadBalancers, in a given region, for a given tenant.
    """
    def __init__(self):
        """
        There are two stores - the lb info, and the metadata info
        """
        self.lbs = {}
        self.meta = {}
        self.node_limit = 25

    def lb_in_region(self, clb_id):
        """
        Returns true if the CLB ID is registered with our list of load
        balancers.
        """
        return clb_id in self.lbs

    def add_load_balancer(self, tenant_id, lb_info, lb_id, current_timestamp):
        """
        Returns response of a newly created load balancer with
        response code 202, and adds the new lb to the store's lbs.
        Note: ``store.lbs`` has tenant_id added as an extra key in comparison
        to the lb_example.
        :param string tenant_id: Tenant ID who will own this load balancer.
        :param dict lb_info: Configuration for the load balancer.  See
            Openstack docs for creating CLBs.
        :param string lb_id: Unique ID for this load balancer.
        :param float current_timestamp: The time since epoch when the CLB is
            created, measured in seconds.
        """
        status = "ACTIVE"

        # Loadbalancers metadata is a list object, creating a metadata store
        # so we dont have to deal with the list
        meta = {}
        if "metadata" in lb_info:
            for each in lb_info["metadata"]:
                meta.update({each["key"]: each["value"]})
        self.meta[lb_id] = meta
        log.msg(self.meta)

        if "lb_building" in self.meta[lb_id]:
            status = "BUILD"

        # Add tenant_id and nodeCount to self.lbs
        current_timestring = seconds_to_timestamp(current_timestamp)
        self.lbs[lb_id] = load_balancer_example(lb_info, lb_id, status,
                                                current_timestring)
        self.lbs[lb_id].update({"tenant_id": tenant_id})
        self.lbs[lb_id]["nodes"] = [
            Node.from_json(blob) for blob in lb_info.get("nodes", [])]

        self.lbs[lb_id].update({"nodeCount": len(self.lbs[lb_id]["nodes"])})

        # and remove before returning response for add lb
        new_lb = _lb_without_tenant(self, lb_id)

        return {'loadBalancer': new_lb}, 202

    def set_attributes(self, lb_id, kvpairs):
        """
        Sets zero or more attributes on the load balancer object.
        Currently supported attributes include: status.
        """
        supported_keys = ["status"]
        badKeys = []
        for k in kvpairs:
            if k not in supported_keys:
                badKeys.append(k)
        if len(badKeys) > 0:
            raise BadKeysError("Attempt to alter a bad attribute", keys=badKeys)

        if "status" in kvpairs:
            supported_statuses = [
                "ACTIVE", "ERROR", "PENDING_DELETE", "PENDING_UPDATE"
            ]
            s = kvpairs["status"]
            if s not in supported_statuses:
                raise BadValueError(
                    "Unsupported status {0} not one of {1}".format(
                        s, supported_statuses
                    ),
                    value=s, accepted_values=supported_statuses
                )

        self.lbs[lb_id].update(kvpairs)

    def get_load_balancers(self, lb_id, current_timestamp):
        """
        Returns the load balancers with the given lb id, with response
        code 200. If no load balancers are found returns 404.
        """
        if lb_id in self.lbs:
            _verify_and_update_lb_state(self, lb_id, False, current_timestamp)
            log.msg(self.lbs[lb_id]["status"])
            new_lb = _lb_without_tenant(self, lb_id)
            return {'loadBalancer': new_lb}, 200
        return not_found_response("loadbalancer"), 404

    def get_nodes(self, lb_id, node_id, current_timestamp):
        """
        Returns the node on the load balancer
        """
        if lb_id in self.lbs:
            _verify_and_update_lb_state(self, lb_id, False, current_timestamp)

            if self.lbs[lb_id]["status"] == "DELETED":
                return (
                    invalid_resource(
                        "The loadbalancer is marked as deleted.", 410),
                    410)

            for each in self.lbs[lb_id]["nodes"]:
                if node_id == each.id:
                    return {"node": each.as_json()}, 200

            return not_found_response("node"), 404

        return not_found_response("loadbalancer"), 404

    def list_load_balancers(self, tenant_id, current_timestamp):
        """
        Returns the list of load balancers with the given tenant id with response
        code 200. If no load balancers are found returns empty list.
        :param string tenant_id: The tenant which owns the load balancers.
        :param float current_timestamp: The current time, in seconds since epoch.

        :return: A 2-tuple, containing the HTTP response and code, in that order.
        """
        response = dict(
            (k, v) for (k, v) in self.lbs.items()
            if tenant_id == v['tenant_id']
        )
        for each in response:
            _verify_and_update_lb_state(self, each, False, current_timestamp)
            log.msg(self.lbs[each]["status"])
        updated_resp = dict(
            (k, v) for (k, v) in self.lbs.items()
            if tenant_id == v['tenant_id']
        )
        return {'loadBalancers': _prep_for_list(updated_resp.values()) or []}, 200

    def list_nodes(self, lb_id, current_timestamp):
        """
        Returns the list of nodes remaining on the load balancer
        """
        if lb_id in self.lbs:
            _verify_and_update_lb_state(self, lb_id, False, current_timestamp)
            if lb_id not in self.lbs:
                return not_found_response("loadbalancer"), 404

            if self.lbs[lb_id]["status"] == "DELETED":
                return invalid_resource("The loadbalancer is marked as deleted.", 410), 410

            node_list = [node.as_json()
                         for node in self.lbs[lb_id]["nodes"]]

            return {"nodes": node_list}, 200
        else:
            return not_found_response("loadbalancer"), 404

    def delete_node(self, lb_id, node_id, current_timestamp):
        """
        Determines whether the node to be deleted exists in the session store,
        deletes the node, and returns the response code.
        """
        if lb_id in self.lbs:

            _verify_and_update_lb_state(self, lb_id, False, current_timestamp)

            if self.lbs[lb_id]["status"] != "ACTIVE":
                # Error message verified as of 2015-04-22
                return considered_immutable_error(
                    self.lbs[lb_id]["status"], lb_id)

            _verify_and_update_lb_state(self, lb_id,
                                        current_timestamp=current_timestamp)

            if _delete_node(self, lb_id, node_id):
                return None, 202
            else:
                return not_found_response("node"), 404

        return not_found_response("loadbalancer"), 404

    def delete_nodes(self, lb_id, node_ids, current_timestamp):
        """
        Bulk-delete multiple LB nodes.
        """
        if not node_ids:
            resp = {
                "message": "Must supply one or more id's to process this request.",
                "code": 400}
            return resp, 400

        if lb_id not in self.lbs:
            return not_found_response("loadbalancer"), 404

        _verify_and_update_lb_state(self, lb_id, False, current_timestamp)

        if self.lbs[lb_id]["status"] != "ACTIVE":
            # Error message verified as of 2015-04-22
            resp = {"message": "LoadBalancer is not ACTIVE",
                    "code": 422}
            return resp, 422

        # We need to verify all the deletions up front, and only allow it through
        # if all of them are valid.
        all_ids = [node.id for node in self.lbs[lb_id].get("nodes", [])]
        non_nodes = set(node_ids).difference(all_ids)
        if non_nodes:
            nodes = ','.join(map(str, non_nodes))
            resp = {
                "validationErrors": {
                    "messages": [
                        "Node ids {0} are not a part of your loadbalancer".format(nodes)
                    ]
                },
                "message": "Validation Failure",
                "code": 400,
                "details": "The object is not valid"}
            return resp, 400

        for node_id in node_ids:
            # It should not be possible for this to fail, since we've already
            # checked that they all exist.
            assert _delete_node(self, lb_id, node_id) is True

        _verify_and_update_lb_state(self, lb_id,
                                    current_timestamp=current_timestamp)
        return EMPTY_RESPONSE, 202

    def add_node(self, node_list, lb_id, current_timestamp):
        """
        Add one or more nodes to a load balancer.  Fails if one or more of the
        nodes provided has the same address/port as an existing node.  Also
        fails if adding the nodes would exceed the maximum number of nodes on
        the CLB.

        :param list node_list: a `list` of `dict` containing specification for
            nodes

        :return: a `tuple` of (json response as a dict, http status code)
        """
        if lb_id in self.lbs:

            _verify_and_update_lb_state(self, lb_id, False, current_timestamp)

            if self.lbs[lb_id]["status"] != "ACTIVE":
                return considered_immutable_error(
                    self.lbs[lb_id]["status"], lb_id)

            nodes = [Node.from_json(blob) for blob in node_list]

            for existing_node in self.lbs[lb_id]["nodes"]:
                for new_node in nodes:
                    if existing_node.same_as(new_node):
                        resource = invalid_resource(
                            "Duplicate nodes detected. One or more nodes "
                            "already configured on load balancer.", 413)
                        return (resource, 413)

            # If there were no duplicates
            new_nodeCount = self.lbs[lb_id]["nodeCount"] + len(nodes)
            if new_nodeCount <= self.node_limit:
                self.lbs[lb_id]["nodes"] = self.lbs[lb_id]["nodes"] + nodes
                self.lbs[lb_id]["nodeCount"] = new_nodeCount
            else:
                resource = invalid_resource(
                    "Nodes must not exceed {0} "
                    "per load balancer.".format(self.node_limit), 413)
                return (resource, 413)

            _verify_and_update_lb_state(self, lb_id,
                                        current_timestamp=current_timestamp)
            return {"nodes": [node.as_json() for node in nodes]}, 202

        return not_found_response("loadbalancer"), 404

    def del_load_balancer(self, lb_id, current_timestamp):
        """
        Returns response for a load balancer
         is in building status for 20
        seconds and response code 202, and adds the new lb to ``self.lbs``.
        A loadbalancer, on delete, goes into PENDING-DELETE and remains in DELETED
        status until a nightly job(maybe?)
        """
        if lb_id in self.lbs:

            if self.lbs[lb_id]["status"] == "PENDING-DELETE":
                msg = ("Must provide valid load balancers: {0} are immutable and "
                       "could not be processed.".format(lb_id))
                # Dont doubt this to be 422, it is 400!
                return invalid_resource(msg, 400), 400

            _verify_and_update_lb_state(self, lb_id, True, current_timestamp)

            if any([self.lbs[lb_id]["status"] == "ACTIVE",
                    self.lbs[lb_id]["status"] == "ERROR",
                    self.lbs[lb_id]["status"] == "PENDING-UPDATE"]):
                del self.lbs[lb_id]
                return EMPTY_RESPONSE, 202

            if self.lbs[lb_id]["status"] == "PENDING-DELETE":
                return EMPTY_RESPONSE, 202

            if self.lbs[lb_id]["status"] == "DELETED":
                _verify_and_update_lb_state(self, lb_id,
                                            current_timestamp=current_timestamp)
                msg = "Must provide valid load balancers: {0} could not be found.".format(lb_id)
                # Dont doubt this to be 422, it is 400!
                return invalid_resource(msg, 400), 400

        return not_found_response("loadbalancer"), 404


@attributes(["tenant_id", "clock",
             Attribute("regional_collections", default_factory=dict)])
class GlobalCLBCollections(object):
    """
    A :obj:`GlobalCLBCollections` is a set of all the
    :obj:`RegionalCLBCollection` objects owned by a given tenant.  In other
    words, all the objects that a single tenant owns globally in a
    cloud load balancer service.
    """

    def collection_for_region(self, region_name):
        """
        Get a :obj:`RegionalCLBCollection` for the region identified by the
        given name.
        """
        if region_name not in self.regional_collections:
            self.regional_collections[region_name] = (
                RegionalCLBCollection()
            )
        return self.regional_collections[region_name]
