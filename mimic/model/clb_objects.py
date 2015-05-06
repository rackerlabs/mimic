"""
Model objects for the CLB mimic.
"""

from copy import deepcopy
from mimic.util.helper import (seconds_to_timestamp, not_found_response,
                               set_resource_status)
from twisted.python import log
from characteristic import attributes, Attribute
from mimic.canned_responses.loadbalancer import load_balancer_example


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


def _lb_without_tenant(store, lb_id):
    """Returns a copy of the store for the given lb_id, without
    tenant_id
    """
    new_lb = deepcopy(store.lbs[lb_id])
    del new_lb["tenant_id"]
    del new_lb["nodeCount"]
    return new_lb


def _verify_and_update_lb_state(store, lb_id, set_state=True,
                                current_timestamp=None):
    """
    Based on the current state, the metadata on the lb and the time since the LB has
    been in that state, set the appropriate state in store.lbs
    Note: Reconsider if update metadata is implemented
    """
    current_timestring = seconds_to_timestamp(current_timestamp)
    if store.lbs[lb_id]["status"] == "BUILD":
        store.meta[lb_id]["lb_building"] = store.meta[lb_id]["lb_building"] or 10
        store.lbs[lb_id]["status"] = set_resource_status(
            store.lbs[lb_id]["updated"]["time"],
            store.meta[lb_id]["lb_building"],
            current_timestamp=current_timestamp
        ) or "BUILD"

    elif store.lbs[lb_id]["status"] == "ACTIVE" and set_state:
        if "lb_pending_update" in store.meta[lb_id]:
            store.lbs[lb_id]["status"] = "PENDING-UPDATE"
            log.msg(store.lbs[lb_id]["status"])
        if "lb_pending_delete" in store.meta[lb_id]:
            store.lbs[lb_id]["status"] = "PENDING-DELETE"
        if "lb_error_state" in store.meta[lb_id]:
            store.lbs[lb_id]["status"] = "ERROR"
        store.lbs[lb_id]["updated"]["time"] = current_timestring

    elif store.lbs[lb_id]["status"] == "PENDING-UPDATE":
        if "lb_pending_update" in store.meta[lb_id]:
            store.lbs[lb_id]["status"] = set_resource_status(
                store.lbs[lb_id]["updated"]["time"],
                store.meta[lb_id]["lb_pending_update"],
                current_timestamp=current_timestamp
            ) or "PENDING-UPDATE"

    elif store.lbs[lb_id]["status"] == "PENDING-DELETE":
        store.meta[lb_id]["lb_pending_delete"] = store.meta[lb_id]["lb_pending_delete"] or 10
        store.lbs[lb_id]["status"] = set_resource_status(
            store.lbs[lb_id]["updated"]["time"],
            store.meta[lb_id]["lb_pending_delete"], "DELETED",
            current_timestamp=current_timestamp
        ) or "PENDING-DELETE"
        store.lbs[lb_id]["updated"]["time"] = current_timestring

    elif store.lbs[lb_id]["status"] == "DELETED":
        # see del_load_balancer above for an explanation of this state change.
        store.lbs[lb_id]["status"] = set_resource_status(
            store.lbs[lb_id]["updated"]["time"], 3600, "DELETING-NOW",
            current_timestamp=current_timestamp
        ) or "DELETED"
        if store.lbs[lb_id]["status"] == "DELETING-NOW":
            del store.lbs[lb_id]


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
