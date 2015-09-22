"""
Model objects for mimic glance images.
"""

from characteristic import attributes, Attribute
from json import dumps
import uuid
from mimic.model.images import (RackspaceWindowsImage, RackspaceArchImage,
                                RackspaceCentOSPVImage, RackspaceCentOSPVHMImage,
                                RackspaceCoreOSImage, RackspaceDebianImage,
                                RackspaceFedoraImage, RackspaceFreeBSDImage,
                                RackspaceGentooImage, RackspaceOpenSUSEImage,
                                RackspaceRedHatPVImage, RackspaceRedHatPVHMImage,
                                RackspaceUbuntuPVImage, RackspaceUbuntuPVHMImage,
                                RackspaceVyattaImage, RackspaceScientificImage,
                                RackspaceOnMetalCentOSImage, RackspaceOnMetalCoreOSImage,
                                RackspaceOnMetalDebianImage, RackspaceOnMetalFedoraImage,
                                RackspaceOnMetalUbuntuImage, OnMetalImage)


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

    def create_images_list(self):
        """
        Generates the data for each glance image in each image class
        """
        image_classes = [RackspaceWindowsImage, RackspaceVyattaImage, RackspaceUbuntuPVImage,
                         RackspaceUbuntuPVHMImage, RackspaceScientificImage, RackspaceArchImage,
                         RackspaceCentOSPVImage, RackspaceCentOSPVHMImage, RackspaceCoreOSImage,
                         RackspaceDebianImage, RackspaceFedoraImage, RackspaceOpenSUSEImage,
                         RackspaceGentooImage, RackspaceFreeBSDImage, RackspaceRedHatPVImage,
                         RackspaceRedHatPVHMImage, RackspaceOnMetalDebianImage,
                         RackspaceOnMetalFedoraImage, RackspaceOnMetalUbuntuImage,
                         RackspaceOnMetalCentOSImage, RackspaceOnMetalCoreOSImage]
        for image_class in image_classes:
            for image, image_spec in image_class.images.iteritems():
                image_name = image
                image_id = str(uuid.uuid4())
                minRam = image_spec['minRam']
                minDisk = image_spec['minDisk']
                image_size = image_spec['OS-EXT-IMG-SIZE:size']
                image = image_class(image_id=image_id, tenant_id=33333, name=image_name,
                                    minRam=minRam, minDisk=minDisk, image_size=image_size)
                if 'com.rackspace__1__ui_default_show' in image_spec:
                    image.set_is_default()
                self.images_store.append(image)

    def list_images(self, region_name, include_details):
        """
        Return a list of glance images.
        """
        self.create_images_list()
        images = []
        for image in self.images_store:
            if region_name != "IAD" and isinstance(image, OnMetalImage):
                continue
            else:
                images.append(self.detailed_json(image))
        result = {"images": images, "schema": "/v2/schemas/images",
                  "first": "/v2/images?limit=1000"}

        return dumps(result)

    def image_by_id(self, image_id):
        """
        Retrieve a :obj:`Glance Image` object by its ID.
        """
        for image in self.images_store:
            if image.image_id == image_id:
                return image
