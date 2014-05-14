# -*- test-case-name: mimic.test.test_auth -*-
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

def format_timestamp(dt):
    """
    Format the given timestamp.

    :param datetime.datetime dt: A datetime.datetime object to be formatted.
    """
    return dt.strftime('%Y-%m-%dT%H:%M:%S.999-05:00')



class CatalogEndpoint(object):
    def __init__(self, tenant_id, region):
        self.tenant_id = tenant_id
        self.region = region

    def url_with_prefix(self, uri_prefix):
        return uri_prefix + "/v2/" + self.tenant_id



class CatalogEntry(object):
    def __init__(self, tenant_id, type, name, regions):
        self.type = type
        self.tenant_id = tenant_id
        self.name = name
        self._regions = regions

    @property
    def endpoints(self):
        """
        Yield a list of CatalogEndpoint objects for each endpoint supported by
        this catalog entry.
        """
        for region in self._regions:
            yield CatalogEndpoint(self.tenant_id, region)

    


def canned_entries(tenant_id):
    """
    Some canned catalog entries.
    """
    return [
        CatalogEntry(
            tenant_id, "compute", "cloudServersOpenStack", ["ORD"]
        ),
        CatalogEntry(
            tenant_id, "rax:load-balancer", "cloudLoadBalancers", ["ORD"]
        ),
    ]



def get_token(tenant_id,
              timestamp=format_timestamp,
              entry_generator=canned_entries):
    """
    Canned response for authentication, with service catalog containing
    endpoints only for services implemented by Mimic.

    :param callable timestamp: A callable, like format_timestamp, which takes a
        datetime and returns a string.
    :param entry_generator: A callable, like canned_entries, which takes a
        datetime and returns an iterable of CatalogEntry.

    :return: a JSON-serializable dictionary matching the format of the JSON
             response for the identity ``/v2/tokens`` request.
    """
    def entry_json():
        # ugly hack corresponding to hard-coding in mimic.tap, eliminate as
        # soon as that is gone.  note that the responsibility here is correct
        # though; URI generation belongs in the auth system.
        port_offset_by_service = {
            "compute": 2,
            "rax:load-balancer": 3,
        }
        for entry in entry_generator(tenant_id):
            def endpoint_json():
                for endpoint in entry.endpoints:
                    yield {
                        "region": endpoint.region,
                        "tenantId": endpoint.tenant_id,
                        "publicURL": endpoint.url_with_prefix(
                            "http://localhost:{port}/".format(
                                port=8900 + port_offset_by_service[entry.type]
                            )
                        ),
                    }
            yield {
                "name": entry.name,
                "type": entry.type,
                "endpoints": list(endpoint_json())
            }

    return {
        "access": {
            "token": {
                "id": HARD_CODED_TOKEN,
                "expires": timestamp(datetime.now() + timedelta(days=1)),
                "tenant": {
                    "id": tenant_id,
                    "name": tenant_id},
                "RAX-AUTH:authenticatedBy": ["PASSWORD"]},
            "serviceCatalog": list(entry_json()),
            "user": {
                "id": HARD_CODED_USER_ID,
                "name": HARD_CODED_USER_NAME,
                "roles": HARD_CODED_ROLES,
            }
        }
    }


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
    Canned response for Identity's get endpoints call.  This returns endpoints
    only for the services implemented by Mimic.
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
