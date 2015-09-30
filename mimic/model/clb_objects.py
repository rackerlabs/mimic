"""
Model objects for the CLB mimic.  Please see the `Rackspace Cloud Load
Balancer API docs
<http://docs.rackspace.com/loadbalancers/api/v1.0/clb-devguide/content/API_Operations.html>`
 for more information.
"""
from copy import deepcopy
from random import randrange

import attr

from characteristic import attributes, Attribute

from six import string_types

from toolz.dicttoolz import dissoc

from twisted.internet.interfaces import IReactorTime
from twisted.python import log

from mimic.canned_responses.loadbalancer import load_balancer_example
from mimic.model.clb_errors import (
    considered_immutable_error,
    invalid_json_schema,
    loadbalancer_not_found,
    lb_deleted_xml,
    node_not_found,
    not_found_xml,
    updating_node_validation_error
)
from mimic.util.helper import (EMPTY_RESPONSE,
                               invalid_resource,
                               not_found_response,
                               seconds_to_timestamp,
                               set_resource_status)


def _one_of_validator(*items):
    """
    Return an :mod:`attr` validator which raises a :class:`TypeError`
    if the value is not equivalent to one of the provided items.

    :param items: Items to compare against
    :return: a callable that returns with None or raises :class:`TypeError`
    """
    def validate(inst, attribute, value):
        if value not in items:
            raise TypeError("{0} must be one of {1}".format(
                attribute.name, items))
    return validate


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
    type = attr.ib(validator=_one_of_validator("PRIMARY", "SECONDARY"),
                   default="PRIMARY")
    weight = attr.ib(validator=attr.validators.instance_of(int), default=1)
    condition = attr.ib(
        validator=_one_of_validator("ENABLED", "DISABLED", "DRAINING"),
        default="ENABLED")
    id = attr.ib(validator=attr.validators.instance_of(int),
                 default=attr.Factory(lambda: randrange(999999)))
    status = attr.ib(validator=attr.validators.instance_of(str),
                     default="ONLINE")
    feed_events = attr.ib(default=[])

    @classmethod
    def from_json(cls, json_blob):
        """
        Create a new node from JSON.

        :param dict json_blob: the JSON dictionary containing node information

        :return: a :class:`Node` object
        :raises: :class:`TypeError` or :class:`ValueError` if the values
            are incorrect.
        """
        # status cannot be in the JSON
        if "status" in json_blob:
            raise ValueError("'status' not allowed in the JSON")

        json_blob['port'] = int(json_blob['port'])
        return Node(**json_blob)

    def as_json(self):
        """
        :return: a JSON dictionary representing the node.
        """
        return dissoc(attr.asdict(self), "feed_events")

    def same_as(self, other):
        """
        :return: `True` if the other node has the same IP address and port
            as this node (but compares nothing else), `False` otherwise.
        """
        return self.address == other.address and self.port == other.port


@attr.s
class CLB(object):
    """
    An object representing a load balancer.  Currently just takes the JSON
    as an attribute, and provides __getitem__ and __setitem__ to access it.

    These should be moved to real attributes as soon as possible.
    """
    _json = attr.ib()
    nodes = attr.ib(default=attr.Factory(list))

    def __getitem__(self, key):
        """
        Convenience function during the full conversion to the object model
        to access JSON keys.
        """
        return self._json[key]

    def __setitem__(self, key, value):
        """
        Convenience function during the full conversion to the object model
        to set JSON keys.
        """
        self._json[key] = value

    def update(self, new_json_dict):
        """
        Convenience function during the full conversion to the object model
        to update all JSON keys.
        """
        self._json.update(new_json_dict)

    def short_json(self):
        """
        :return: a short JSON dict representation of this object to be used
        when listing load balancers.  Does not include the node list, but does
        include a "nodeCount" attribute, even if there are no nodes.
        """
        entries = ('name', 'protocol', 'id', 'port', 'algorithm', 'status',
                   'timeout', 'created', 'virtualIps', 'updated')
        result = dict((entry, self._json[entry]) for entry in entries)
        result['nodeCount'] = len(self.nodes)
        return result

    def full_json(self):
        """
        :return: a longer, detailed JSON dict reprentation of this object that
        includes all the nodes, if there are any present.  Does not include
        a "nodeCount" attribute.
        """
        result = deepcopy(self._json)
        if len(self.nodes) > 0:
            result["nodes"] = [node.as_json() for node in self.nodes]
        return result


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


def node_feed_xml(events):
    """
    Return feed of node events
    """
    feed = '<feed xmlns="http://www.w3.org/2005/Atom">{entries}</feed>'
    entry = ('<entry><summary>{summary}</summary>'
             '<updated>{updated}</updated></entry>')
    entries = [entry.format(summary=summary, updated=updated)
               for summary, updated in events]
    return feed.format(entries=''.join(entries))


