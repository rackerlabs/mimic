"""
Model objects for mimic glance images.
"""

from characteristic import attributes, Attribute
from json import dumps
from mimic.model.rackspace_images import (OnMetalImage)


@attributes(["tenant_id", "region_name", "clock", "image_store"])
class RegionalGlanceImageCollection(object):
    """
    A collection of images, in a given region, for a given tenant.
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
        images_store = self.image_store.create_image_store(tenant_id)
        images = []
        for image in images_store:
            if region_name != "IAD" and isinstance(image, OnMetalImage):
                continue
            else:
                images.append(self.detailed_json(image))
        result = {"images": images, "schema": "/v2/schemas/images",
                  "first": "/v2/images?limit=1000"}

        return dumps(result)


@attributes(["tenant_id", "clock",
             Attribute("regional_collections", default_factory=dict)])
class GlobalGlanceImageCollection(object):
    """
    A :obj:`GlobalImageCollection` is a set of all the
    :obj:`RegionalImageCollection` objects owned by a given tenant.  In other
    words, all the glance image objects that a single tenant owns globally.
    """

    def collection_for_region(self, region_name, image_store):
        """
        Get a :obj:`RegionalGlanceImageCollection` for the region identified by the
        given name.
        """
        if region_name not in self.regional_collections:
            self.regional_collections[region_name] = (
                RegionalGlanceImageCollection(tenant_id=self.tenant_id, region_name=region_name,
                                              clock=self.clock, image_store=image_store))
        return self.regional_collections[region_name]
