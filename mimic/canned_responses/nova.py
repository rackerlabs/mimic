# -*- test-case-name: mimic.test.test_nova -*-
"""
Canned responses for nova.

This is a *bad* example of how you might implement generating a response to a
request.  The better example is split between :obj:`mimic.rest.nova_api` for
routing and HTTP protocol logic and :obj:`mimic.model.nova_objects` for
application-domain objects describing servers.  At this point this module
contains only those responses for which no live / dynamic / stateful responses
can be generated, and are therefore not really fully implemented.
"""

from mimic.canned_responses.mimic_presets import get_presets
from mimic.util.helper import not_found_response


def get_image(image_id):
    """
    Canned response for get image.  The image id provided is substituted in the
    response, if not one of the invalid image ids specified in mimic_presets.
    """
    if (
            image_id in get_presets['servers']['invalid_image_ref'] or
            image_id.endswith('Z')
    ):
        return not_found_response('images'), 404
    return {'image': {'status': 'ACTIVE', 'id': image_id, 'name': 'mimic-test-image'}}, 200


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