@attr.s
class RegionalCLBCollection(object):
    """
    A collection of CloudLoadBalancers, in a given region, for a given tenant.
    """
    clock = attr.ib(validator=attr.validators.provides(IReactorTime))
    node_limit = attr.ib(default=25,
                         validator=attr.validators.instance_of(int))
    lbs = attr.ib(default=attr.Factory(dict))
    meta = attr.ib(default=attr.Factory(dict))

    def lb_in_region(self, clb_id):
        """
        Returns true if the CLB ID is registered with our list of load
        balancers.
        """
        return clb_id in self.lbs

    def add_load_balancer(self, lb_info, lb_id):
        """
        Returns response of a newly created load balancer with
        response code 202, and adds the new lb to the store's lbs.
        :param dict lb_info: Configuration for the load balancer.  See
            Openstack docs for creating CLBs.
        :param string lb_id: Unique ID for this load balancer.
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

        current_timestring = seconds_to_timestamp(self.clock.seconds())
        self.lbs[lb_id] = CLB(load_balancer_example(lb_info, lb_id, status,
                                                    current_timestring),
                              nodes=[Node.from_json(blob)
                                     for blob in lb_info.get("nodes", [])])

        return {'loadBalancer': self.lbs[lb_id].full_json()}, 202

    def _verify_and_update_lb_state(self, lb_id, set_state=True,
                                    current_timestamp=None):
        """
        Based on the current state, the metadata on the lb and the time since the LB has
        been in that state, set the appropriate state in self.lbs
        Note: Reconsider if update metadata is implemented
        """
        current_timestring = seconds_to_timestamp(current_timestamp)
        if self.lbs[lb_id]["status"] == "BUILD":
            self.meta[lb_id]["lb_building"] = self.meta[lb_id]["lb_building"] or 10
            self.lbs[lb_id]["status"] = set_resource_status(
                self.lbs[lb_id]["updated"]["time"],
                self.meta[lb_id]["lb_building"],
                current_timestamp=current_timestamp
            ) or "BUILD"

        elif self.lbs[lb_id]["status"] == "ACTIVE" and set_state:
            if "lb_pending_update" in self.meta[lb_id]:
                self.lbs[lb_id]["status"] = "PENDING-UPDATE"
                log.msg(self.lbs[lb_id]["status"])
            if "lb_pending_delete" in self.meta[lb_id]:
                self.lbs[lb_id]["status"] = "PENDING-DELETE"
            if "lb_error_state" in self.meta[lb_id]:
                self.lbs[lb_id]["status"] = "ERROR"
            self.lbs[lb_id]["updated"]["time"] = current_timestring

        elif self.lbs[lb_id]["status"] == "PENDING-UPDATE":
            if "lb_pending_update" in self.meta[lb_id]:
                self.lbs[lb_id]["status"] = set_resource_status(
                    self.lbs[lb_id]["updated"]["time"],
                    self.meta[lb_id]["lb_pending_update"],
                    current_timestamp=current_timestamp
                ) or "PENDING-UPDATE"

        elif self.lbs[lb_id]["status"] == "PENDING-DELETE":
            self.meta[lb_id]["lb_pending_delete"] = self.meta[lb_id]["lb_pending_delete"] or 10
            self.lbs[lb_id]["status"] = set_resource_status(
                self.lbs[lb_id]["updated"]["time"],
                self.meta[lb_id]["lb_pending_delete"], "DELETED",
                current_timestamp=current_timestamp
            ) or "PENDING-DELETE"
            self.lbs[lb_id]["updated"]["time"] = current_timestring

        elif self.lbs[lb_id]["status"] == "DELETED":
            # see del_load_balancer above for an explanation of this state change.
            self.lbs[lb_id]["status"] = set_resource_status(
                self.lbs[lb_id]["updated"]["time"], 3600, "DELETING-NOW",
                current_timestamp=current_timestamp
            ) or "DELETED"
            if self.lbs[lb_id]["status"] == "DELETING-NOW":
                del self.lbs[lb_id]

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

    def get_load_balancers(self, lb_id):
        """
        Returns the load balancers with the given lb id, with response
        code 200. If no load balancers are found returns 404.
        """
        if lb_id in self.lbs:
            self._verify_and_update_lb_state(lb_id, False, self.clock.seconds())
            log.msg(self.lbs[lb_id]["status"])
            return {'loadBalancer': self.lbs[lb_id].full_json()}, 200
        return not_found_response("loadbalancer"), 404

    def get_node(self, lb_id, node_id):
        """
        Returns the node on the load balancer
        """
        if lb_id in self.lbs:
            self._verify_and_update_lb_state(lb_id, False, self.clock.seconds())

            if self.lbs[lb_id]["status"] == "DELETED":
                return (
                    invalid_resource(
                        "The loadbalancer is marked as deleted.", 410),
                    410)

            for each in self.lbs[lb_id].nodes:
                if node_id == each.id:
                    return {"node": each.as_json()}, 200

            return not_found_response("node"), 404

        return not_found_response("loadbalancer"), 404

    def get_node_feed(self, lb_id, node_id):
        """
        Return load balancer's node's atom feed
        """
        if lb_id not in self.lbs:
            return not_found_xml("Load balancer")

        self._verify_and_update_lb_state(lb_id, False, self.clock.seconds())

        if self.lbs[lb_id]["status"] == "DELETED":
            return lb_deleted_xml()

        for node in self.lbs[lb_id].nodes:
            if node_id == node.id:
                return node_feed_xml(node.feed_events), 200

        return not_found_xml("Node")

    def list_load_balancers(self):
        """
        Returns the list of load balancers with the given tenant id with response
        code 200. If no load balancers are found returns empty list.

        :return: A 2-tuple, containing the HTTP response and code, in that order.
        """
        for lb_id in self.lbs:
            self._verify_and_update_lb_state(lb_id, False, self.clock.seconds())
            log.msg(self.lbs[lb_id]["status"])
        return (
            {'loadBalancers': [lb.short_json() for lb in self.lbs.values()]},
            200)

    def list_nodes(self, lb_id):
        """
        Returns the list of nodes remaining on the load balancer
        """
        if lb_id in self.lbs:
            self._verify_and_update_lb_state(lb_id, False, self.clock.seconds())
            if lb_id not in self.lbs:
                return not_found_response("loadbalancer"), 404

            if self.lbs[lb_id]["status"] == "DELETED":
                return invalid_resource("The loadbalancer is marked as deleted.", 410), 410

            node_list = [node.as_json()
                         for node in self.lbs[lb_id].nodes]

            return {"nodes": node_list}, 200
        else:
            return not_found_response("loadbalancer"), 404

    def _delete_node(self, lb_id, node_id):
        """
        Deletes a node by ID.
        """
        if self.lbs[lb_id].nodes:
            previous_size = len(self.lbs[lb_id].nodes)
            self.lbs[lb_id].nodes[:] = [node
                                        for node in self.lbs[lb_id].nodes
                                        if node.id != node_id]
            return len(self.lbs[lb_id].nodes) < previous_size
        return False

    def delete_node(self, lb_id, node_id):
        """
        Determines whether the node to be deleted exists in the session store,
        deletes the node, and returns the response code.
        """
        current_timestamp = self.clock.seconds()
        if lb_id in self.lbs:

            self._verify_and_update_lb_state(lb_id, False, current_timestamp)

            if self.lbs[lb_id]["status"] != "ACTIVE":
                # Error message verified as of 2015-04-22
                return considered_immutable_error(
                    self.lbs[lb_id]["status"], lb_id)

            self._verify_and_update_lb_state(
                lb_id, current_timestamp=current_timestamp)

            if self._delete_node(lb_id, node_id):
                return None, 202
            else:
                return not_found_response("node"), 404

        return not_found_response("loadbalancer"), 404

    def delete_nodes(self, lb_id, node_ids):
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

        current_timestamp = self.clock.seconds()
        self._verify_and_update_lb_state(lb_id, False, current_timestamp)

        if self.lbs[lb_id]["status"] != "ACTIVE":
            # Error message verified as of 2015-04-22
            resp = {"message": "LoadBalancer is not ACTIVE",
                    "code": 422}
            return resp, 422

        # We need to verify all the deletions up front, and only allow it through
        # if all of them are valid.
        all_ids = [node.id for node in self.lbs[lb_id].nodes]
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
            assert self._delete_node(lb_id, node_id) is True

        self._verify_and_update_lb_state(
            lb_id, current_timestamp=current_timestamp)
        return EMPTY_RESPONSE, 202

    def add_node(self, node_list, lb_id):
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
            current_timestamp = self.clock.seconds()
            self._verify_and_update_lb_state(lb_id, False, current_timestamp)

            if self.lbs[lb_id]["status"] != "ACTIVE":
                return considered_immutable_error(
                    self.lbs[lb_id]["status"], lb_id)

            nodes = [Node.from_json(blob) for blob in node_list]

            for existing_node in self.lbs[lb_id].nodes:
                for new_node in nodes:
                    if existing_node.same_as(new_node):
                        resource = invalid_resource(
                            "Duplicate nodes detected. One or more nodes "
                            "already configured on load balancer.", 413)
                        return (resource, 413)

            # If there were no duplicates
            new_nodeCount = len(self.lbs[lb_id].nodes) + len(nodes)
            if new_nodeCount <= self.node_limit:
                self.lbs[lb_id].nodes = self.lbs[lb_id].nodes + nodes
            else:
                resource = invalid_resource(
                    "Nodes must not exceed {0} "
                    "per load balancer.".format(self.node_limit), 413)
                return (resource, 413)

            self._verify_and_update_lb_state(
                lb_id, current_timestamp=current_timestamp)
            return {"nodes": [node.as_json() for node in nodes]}, 202

        return not_found_response("loadbalancer"), 404

    def update_node(self, lb_id, node_id, node_updates):
        """
        Update the weight, condition, or type of a single node.  The IP, port,
        status, and ID are immutable, and attempting to change them will cause
        a 400 response to be returned.

        All success and error behavior verified as of 2016-06-16.

        :param str lb_id: the load balancer ID
        :param str node_id: the node ID to update
        :param dict node_updates: The JSON dictionary containing node
            attributes to update
        :param current_timestamp: What the current time is

        :return: a `tuple` of (json response as a dict, http status code)
        """
        feed_summary = (
            "Node successfully updated with address: '{address}', port: '{port}', "
            "weight: '{weight}', condition: '{condition}'")
        # first, store whether address and port were provided - if they were
        # that's a validation error not a schema error
        things_wrong = dict([(k, True) for k in ("address", "port", "id")
                             if k in node_updates])
        node_updates = dict([(k, v) for k, v in node_updates.items()
                             if k not in ("address", "port")])
        # use the Node.from_json to check the schema
        try:
            Node.from_json(dict(address="1.1.1.1", port=80, **node_updates))
        except (TypeError, ValueError):
            return invalid_json_schema()

        # handle the possible validation (as opposed to schema) errors
        if not 1 <= node_updates.get('weight', 1) <= 100:
            things_wrong["weight"] = True
        if things_wrong:
            return updating_node_validation_error(**things_wrong)

        # Now, finally, check if the LB exists and node exists
        if lb_id in self.lbs:
            self._verify_and_update_lb_state(lb_id, False, self.clock.seconds())

            if self.lbs[lb_id]["status"] != "ACTIVE":
                return considered_immutable_error(
                    self.lbs[lb_id]["status"], lb_id)

            for i, node in enumerate(self.lbs[lb_id].nodes):
                if node.id == node_id:
                    params = attr.asdict(node)
                    params.update(node_updates)
                    self.lbs[lb_id].nodes[i] = Node(**params)
                    self.lbs[lb_id].nodes[i].feed_events.append(
                        (feed_summary.format(**params),
                         seconds_to_timestamp(self.clock.seconds())))
                    return ("", 202)

            return node_not_found()

        return loadbalancer_not_found()

    def del_load_balancer(self, lb_id):
        """
        Returns response for a load balancer
         is in building status for 20
        seconds and response code 202, and adds the new lb to ``self.lbs``.
        A loadbalancer, on delete, goes into PENDING-DELETE and remains in DELETED
        status until a nightly job(maybe?)
        """
        if lb_id in self.lbs:
            current_timestamp = self.clock.seconds()

            if self.lbs[lb_id]["status"] == "PENDING-DELETE":
                msg = ("Must provide valid load balancers: {0} are immutable and "
                       "could not be processed.".format(lb_id))
                # Dont doubt this to be 422, it is 400!
                return invalid_resource(msg, 400), 400

            self._verify_and_update_lb_state(lb_id, True, current_timestamp)

            if any([self.lbs[lb_id]["status"] == "ACTIVE",
                    self.lbs[lb_id]["status"] == "ERROR",
                    self.lbs[lb_id]["status"] == "PENDING-UPDATE"]):
                del self.lbs[lb_id]
                return EMPTY_RESPONSE, 202

            if self.lbs[lb_id]["status"] == "PENDING-DELETE":
                return EMPTY_RESPONSE, 202

            if self.lbs[lb_id]["status"] == "DELETED":
                self._verify_and_update_lb_state(
                    lb_id, current_timestamp=current_timestamp)
                msg = "Must provide valid load balancers: {0} could not be found.".format(lb_id)
                # Dont doubt this to be 422, it is 400!
                return invalid_resource(msg, 400), 400

        return not_found_response("loadbalancer"), 404


@attributes(["clock",
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
                RegionalCLBCollection(self.clock)
            )
        return self.regional_collections[region_name]
