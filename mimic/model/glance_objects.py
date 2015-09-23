"""
Model objects for mimic glance images.
"""

from characteristic import attributes, Attribute
from json import dumps
from mimic.model.images import (ImageStore, OnMetalImage)


@attributes([Attribute("images_store", default_factory=list)])
class GlanceImage(object):
    """
    A Glance Image object
    """

    def detailed_json(self, image):
        """
        Long-form JSON-serializable object representation of this flavor, as
        returned by either a GET on this individual flavor or a member in the
        list returned by the list-details request.
        """
        template = {}
        for key, value in image.metadata_json().iteritems():
            template.update({key: value})

        if image.is_default:
            template.update({"com.rackspace__1__ui_default_show": "True"})

        template.update({
            "id": image.image_id,
            "name": image.name,
            "minRam": image.minRam,
            "minDisk": image.minDisk,
            "size": image.image_size,
            "status": "active"
        })
        return template

    def list_images(self, region_name, tenant_id, include_details):
        """
        Return a list of glance images.
        """
        images_store = ImageStore.create_image_store(tenant_id)
        images = []
        for image in images_store:
            if region_name != "IAD" and isinstance(image, OnMetalImage):
                continue
            else:
                images.append(self.detailed_json(image))
        result = {"images": images, "schema": "/v2/schemas/images",
                  "first": "/v2/images?limit=1000"}

        return dumps(result)
