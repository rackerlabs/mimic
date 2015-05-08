"""
Model objects for the CLB mimic.
"""

from mimic.util.helper import (not_found_response, seconds_to_timestamp,
                               invalid_resource)
from twisted.python import log
from characteristic import attributes, Attribute
from mimic.canned_responses.loadbalancer import (load_balancer_example,
                                                 _verify_and_update_lb_state,
                                                 _lb_without_tenant,
                                                 _format_nodes_on_lb)


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

    def add_node(self, node_list, lb_id, current_timestamp):
        """
        Returns the canned response for add nodes
        """
        if lb_id in self.lbs:

            _verify_and_update_lb_state(self, lb_id, False, current_timestamp)

            if self.lbs[lb_id]["status"] != "ACTIVE":
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

                self.lbs[lb_id]["nodes"] = self.lbs[lb_id]["nodes"] + nodes
            else:
                self.lbs[lb_id]["nodes"] = nodes
                self.lbs[lb_id]["nodeCount"] = len(self.lbs[lb_id]["nodes"])
                _verify_and_update_lb_state(self, lb_id,
                                            current_timestamp=current_timestamp)
            return {"nodes": nodes}, 202

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
