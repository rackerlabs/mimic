"""
Model objects for the CLB mimic.
"""

from mimic.util.helper import (
    EMPTY_RESPONSE, not_found_response, seconds_to_timestamp,
    set_resource_status, invalid_resource
)
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

    def del_load_balancer(self, lb_id, current_timestamp):
        """
        Returns response for a load balancer that is in building status for 20
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

            self._verify_and_update_lb_state(lb_id, True, current_timestamp)

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
