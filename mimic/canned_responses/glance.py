"""
Cannned responses for glance images
"""
import json
import os

# Pull this out and put in util/helper.py
def _location():
    return os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def _get_json(file_name):
    f = open(os.path.join(_location(), file_name))
    data = f.read()
    return json.loads(data)


def get_images():
    """
    Canned response for glance images list call
    """
    return _get_json("json/glance/glance_images.json")


def get_pending_images():
    """
    Pending images response
    """
    return []
