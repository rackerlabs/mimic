# -*- test-case-name: mimic.test.test_nova -*-
"""
Canned responses for nova's GET limits API
"""

from __future__ import absolute_import, division, unicode_literals


def get_limit():
    """
    Canned response for limits for servers. Returns only the absolute limits
    """
    return {"limits":
            {"absolute": {"maxServerMeta": 40,
                          "maxPersonality": 5,
                          "totalPrivateNetworksUsed": 0,
                          "maxImageMeta": 40,
                          "maxPersonalitySize": 1000,
                          "maxSecurityGroupRules": -1,
                          "maxTotalKeypairs": 100,
                          "totalCoresUsed": 5,
                          "totalRAMUsed": 2560,
                          "totalInstancesUsed": 5,
                          "maxSecurityGroups": -1,
                          "totalFloatingIpsUsed": 0,
                          "maxTotalCores": -1,
                          "totalSecurityGroupsUsed": 0,
                          "maxTotalPrivateNetworks": 3,
                          "maxTotalFloatingIps": -1,
                          "maxTotalInstances": 200,
                          "maxTotalRAMSize": 256000}}}


def get_version_v2(uri):
    """
    Canned response nova v2 version.

    Cf: http://developer.openstack.org/api-ref-compute-v2.1.html
    #listVersionsv2.1
    """
    return {"version":
            {"status": "SUPPORTED",
             "updated": "2011-01-21T11:33:21Z",
             "links": [{"href": uri,
                        "rel": "self"},
                       {"href": "http://docs.openstack.org/",
                        "type": "text/html",
                        "rel": "describedby"}],
             "min_version": "",
             "version": "",
             "media-types":
             [{
                 "base": "application/json",
                 "type": "application/vnd.openstack.compute+json;version=2"
             }],
             }
            }
