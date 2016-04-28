"""
Cannned responses for glance images
"""

from __future__ import absolute_import, division, unicode_literals

from mimic.canned_responses.json.glance.glance_images_json import (images,
                                                                   image_schema)


def get_images():
    """
    Canned response for glance images list call
    """
    return images


def get_image_schema():
    """
    Canned response for GET glance image schema API call
    """
    return image_schema
