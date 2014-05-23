# -*- test-case-name: mimic.test.test_auth -*-
"""
Canned response for get auth token
"""
from datetime import datetime, timedelta
from random import randrange
from mimic.catalog import Entry
auth_cache = {}
token_cache = {}

HARD_CODED_TOKEN = "fff73937db5047b8b12fc9691ea5b9e8"
HARD_CODED_USER_ID = "10002"
HARD_CODED_USER_NAME = "autoscaleaus"
HARD_CODED_ROLES = [{"id": "1", "description": "Admin", "name": "Identity"}]

def HARD_CODED_PREFIX(entry_type):
    """
    Temporary hack.
    """
    # ugly hack corresponding to hard-coding in mimic.tap, eliminate as soon as
    # that is gone.  note that the responsibility here is correct though; URI
    # generation belongs in the auth system.
    port_offset_by_service = {
        "compute": 2,
        "rax:load-balancer": 3,
    }
    return "http://localhost:{port}/".format(
        port=8900 + port_offset_by_service[entry_type]
    )

def format_timestamp(dt):
    """
    Format the given timestamp.

    :param datetime.datetime dt: A datetime.datetime object to be formatted.
    """
    return dt.strftime('%Y-%m-%dT%H:%M:%S.999-05:00')



def canned_entries(tenant_id):
    """
    Some canned catalog entries.
    """
    return [
        Entry.with_regions(
            tenant_id, "compute", "cloudServersOpenStack", ["ORD"]
        ),
        Entry.with_regions(
            tenant_id, "rax:load-balancer", "cloudLoadBalancers", ["ORD"]
        ),
    ]



def get_token(tenant_id,
              timestamp=format_timestamp,
              entry_generator=canned_entries,
              response_token=HARD_CODED_TOKEN,
              response_user_id=HARD_CODED_USER_ID,
              response_user_name=HARD_CODED_USER_NAME,
              response_roles=HARD_CODED_ROLES,
              prefix_for_type=HARD_CODED_PREFIX,
            ):
    """
    Canned response for authentication, with service catalog containing
    endpoints only for services implemented by Mimic.

    :param callable timestamp: A callable, like format_timestamp, which takes a
        datetime and returns a string.
    :param entry_generator: A callable, like canned_entries, which takes a
        datetime and returns an iterable of Entry.

    :return: a JSON-serializable dictionary matching the format of the JSON
             response for the identity ``/v2/tokens`` request.
    """
    def entry_json():
        for entry in entry_generator(tenant_id):
            def endpoint_json():
                for endpoint in entry.endpoints:
                    yield {
                        "region": endpoint.region,
                        "tenantId": endpoint.tenant_id,
                        "publicURL": endpoint.url_with_prefix(
                            prefix_for_type(entry.type)
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
                "id": response_token,
                "expires": timestamp(datetime.now() + timedelta(days=1)),
                "tenant": {
                    "id": tenant_id,
                    "name": tenant_id},
                "RAX-AUTH:authenticatedBy": ["PASSWORD"]},
            "serviceCatalog": list(entry_json()),
            "user": {
                "id": response_user_id,
                "name": response_user_name,
                "roles": response_roles,
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



def get_user_token(expires_in, username,
                   timestamp=format_timestamp):
    """
    Canned response for get user token.  Also, creates a unique token for a
    given username, and associated that token to the username in auth_cache.
    """
    token = 'mocked-token{0}'.format(str(randrange(9999999)))
    if username in auth_cache:
        if not auth_cache.get('username.token'):
            auth_cache[username]['token'] = token
    else:
        auth_cache[username] = {
            'token': token,
            'tenant_id': '11111',
        }
    token_cache[token] = auth_cache[username]['tenant_id']
    return {
        "access": {
            "token": {
                "id": auth_cache[username]['token'],
                "expires": format_timestamp(datetime.now() +
                                            timedelta(seconds=int(expires_in)))
            }
        }
    }



def get_endpoints(tenant_id, entry_generator=canned_entries,
                  prefix_for_type=HARD_CODED_PREFIX):
    """
    Canned response for Identity's get endpoints call.  This returns endpoints
    only for the services implemented by Mimic.

    :param entry_generator: A callable, like :func:`canned_entries`, which
        takes a datetime and returns an iterable of Entry.
    """
    result = []
    for entry in entry_generator(tenant_id):
        for endpoint in entry.endpoints:
            result.append({
                "region": endpoint.region,
                "tenantId": endpoint.tenant_id,
                "publicURL": endpoint.url_with_prefix(
                    prefix_for_type(entry.type)
                ),
                "name": entry.name,
                "type": entry.type,
                "id": endpoint.endpoint_id,
            })
    return {"endpoints": result}
