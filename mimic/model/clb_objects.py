"""
Model objects for the CLB mimic.
"""

from mimic.util.helper import (EMPTY_RESPONSE, invalid_resource,
                               not_found_response, seconds_to_timestamp,)
from twisted.python import log
from characteristic import attributes, Attribute
from mimic.canned_responses.loadbalancer import (load_balancer_example,
                                                 _verify_and_update_lb_state,
                                                 _lb_without_tenant)


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

    def del_load_balancer(store, lb_id, current_timestamp):
        """
        Returns response for a load balancer that is in building status for 20
        seconds and response code 202, and adds the new lb to ``store.lbs``.
        A loadbalancer, on delete, goes into PENDING-DELETE and remains in
        DELETED status until a nightly job(maybe?)
        """
        if lb_id in store.lbs:

            if store.lbs[lb_id]["status"] == "PENDING-DELETE":
                msg = ("Must provide valid load balancers: {0} are "
                       "immutable and could not be processed.".format(lb_id))
                # Dont doubt this to be 422, it is 400!
                return invalid_resource(msg, 400), 400

            _verify_and_update_lb_state(store, lb_id, True, current_timestamp)

            if any([store.lbs[lb_id]["status"] == "ACTIVE",
                    store.lbs[lb_id]["status"] == "ERROR",
                    store.lbs[lb_id]["status"] == "PENDING-UPDATE"]):
                del store.lbs[lb_id]
                return EMPTY_RESPONSE, 202

            if store.lbs[lb_id]["status"] == "PENDING-DELETE":
                return EMPTY_RESPONSE, 202

            if store.lbs[lb_id]["status"] == "DELETED":
                _verify_and_update_lb_state(
                    store,
                    lb_id,
                    current_timestamp=current_timestamp)
                msg = ("Must provide valid load balancers: {0} "
                       "could not be found.".format(lb_id))
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
