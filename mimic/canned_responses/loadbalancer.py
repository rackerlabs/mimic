"""
Canned response for add and delete node for load balancers
TBD: Add delay of 'time' seconds on create lb to transition from BUILD to ACTIVE,
     if lb name has 'BUILD' in it during create or update.
    {
     message: "Load Balancer 'XXXX' has a status of 'BUILD' and is considered immutable."
     code: 422
    }
Set the LB status to be in 'ERROR' if name has 'ERROR' when LB is created or updated.
Set the LB status to be 'PENDING-UPDATE' on every add/delete node and update node to have
  name 'PENDING-UPDATE'. Never during create. (?)
Set LB status to 'PENDING-DELETE' on DELETE LB if the LB name has 'PENDING_DELETE' in it,
  for 'time' seconds
If a LB is deleted, set the status to 'DELETED' and results in 422 on any action.
"""
from random import randrange
from copy import deepcopy
from mimic.util.helper import (not_found_response, current_time_in_utc,
                               invalid_resource)

lb_node_id_cache = {}
lb_cache = {}


def load_balancer_example(lb_info, lb_id, status):
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
                  "timeout": lb_info.get("tiemout", 30),
                  "created": {"time": current_time_in_utc()},
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
                  "updated": {"time": current_time_in_utc()},
                  "halfClosed": lb_info.get("halfClosed", False),
                  "connectionLogging": lb_info.get("connectionLogging", {"enabled": False}),
                  "contentCaching": {"enabled": False}}
    if lb_info.get("nodes"):
        lb_example.update({"nodes": _format_nodes_on_lb(lb_info["nodes"])})
    if lb_info.get("metadata"):
        lb_example.update({"metadata": _format_meta(lb_info["metadata"])})
    return lb_example


def add_load_balancer(tenant_id, lb_info, lb_id):
    """
    Returns response of a newly created load balancer with
    response code 202, and adds the new lb to the lb_cache.
    Note: lb_cache has tenant_id added as an extra key in comparison
    to the lb_example.
    """
    status = "ACTIVE"
    lb_cache[lb_id] = load_balancer_example(lb_info, lb_id, status)
    lb_cache[lb_id].update({"tenant_id": tenant_id})
    new_lb = deepcopy(lb_cache[lb_id])
    del new_lb["tenant_id"]
    return {'loadBalancer': new_lb}, 202


def del_load_balancer(lb_id):
    """
    Returns response for a load balancer that is in building status for 20 seconds
    and response code 202, and adds the new lb to the lb_cache
    """
    if lb_id in lb_cache:
        del lb_cache[lb_id]
        return None, 202
    else:
        return not_found_response(), 404


def list_load_balancers(tenant_id):
    """
    Returns the list of load balancers with the given tenant id with response
    code 200. If no load balancers are found returns empty list.
    """
    response = dict(
        (k, v) for (k, v) in lb_cache.items()
        if tenant_id == v['tenant_id']
    )
    return {'loadBalancers': response.values() or []}, 200


def add_node(node_list, lb_id):
    """
    Returns the canned response for add nodes
    """
    if lb_id in lb_cache:
        nodes = _format_nodes_on_lb(node_list)
        if lb_cache[lb_id].get("nodes"):
            for existing_node in lb_cache[lb_id]["nodes"]:
                for new_node in node_list:
                    if (
                        existing_node["address"] == new_node["address"] and
                        existing_node["port"] == new_node["port"]
                    ):
                            return invalid_resource("Duplicate nodes detected. One or more nodes "
                                                    "already configured on load balancer.", 413), 413
            lb_cache[lb_id]["nodes"] = lb_cache[lb_id]["nodes"] + nodes
        else:
            lb_cache[lb_id]["nodes"] = nodes
        return {"nodes": nodes}, 200
    else:
        return not_found_response("loadbalancer"), 404


def delete_node(lb_id, node_id):
    """
    Determines whether the node to be deleted exists in mimic cache and
    returns the response code.
    Note : Currently even if node does not exist, return 202 on delete.
    """
    if lb_id in lb_cache:
        lb_cache[lb_id]["nodes"] = [x for x in lb_cache[
            lb_id]["nodes"] if not (node_id == x.get("id"))]
        if not lb_cache[lb_id]["nodes"]:
            del lb_cache[lb_id]["nodes"]
        return None, 202
    else:
        return not_found_response("loadbalancer"), 404


def list_nodes(lb_id):
    """
    Returns the list of nodes remaining on the load balancer
    """
    if lb_id in lb_cache:
        node_list = []
        if lb_cache[lb_id].get("nodes"):
            node_list = lb_cache[lb_id]["nodes"]
        return {"nodes": node_list}, 200
    else:
        return not_found_response("loadbalancer"), 404


def _format_nodes_on_lb(node_list):
    """
    create a dict of nodes given the list of nodes
    """
    nodes = []
    for each in node_list:
        node = {}
        node["address"] = each["address"]
        node["condition"] = each["condition"]
        node["port"] = each["port"]
        if each.get("weight"):
            node["weight"] = each["weight"]
        if each.get("type"):
            node["type"] = each["type"]
        node["id"] = randrange(999999)
        node["status"] = "ONLINE"
        nodes.append(node)
    return nodes


def _format_meta(node_list):
    """
    creates metadata with 'id' as a key
    """
    meta = []
    for each in node_list:
        each.update({"id": randrange(999)})
        meta.append(each)
    return meta
