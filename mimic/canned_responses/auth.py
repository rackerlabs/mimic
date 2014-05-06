"""
Canned response for get auth token
"""
from datetime import datetime, timedelta
from random import randrange
from mimic.util.mimic_options import OPTION_VALUES


auth_cache = {}
token_cache = {}


def get_token(tenant_id):
    service_urls = get_service_urls(tenant_id, OPTION_VALUES)
    return {
        "access": {
            "token": {
                "id": "fff73937db5047b8b12fc9691ea5b9e8",
                "expires": ((datetime.now() + timedelta(1)).
                            strftime(('%Y-%m-%dT%H:%M:%S.999-05:00'))),
                "tenant": {
                    "id": tenant_id,
                    "name": tenant_id},
                "RAX-AUTH:authenticatedBy": ["PASSWORD"]},
            "serviceCatalog": [
                {"name": "cloudServersOpenStack",
                 "endpoints": [{"region": "ORD",
                                "tenantId": tenant_id,
                                "publicURL": service_urls['nova']}],
                 "type": "compute"},
                {"name": "cloudLoadBalancers",
                 "endpoints": [{"region": "ORD",
                                "tenantId": tenant_id,
                                "publicURL": service_urls['load_balancer']}],
                 "type": "rax:load-balancer"}],
            "user": {"id": "10002",
                     "name": "autoscaleaus",
                     "roles": [{"id": "1", "description": "Admin", "name": "Identity"}]
                     }}}


def get_user(tenant_id):
    username = 'mockuser{0}'.format(str(randrange(999999)))
    auth_cache[username] = {'tenant_id': tenant_id}
    return {'user': {'id': username}}


def get_user_token(expires_in, username):
    token = 'mocked-token{0}'.format(str(randrange(9999999)))
    if username in auth_cache:
        if not auth_cache.get('username.token'):
            auth_cache[username]['token'] = token
    else:
        auth_cache[username] = {}
        auth_cache[username]['token'] = token
        auth_cache[username]['tenant_id'] = '11111'
    token_cache[token] = auth_cache[username]['tenant_id']
    return {
        "access":
        {"token":
           {"id": auth_cache[username]['token'],
            "expires": ((datetime.now() + timedelta(seconds=int(expires_in))).
                        strftime(('%Y-%m-%dT%H:%M:%S.999-05:00')))}
         }
    }


def get_endpoints(token_id):
    if token_id in token_cache:
        tenant_id = token_cache[token_id]
    else:
        tenant_id = "11111"

    service_urls = get_service_urls(tenant_id, OPTION_VALUES)

    return {"endpoints": [{"tenantId": tenant_id,
                           "region": "ORD",
                           "id": 19,
                           "publicURL": service_urls['load_balancer'],
                           "name": "cloudLoadBalancers",
                           "type": "rax:load-balancer"},
                          {"tenantId": tenant_id,
                           "region": "ORD",
                           "id": 303,
                           "publicURL": service_urls['nova'],
                           "versionInfo": "http://127.0.0.1:8902/v2",
                           "versionList": "http://127.0.0.1:8902/",
                           "name": "cloudServersOpenStack",
                           "versionId": "2",
                           "type": "compute"}]}


def get_service_urls(tenant_id, OPTION_VALUES):
    """
    Returns a dict object consisting of the service and its endpoint
    """
    n_version = 'v2'
    l_version = 'v1.0'

    port = OPTION_VALUES['port']
    ip = OPTION_VALUES['ip_address']

    # the port is incremented by 2 cause the first is assigned to mimic and the next to Identity
    nova_endpoint = "http://{0}:{1}/{2}/{3}".format(ip, str(port + 2), n_version, tenant_id)
    lb_endpoint = "http://{0}:{1}/{2}/{3}".format(ip, str(port + 3), l_version, tenant_id)

    return {'nova': nova_endpoint, 'load_balancer': lb_endpoint}
