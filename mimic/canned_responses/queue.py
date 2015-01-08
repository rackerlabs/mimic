"""
Canned response for Queue
"""


def queues_example(queue_name):
    """
    Create queue response example
    """
    queue_example = {"href": "/v1/queues/" + queue_name,
                     "name": queue_name}
    return queue_example


def add_queue(queue_id, queue_name, tenant_id, q_cache):
    """
    Returns response of a newly created queue with
    response code 201, and adds the new queue to the queue_cache.
    """
    q_cache[queue_id] = queues_example(queue_name)
    q_cache[queue_id].update({"tenant_id": tenant_id})
    return None, 201


def list_queues(tenant_id, q_cache):
    """
    Returns a list of queues with response code 200
    """
    return {'queues': q_cache.values() or []}, 200


def delete_queue(queue_name, q_cache):
    """
    Deletes a queue with response code 204
    """
    for key, val in q_cache.items():
        if queue_name == val['name']:
            del q_cache[key]
            return None, 204
