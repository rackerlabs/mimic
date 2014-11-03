from twisted.python import log
agents_cache = {}

def list_agents(tenant_id):

    response = dict(
       (k,v) for (k,v) in agents_cache.items()
       if tenant_id == v['tenant_id']
    )

    return {'agents': response.values() or []}, 200
