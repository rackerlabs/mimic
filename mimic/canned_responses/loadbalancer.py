# -*- test-case-name: mimic.test.test_loadbalancer -*-
"""
Canned response for add/get/list/delete load balancers and
add/get/delete/list nodes
"""
from random import randrange
from mimic.util.helper import (set_resource_status, seconds_to_timestamp)
from twisted.python import log


def load_balancer_example(lb_info, lb_id, status,
                          current_time):
    """
    Create load balancer response example
    """
    lb_example = {"name": lb_info["name"],
                  "id": lb_id,
                  "protocol": lb_info["protocol"],
                  "port": lb_info.get("port", 80),
                  "algorithm": lb_info.get("algorithm") or "RANDOM",
                  "status": status,
                  "cluster": {"name": "test-cluster"},
                  "timeout": lb_info.get("timeout", 30),
                  "created": {"time": current_time},
                  "virtualIps": [{"address": "127.0.0.1",
                                 "id": 1111, "type": "PUBLIC", "ipVersion": "IPV4"},
                                 {"address": "0000:0000:0000:0000:1111:111b:0000:0000",
                                  "id": 1111,
                                  "type": "PUBLIC",
                                  "ipVersion": "IPV6"}],
                  "sourceAddresses": {"ipv6Public": "0000:0001:0002::00/00",
                                      "ipv4Servicenet": "127.0.0.1",
                                      "ipv4Public": "127.0.0.1"},
                  "httpsRedirect": lb_info.get("httpsRedirect", False),
                  "updated": {"time": current_time},
                  "halfClosed": lb_info.get("halfClosed", False),
                  "connectionLogging": lb_info.get("connectionLogging", {"enabled": False}),
                  "contentCaching": {"enabled": False}}
    if lb_info.get("metadata"):
        lb_example.update({"metadata": _format_meta(lb_info["metadata"])})
    return lb_example


def _delete_node(store, lb_id, node_id):
    """Delete a node by ID."""
    if store.lbs[lb_id].nodes:
        for each in store.lbs[lb_id].nodes:
            if each.id == node_id:
                index = store.lbs[lb_id].nodes.index(each)
                del store.lbs[lb_id].nodes[index]
                return True
    return False


def _format_meta(metadata_list):
    """
    creates metadata with 'id' as a key
    """
    meta = []
    for each in metadata_list:
        each.update({"id": randrange(999)})
        meta.append(each)
    return meta


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
