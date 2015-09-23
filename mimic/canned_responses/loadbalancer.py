# -*- test-case-name: mimic.test.test_loadbalancer -*-
"""
Canned response for add/get/list/delete load balancers and
add/get/delete/list nodes
"""
from random import randrange


def load_balancer_example(lb_info, lb_id, status,
                          current_time):
    """
    Create load balancer response example
    """
    lb_example = {"name": lb_info["name"],
                  "id": lb_id,
                  "protocol": lb_info["protocol"],
                  "port": lb_info.get("port", 80),
                  "algorithm": lb_info.get("algorithm") or "RANDOM",
                  "status": status,
                  "cluster": {"name": "test-cluster"},
                  "timeout": lb_info.get("timeout", 30),
                  "created": {"time": current_time},
                  "virtualIps": [{"address": "127.0.0.1",
                                 "id": 1111, "type": "PUBLIC", "ipVersion": "IPV4"},
                                 {"address": "0000:0000:0000:0000:1111:111b:0000:0000",
                                  "id": 1111,
                                  "type": "PUBLIC",
                                  "ipVersion": "IPV6"}],
                  "sourceAddresses": {"ipv6Public": "0000:0001:0002::00/00",
                                      "ipv4Servicenet": "127.0.0.1",
                                      "ipv4Public": "127.0.0.1"},
                  "httpsRedirect": lb_info.get("httpsRedirect", False),
                  "updated": {"time": current_time},
                  "halfClosed": lb_info.get("halfClosed", False),
                  "connectionLogging": lb_info.get("connectionLogging", {"enabled": False}),
                  "contentCaching": {"enabled": False}}
    if lb_info.get("metadata"):
        lb_example.update({"metadata": _format_meta(lb_info["metadata"])})
    return lb_example


def _format_meta(metadata_list):
    """
    creates metadata with 'id' as a key
    """
    meta = []
    for each in metadata_list:
        each.update({"id": randrange(999)})
        meta.append(each)
    return meta
