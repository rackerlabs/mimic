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
                "id": "829409",
                "name": "829409"},
            "RAX-AUTH:authenticatedBy": ["PASSWORD"]},
        "serviceCatalog": [
            {"name": "cloudServersOpenStack",
             "endpoints": [{"region": "ORD",
                            "tenantId": "829409",
                            "publicURL": "http://localhost:8080/v2/829409/servers"}],
             "type": "compute"},
            {"name": "cloudLoadBalancers",
             "endpoints": [{"region": "ORD",
                            "tenantId": "829409",
                            "publicURL": "http://localhost:8080/v2/829409/loadbalancers"}],
             "type": "rax:load-balancer"}]}}


def get_user():
    return {'user': {'id': 'autoscaleprod'}}


def get_user_token(expires_in):
    return {
        "access":
           {"token":
            {"id": "sample12auth12token12f0r12otter",
             "expires": ((datetime.now() + timedelta(seconds=int(expires_in))).
                         strftime(('%Y-%m-%dT%H:%M:%S.999-05:00')))}
            }
        }
