"""
Canned response for add and delete node for load balancers
"""
from random import randrange
from twisted.python import log
from datetime import datetime, timedelta
from mimic.canned_responses.mimic_presets import get_presets
from mimic.util.helper import (not_found_response, current_time_in_utc, fmt)

lb_node_id_cache = {}
lb_cache = {}


def load_balancer_example(lb_info, lb_id, status):
    """
    Create load balancer response example
    """
    lb_example = {"name": lb_info["name"],
                  "id": randrange(99999),
                  "protocol": lb_info["protocol"],
                  "port": lb_info.get("port", 80),
                  "algorithm": lb_info.get("algorithm") or "RANDOM",
                  "status": status,
                  "cluster": {"name": "test-cluster"},
                  "timeout": lb_info.get("tiemout", 30),
                  "created": {"time": current_time_in_utc()},
                  "virtualIps": [{"address": "127.0.0.1",
                                 "id": randrange(99999),
                                 "type": "PUBLIC",
                                 "ipVersion": "IPV4"},
                                 {"address": "0000:0000:0000:0000:1111:111b:0000:0000",
                                  "id": randrange(99999),
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
        nodes_list = []
        for each in lb_info["nodes"]:
            node = {}
            node["address"] = each["address"]
            node["condition"] = each["condition"]
            node["port"] = each["port"]
            if each.get("weight"):
                node["weight"] = each["weight"]
            if each.get("type"):
                node["type"] = each["type"]
            nodes_list.append(node)
        lb_example.update({"nodes": nodes_list})
    return lb_example


def add_load_balancer(tenant_id, lb_info, lb_id):
    """
    Returns response of a newly created load balancer with
    response code 202, and adds the new lb to the lb_cache
    """
    status = "ACTIVE"
    if "BUILD" in lb_info["name"].upper():
        status = "BUILD"

    lb_cache[lb_id] = load_balancer_example(lb_info, lb_id, status)
    lb_cache[lb_id].update({"tenant_id": tenant_id})
    new_lb = lb_cache[lb_id].deepcopy()
    del new_lb["tenant_id"]
    return {'loadBalancer': new_lb}


def del_load_balancer(lb_id):
    """
    Returns response for a load balancer that is in building status for 20 seconds
    and response code 202, and adds the new lb to the lb_cache
    """
    if lb_id in lb_cache:
        del lb_cache[lb_id]
        return True, 204
    else:
        return not_found_response(), 404


def add_node(node_list, lb_id):
    """
    Returns the canned response for add nodes
    """
    node_response_list = []
    if lb_id not in lb_node_id_cache:
        lb_node_id_cache[lb_id] = {}
    for node in node_list:
        node_data = {}
        node_data['id'] = str(randrange(99999))
        node_data['status'] = 'ONLINE'
        node_data['address'] = node['address']
        node_data['port'] = node['port']
        node_data['condition'] = node['condition']
        if node.get('weight', 0):
            node_data['weight'] = node['weight']
        if node.get('type', 0):
            node_data['type'] = node['type']
        lb_node_id_cache[lb_id][node_data['id']] = node_data
        node_response_list.append(node_data)
    log.msg(lb_node_id_cache)
    return {'nodes': node_response_list}


def delete_node(lb_id, node_id):
    """
    Determines whether the node to be deleted exists in mimic cache and
    returns the response code.
    """
    response = 404
    if lb_id in lb_node_id_cache:
        if node_id in lb_node_id_cache[lb_id]:
            del lb_node_id_cache[lb_id][node_id]
            response = 202
    return response


def list_nodes(lb_id):
    """
    Returns the list of nodes remaining on the load balancer
    """
    if lb_id in lb_node_id_cache:
        return lb_node_id_cache[lb_id].values()
    else:
        return []


def _set_lb_status(lb_id):
    """
    Sets the load balancer to "ACTIVE" state if it has been on its
    previous ("BUILD", PENDING-UPDATE, PENDING-DELETE) state for over
    30 seconds. (This time can be changed by the presets)
    """
    if lb_cache[lb_id]["status"] != "ACTIVE":
        if (datetime.strptime(lb_cache[lb_id]['updated'], fmt) +
                timedelta(seconds=get_presets['loadbalancers']['time'])) < datetime.utcnow():
            lb_cache[lb_id]['status'] = "ACTIVE"
