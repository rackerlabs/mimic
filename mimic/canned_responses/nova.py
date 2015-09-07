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


def get_networks():
    """
    Return networks
    """
    return _get_json("json/nova/networks_json.py")


def get_os_volume_attachments():
    """
    Return volume empty attachments
    """
    return {"volumeAttachments": []}
