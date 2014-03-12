"""
Canned response for get auth token
"""
from datetime import datetime, timedelta
from random import randrange
auth_cache = {}
token_cache = {}


def get_token(tenant_id,auth_user_name):
    if auth_user_name == 'user-admin':
        dict_roles = [{"id": "3", "serviceId": "bde1268ebabeeabb70a0e702a4626977c331d5c4","description": "User Admin Role.", "name": "identity:user-admin"}]
    elif auth_user_name == 'global-admin':
	dict_roles = [{"id": "10000258","description": "Full Access Admin Role for Account User","name": "admin"},
   					  {"id": "2","description": "Default Role.","name": "identity:default"}]
    print auth_user_name
    print dict_roles	
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
                                "publicURL": "http://localhost:8902/v2/{0}".format(tenant_id)}],
                 "type": "compute"},
                {"name": "cloudLoadBalancers",
                 "endpoints": [{"region": "ORD",
                                "tenantId": tenant_id,
                                "publicURL": "http://localhost:8903/v2/{0}".format(tenant_id)}],
                 "type": "rax:load-balancer"}],
            "user": {"id": "10002",
                     "name": auth_user_name,
                     "roles": dict_roles
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
            token_cache[token] = auth_cache[username]['tenant_id']
    else:
        auth_cache['no-user']['token'] = 'token-even-when-no-user'
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
        tenant_id = "851153"
    return {"endpoints": [{"tenantId": tenant_id,
                           "region": "ORD",
                           "id": 19,
                           "publicURL": "http://localhost:8903/v2/{0}".format(tenant_id),
                           "name": "cloudLoadBalancers",
                           "type": "rax:load-balancer"},
                          {"tenantId": tenant_id,
                           "region": "ORD",
                           "id": 86,
                           "publicURL": "http://localhost:8904/v2/{0}".format(tenant_id),
                           "name": "autoscale",
                           "type": "rax:autoscale"},
                          {"tenantId": tenant_id,
                           "region": "ORD",
                           "id": 303,
                           "publicURL": "http://localhost:8902/v2/{0}".format(tenant_id),
                           "versionInfo": "http://localhost:8902/v2",
                           "versionList": "http://localhost:8902/",
                           "name": "cloudServersOpenStack",
                           "versionId": "2",
                           "type": "compute"}]}
