from random import randrange
from copy import deepcopy

queue_cache = {}

def queues_example(queue_name):
    """
    Create queue response example
    """
    queue_example = {"href": "/v1/queues/" + queue_name,
		     "name": queue_name}
    return queue_example
                  
def add_queue(queue_id, queue_name, tenant_id):
    """
    Returns response of a newly created queue with
    response code 201, and adds the new queue to the queue_cache.
    """
    queue_cache[queue_id] = queues_example(queue_name)
    queue_cache[queue_id].update({"tenant_id": tenant_id})
    new_queue = deepcopy(queue_cache[queue_id])
    del new_queue["tenant_id"]
    return  None, 201

def list_queues(tenant_id):
    """
    Returns a list of queues with response code 200
    """
    response = {k: v for (k, v) in queue_cache.items() if tenant_id == v['tenant_id']}
    return {'queues': response.values() or []}, 200

def delete_queue(queue_name):
    """
    Deletes a queue with response code 201
    """
    for key, val in queue_cache.items():
      if queue_name == val['name']:
        del queue_cache[key]
        return None, 201
       
