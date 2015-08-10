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

import json
import os
# from mimic.canned_responses.mimic_presets import get_presets
# from mimic.util.helper import not_found_response


def _location():
    return os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def _get_json(file_name):
    f = open(os.path.join(_location(), file_name))
    data = f.read()
    return json.loads(data)


def get_key_pairs():
    """
    Canned responses for key pairs - just returns a static blob of json
    """
    return _get_json("json/nova/key_pairs_json.py")


def get_limit():
    """
    Canned response for limits for servers. Returns only the absolute limits
    """
    return _get_json("json/nova/limits_json.py")


def get_flavor_details():
    """
    Return flavor details
    """
    return _get_json("json/nova/flavor_details_json.py")


def get_networks():
    """
    Return networks
    """
    return _get_json("json/nova/networks_json.py")


def get_images():
    """
    Return images from servers endpoint
    """
    return _get_json("json/nova/images_json.py")


def get_os_volume_attachments():
    """
    Return get_os_volume_attachments()
    """
    return {"volumeAttachments": []}


def get_image(image_id):
    """
    Canned response for get image.  The image id provided is substituted in the
    response, if not one of the invalid image ids specified in mimic_presets.
    """
    images_data = _get_json("json/nova/images_json.py")['images']
    for image in images_data:
        if image['id'] == image_id:
            return image

            # if (
            #                 image_id in get_presets['servers']['invalid_image_ref'] or
            #             image_id.endswith('Z')
            # ):
            #     return not_found_response('images'), 404
            # return {'image': {'status': 'ACTIVE', 'id': image_id, 'name': 'mimic-test-image'}}, 200


def get_flavor(flavor_id):
    """
    Canned response for get flavor.
    The flavor id provided is substituted in the response
    """
    # if flavor_id in get_presets['servers']['invalid_flavor_ref']:
    #     return not_found_response('flavors'), 404
    # return ({'flavor': {'name': '512MB Standard Instance',
    #                     'id': flavor_id,
    #                     'name': 'mimic-test-flavor'}},
    #         200)
    flavors_data = _get_json("json/nova/flavor_details_json.py")['flavors']
    for flavor in flavors_data:
        if flavor['id'] == flavor_id:
            return {"flavor": flavor}
