"""
Model objects for images.
"""

from __future__ import absolute_import, division, unicode_literals

from characteristic import attributes, Attribute
from json import dumps
from mimic.model.rackspace_images import OnMetalImage

from mimic.model.nova_objects import not_found
from mimic.canned_responses.mimic_presets import get_presets


@attributes(
    ["tenant_id", "region_name", "clock", "image_store"])
class RegionalNovaImageCollection(object):
    """
    A collection of nova images, in a given region, for a given tenant.
    """
    def list_images(self, include_details, absolutize_url):
        """
        Return a list of images.
        """
        images_store = self.image_store.create_image_store(self.tenant_id)
        images = []
        for image in images_store:
            if self.region_name != "IAD" and isinstance(image, OnMetalImage):
                continue
            if include_details:
                images.append(image.detailed_json(absolutize_url))
            else:
                images.append(image.brief_json(absolutize_url))
        result = {"images": images}
        return dumps(result)

    def get_image(self, http_get_request, image_id, absolutize_url):
        """
        Return an image object if one exists from the list `/images` api,
        else return 404 Image not found.
        """
        if image_id in get_presets['servers']['invalid_image_ref'] or image_id.endswith('Z'):
            return dumps(not_found("The resource could not be found.",
                                   http_get_request))
        self.image_store.create_image_store(self.tenant_id)
        image = self.image_store.get_image_by_id(image_id)
        if image is None:
            return dumps(not_found('Image not found.', http_get_request))
        return dumps({"image": image.detailed_json(absolutize_url)})


@attributes(["tenant_id", "clock",
             Attribute("regional_collections", default_factory=dict)])
class GlobalNovaImageCollection(object):
    """
    A :obj:`GlobalNovaImageCollection` is a set of all the
    :obj:`RegionalNovaImageCollection` objects owned by a given tenant.  In other
    words, all the image objects that a single tenant owns globally.
    """

    def collection_for_region(self, region_name, image_store):
        """
        Get a :obj:`RegionalFlavorCollection` for the region identified by the
        given name.
        """
        if region_name not in self.regional_collections:
            self.regional_collections[region_name] = (
                RegionalNovaImageCollection(tenant_id=self.tenant_id, region_name=region_name,
                                            clock=self.clock, image_store=image_store))
        return self.regional_collections[region_name]
