"""
Canned response for add and delete node for load balancers
"""
from random import randrange
from twisted.python import log


lb_node_id_cache = {}


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
        try:
            if node['weight']:
                node_data['weight'] = node['weight']
        except:
            KeyError
        try:
            if node['type']:
                node_data['type'] = node['type']
        except:
            KeyError
        lb_node_id_cache[lb_id][node_data['id']] = node_data
        node_response_list.append(node_data)
    #log.msg(lb_node_id_cache)
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
