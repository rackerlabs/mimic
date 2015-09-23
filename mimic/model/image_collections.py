"""
Model objects for images.
"""

from characteristic import attributes, Attribute
from json import dumps
from mimic.model.images import (
    RackspaceWindowsImage, RackspaceArchImage, RackspaceCentOSPVImage,
    RackspaceCentOSPVHMImage, RackspaceCoreOSImage, RackspaceDebianImage,
    RackspaceFedoraImage, RackspaceFreeBSDImage, RackspaceGentooImage, RackspaceOpenSUSEImage,
    RackspaceRedHatPVImage, RackspaceRedHatPVHMImage, RackspaceUbuntuPVImage, RackspaceUbuntuPVHMImage,
    RackspaceVyattaImage, RackspaceScientificImage, RackspaceOnMetalCentOSImage,
    RackspaceOnMetalCoreOSImage, RackspaceOnMetalDebianImage, RackspaceOnMetalFedoraImage,
    RackspaceOnMetalUbuntuImage, OnMetalImage)

from mimic.model.nova_objects import not_found
from mimic.canned_responses.mimic_presets import get_presets
import uuid


@attributes(
    ["tenant_id", "region_name", "clock",
     Attribute("images_store", default_factory=list)]
)
class RegionalImageCollection(object):
    """
    A collection of images, in a given region, for a given tenant.
    """
    def image_by_id(self, image_id):
        """
        Retrieve a :obj:`Image` object by its ID.
        """
        self._create_images_list()
        for image in self.images_store:
            if image.image_id == image_id:
                return image

    def _create_images_list(self):
        """
        Generates the data for each image in each image class
        """
        image_classes = [RackspaceWindowsImage, RackspaceArchImage, RackspaceCentOSPVImage,
                         RackspaceCentOSPVHMImage, RackspaceCoreOSImage, RackspaceDebianImage,
                         RackspaceFedoraImage, RackspaceFreeBSDImage, RackspaceGentooImage,
                         RackspaceOpenSUSEImage, RackspaceRedHatPVImage, RackspaceRedHatPVHMImage,
                         RackspaceUbuntuPVImage, RackspaceUbuntuPVHMImage, RackspaceVyattaImage,
                         RackspaceScientificImage, RackspaceOnMetalCentOSImage,
                         RackspaceOnMetalCoreOSImage, RackspaceOnMetalDebianImage,
                         RackspaceOnMetalFedoraImage, RackspaceOnMetalUbuntuImage]
        if len(self.images_store) < 1:
            for image_class in image_classes:
                for image, image_spec in image_class.images.iteritems():
                    image_name = image
                    image_id = str(uuid.uuid4())
                    minRam = image_spec['minRam']
                    minDisk = image_spec['minDisk']
                    image_size = image_spec['OS-EXT-IMG-SIZE:size']
                    tenant_id = self.tenant_id
                    image = image_class(image_id=image_id, tenant_id=tenant_id,
                                        image_size=image_size, name=image_name, minRam=minRam,
                                        minDisk=minDisk)
                    self.images_store.append(image)

    def list_images(self, include_details, absolutize_url):
        """
        Return a list of images.
        """
        self._create_images_list()
        images = []
        for image in self.images_store:
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
        if image_id in get_presets['servers']['invalid_image_ref']:
            return dumps(not_found("The resource could not be found.",
                                   http_get_request))
        self._create_images_list()
        image = self.image_by_id(image_id)
        if image is None:
            return dumps(not_found('Image not found.', http_get_request))
        return dumps({"image": image.detailed_json(absolutize_url)})


@attributes(["tenant_id", "clock",
             Attribute("regional_collections", default_factory=dict)])
class GlobalImageCollection(object):
    """
    A :obj:`GlobalImageCollection` is a set of all the
    :obj:`RegionalImageCollection` objects owned by a given tenant.  In other
    words, all the image objects that a single tenant owns globally.
    """

    def collection_for_region(self, region_name):
        """
        Get a :obj:`RegionalFlavorCollection` for the region identified by the
        given name.
        """
        if region_name not in self.regional_collections:
            self.regional_collections[region_name] = (
                RegionalImageCollection(tenant_id=self.tenant_id, region_name=region_name,
                                        clock=self.clock))
        return self.regional_collections[region_name]
