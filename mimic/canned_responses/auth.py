"""
Canned response for get auth token
"""
from datetime import datetime, timedelta
from random import randrange
auth_cache = {}
token_cache = {}

HARD_CODED_TOKEN = "fff73937db5047b8b12fc9691ea5b9e8"
HARD_CODED_USER_ID = "10002"
HARD_CODED_USER_NAME = "autoscaleaus"
HARD_CODED_ROLES = [{"id": "1", "description": "Admin", "name": "Identity"}]

def get_token(tenant_id):
    """
    Canned response for authentication, with service catalog containing endpoints only
    for services implemented by Mimic.
    """
    return {
        "access": {
            "token": {
                "id": HARD_CODED_TOKEN,
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
            "user": {"id": HARD_CODED_USER_ID,
                     "name": HARD_CODED_USER_NAME,
                     "roles": HARD_CODED_ROLES,
                     }}}


def get_user(tenant_id):
    """
    Canned response for get user. This adds the tenant_id to the auth_cache and
    returns unique username for the tenant id.
    """
    username = 'mockuser{0}'.format(str(randrange(999999)))
    auth_cache[username] = {'tenant_id': tenant_id}
    return {'user': {'id': username}}


def get_user_token(expires_in, username):
    """
    Canned response for get user token. Also, creates a unique token for a given username,
    and associated that token to the username in auth_cache.
    """
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
    """
    Canned response for Identity's get enpoints call. This returns endpoints only
    for the services implemented by Mimic.
    """
    if token_id in token_cache:
        tenant_id = token_cache[token_id]
    else:
        tenant_id = "11111"
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
