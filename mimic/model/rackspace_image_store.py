from characteristic import attributes, Attribute
from rackspace_images import (RackspaceWindowsImage, RackspaceArchImage, RackspaceCentOSPVImage,
                              RackspaceCentOSPVHMImage, RackspaceCoreOSImage, RackspaceDebianImage,
                              RackspaceFedoraImage, RackspaceFreeBSDImage, RackspaceGentooImage,
                              RackspaceOpenSUSEImage, RackspaceRedHatPVImage, RackspaceRedHatPVHMImage,
                              RackspaceUbuntuPVImage, RackspaceUbuntuPVHMImage, RackspaceVyattaImage,
                              RackspaceScientificImage, RackspaceOnMetalCentOSImage,
                              RackspaceOnMetalCoreOSImage, RackspaceOnMetalDebianImage,
                              RackspaceOnMetalFedoraImage, RackspaceOnMetalUbuntuImage)


@attributes([Attribute("image_store", default_factory=list)])
class RackspaceImageStore(object):
    """
    A store for images to share between nova_api and glance_api
    """
    def create_image_store(self, tenant_id):
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
        if len(self.image_store) < 1:
            for image_class in image_classes:
                for image, image_spec in image_class.images.iteritems():
                    image_name = image
                    image_id = image_spec['id']
                    minRam = image_spec['minRam']
                    minDisk = image_spec['minDisk']
                    image_size = image_spec['OS-EXT-IMG-SIZE:size']
                    disk_config = image_spec['OS-DCF:diskConfig']
                    image = image_class(image_id=image_id, tenant_id=tenant_id,
                                        image_size=image_size, name=image_name, minRam=minRam,
                                        minDisk=minDisk, disk_config=disk_config)
                    if 'com.rackspace__1__ui_default_show' in image_spec:
                        image.set_is_default()
                    self.image_store.append(image)
        return self.image_store

    def get_image_by_id(self, image_id):
        """
        Get an image by its id
        """
        for image in self.image_store:
            if image_id == image.image_id:
                return image

    def add_image_to_store(self, image):
        """
        Add a new image to the images store
        """
        self.image_store.append(image)

    def delete_image_from_store(self, image_id):
        """
        Deletes an image from the image store
        """
        image = self.get_image_by_id(image_id)
        self.image_store.remove(image)