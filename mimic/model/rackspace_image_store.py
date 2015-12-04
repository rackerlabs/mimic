"""
An image store representing Rackspace specific images
"""
from __future__ import absolute_import, division, unicode_literals
from characteristic import attributes, Attribute
from six import iteritems
from mimic.model.rackspace_images import (RackspaceWindowsImage,
                                          RackspaceCentOSPVImage, RackspaceCentOSPVHMImage,
                                          RackspaceCoreOSImage, RackspaceDebianImage,
                                          RackspaceFedoraImage, RackspaceFreeBSDImage,
                                          RackspaceGentooImage, RackspaceOpenSUSEImage,
                                          RackspaceRedHatPVImage, RackspaceRedHatPVHMImage,
                                          RackspaceUbuntuPVImage, RackspaceUbuntuPVHMImage,
                                          RackspaceVyattaImage, RackspaceScientificImage,
                                          RackspaceOnMetalCentOSImage, RackspaceOnMetalCoreOSImage,
                                          RackspaceOnMetalDebianImage, RackspaceOnMetalFedoraImage,
                                          RackspaceOnMetalUbuntuImage)

from mimic.model.rackspace_images import create_rackspace_images


@attributes([Attribute("image_list", default_factory=list)])
class RackspaceImageStore(object):
    """
    A store for images to share between nova_api and glance_api
    :var image_list: list of Rackspace images
    """
    def create_image_store(self, tenant_id):
        """
        Generates the data for each image in each image class
        """
        image_classes = [RackspaceWindowsImage, RackspaceCentOSPVImage,
                         RackspaceCentOSPVHMImage, RackspaceCoreOSImage, RackspaceDebianImage,
                         RackspaceFedoraImage, RackspaceFreeBSDImage, RackspaceGentooImage,
                         RackspaceOpenSUSEImage, RackspaceRedHatPVImage, RackspaceRedHatPVHMImage,
                         RackspaceUbuntuPVImage, RackspaceUbuntuPVHMImage, RackspaceVyattaImage,
                         RackspaceScientificImage, RackspaceOnMetalCentOSImage,
                         RackspaceOnMetalCoreOSImage, RackspaceOnMetalDebianImage,
                         RackspaceOnMetalFedoraImage, RackspaceOnMetalUbuntuImage]
        if len(self.image_list) < 1:
            for image_class in image_classes:
                for image, image_spec in iteritems(image_class.images):
                    image_name = image
                    image_id = image_spec['id']
                    minRam = image_spec['minRam']
                    minDisk = image_spec['minDisk']
                    image_size = image_spec['OS-EXT-IMG-SIZE:size']
                    image = image_class(image_id=image_id, tenant_id=tenant_id,
                                        image_size=image_size, name=image_name, minRam=minRam,
                                        minDisk=minDisk)
                    if 'com.rackspace__1__ui_default_show' in image_spec:
                        image.set_is_default()
                    self.image_list.append(image)
            self.image_list.extend(create_rackspace_images(tenant_id))
        return self.image_list

    def get_image_by_id(self, image_id):
        """
        Get an image by its id
        """
        for image in self.image_list:
            if image_id == image.image_id:
                return image

    def add_image_to_store(self, image):
        """
        Add a new image to the list of images
        """
        self.image_list.append(image)
