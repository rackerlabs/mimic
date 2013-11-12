"""
Canned response for get auth token
"""
from datetime import datetime, timedelta


get_token = {
    "access": {
        "token": {
            "id": "fff73937db5047b8b12fc9691ea5b9e8",
            "expires": ((datetime.now() + timedelta(1)).
                        strftime(('%Y-%m-%dT%H:%M:%S.999-05:00'))),
            "tenant": {
                "id": "851153",
                "name": "851153"},
            "RAX-AUTH:authenticatedBy": ["PASSWORD"]},
        "serviceCatalog": [
            {"name": "cloudServersOpenStack",
             "endpoints": [{"region": "ORD",
                            "tenantId": "851153",
                            "publicURL": "http://10.20.76.59:8902/v2/851153/servers"}],
             "type": "compute"},
            {"name": "cloudLoadBalancers",
             "endpoints": [{"region": "ORD",
                            "tenantId": "851153",
                            "publicURL": "http://10.20.76.59:8903/v2/851153/loadbalancers"}],
             "type": "rax:load-balancer"}],
        "user": {"id": "10002",
                 "name": "autoscaleaus",
                 "roles": [{"id": "1", "description": "Admin", "name": "Identity"}]
                 }}}


def get_user():
    return {'user': {'id': 'autoscaleaus'}}


def get_user_token(expires_in):
    return {
        "access":
           {"token":
            {"id": "sample12auth12token12f0r12otter",
             "expires": ((datetime.now() + timedelta(seconds=int(expires_in))).
                         strftime(('%Y-%m-%dT%H:%M:%S.999-05:00')))}
            }
    }


def get_endpoints():
    return {"endpoints": [{"tenantId": "851153",
                           "region": "ORD",
                           "id": 19,
                           "publicURL": "http://10.20.76.59:8903/v2/851153",
                           "name": "cloudLoadBalancers",
                           "type": "rax:load-balancer"},
                          {"tenantId": "851153",
                           "region": "ORD",
                           "id": 86,
                           "publicURL": "http://10.20.76.59:8904/v2/851153",
                           "name": "autoscale",
                           "type": "rax:autoscale"},
                          {"tenantId": "851153",
                           "region": "ORD",
                           "id": 303,
                           "publicURL": "http://10.20.76.59:8902/v2/851153/",
                           "versionInfo": "http://10.20.76.59:8902/v2",
                           "versionList": "http://10.20.76.59:8902/",
                           "name": "cloudServersOpenStack",
                           "versionId": "2",
                           "type": "compute"}]}
