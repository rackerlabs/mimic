"""
Model objects for the CLB mimic.
"""

from mimic.util.helper import (not_found_response, seconds_to_timestamp,
                               EMPTY_RESPONSE,
                               invalid_resource)
from twisted.python import log
from characteristic import attributes, Attribute
from mimic.canned_responses.loadbalancer import (load_balancer_example,
                                                 _verify_and_update_lb_state,
                                                 _lb_without_tenant,
                                                 _format_nodes_on_lb,
                                                 _delete_node)


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
        self.lbs[lb_id].update(
            {"nodeCount": len(self.lbs[lb_id].get("nodes", []))})

        # and remove before returning response for add lb
        new_lb = _lb_without_tenant(self, lb_id)

        return {'loadBalancer': new_lb}, 202

    def set_attributes(self, lb_id, kvpairs):
        """
        Sets zero or more attributes on the load balancer object.
        Currently supported attributes include: status.
        :param lb_id: The ID of the load balancer to change.
        :param dict kvpairs: A dictionary with keys corresponding to load
            balancer attributes and the values to a replacement value.
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

            if self.lbs[lb_id].get("nodes"):
                for each in self.lbs[lb_id]["nodes"]:
                    if node_id == each["id"]:
                        return {"node": each}, 200
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
            node_list = []
            if self.lbs[lb_id].get("nodes"):
                node_list = self.lbs[lb_id]["nodes"]
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
                resource = invalid_resource(
                    "Load Balancer '{0}' has a status of '{1}' and is considered "
                    "immutable.".format(lb_id, self.lbs[lb_id]["status"]), 422)
                return (resource, 422)

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
        all_ids = [node["id"] for node in self.lbs[lb_id].get("nodes", [])]
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
        Returns the canned response for add nodes
        """
        if lb_id in self.lbs:

            _verify_and_update_lb_state(self, lb_id, False, current_timestamp)

            if self.lbs[lb_id]["status"] != "ACTIVE":
                if ((self.lbs[lb_id]["status"] == "ERROR") and
                        ("error_response" in self.lbs[lb_id])):

                    err_resp = self.lbs[lb_id]["error_response"]
                    resource = invalid_resource(err_resp["message"],
                                                err_resp["code"])
                    return (resource, err_resp["code"])

                resource = invalid_resource(
                    "Load Balancer '{0}' has a status of {1} and is considered "
                    "immutable.".format(lb_id, self.lbs[lb_id]["status"]), 422)
                return (resource, 422)

            nodes = _format_nodes_on_lb(node_list)

            if self.lbs[lb_id].get("nodes"):
                for existing_node in self.lbs[lb_id]["nodes"]:
                    for new_node in node_list:
                        if (existing_node["address"] == new_node["address"] and
                                existing_node["port"] == new_node["port"]):
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
            else:
                self.lbs[lb_id]["nodes"] = nodes
                self.lbs[lb_id]["nodeCount"] = len(self.lbs[lb_id]["nodes"])
                _verify_and_update_lb_state(self, lb_id,
                                            current_timestamp=current_timestamp)
            return {"nodes": nodes}, 202

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
