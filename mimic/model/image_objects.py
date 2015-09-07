"""
Model objects for mimic images.
"""

from characteristic import attributes


@attributes(['image_id', 'tenant_id', 'name', 'minDisk', 'minRam', 'image_size'])
class Image(object):
    """
    A Image object
    """

    is_default = False

    def set_is_default(self):
        """
        Sets the image as default
        """
        self.is_default = True

    def links_json(self, absolutize_url):
        """
        Create a JSON-serializable data structure describing the links to this
        image.
        """
        return [
            {
                "href": absolutize_url("v2/{0}/images/{1}"
                                       .format(self.tenant_id, self.image_id)),
                "rel": "self"
            },
            {
                "href": absolutize_url("{0}/images/{1}"
                                       .format(self.tenant_id, self.image_id)),
                "rel": "bookmark"
            },
            {
                "href": absolutize_url("/images/{0}"
                                       .format(self.image_id)),
                "type": "application/vnd.openstack.image",
                "rel": "alternate"
            }
        ]

    def brief_json(self, absolutize_url):
        """
        Brief JSON-serializable version of this flavor, for the non-details
        list flavors request.
        """
        return {
            "id": self.image_id,
            "links": self.links_json(absolutize_url),
            "name": self.name
        }

    def detailed_json(self, absolutize_url):
        """
        Long-form JSON-serializable object representation of this flavor, as
        returned by either a GET on this individual flavor or a member in the
        list returned by the list-details request.
        """
        template = {}
        template.update({
            "id": self.image_id,
            "links": self.links_json(absolutize_url),
            "name": self.name,
            "minRam": self.minRam,
            "minDisk": self.minDisk,
            "OS-EXT-IMG-SIZE:size": self.image_size,
            "com.rackspace__1__ui_default_show": self.is_default,
            "metadata": self.metadata_json()
        })
        return template


class RackspaceWindowsImage(Image):
    """
    A Rackspace window image object representation
    """
    images = {"Windows Server 2008 R2 SP1 + SQL Server 2008 R2 SP2 Standard":
              {"id": "a3b09eeb-e517-44d1-9d2e-85d77e989b95", "minRam": 2048, "minDisk": 40,
               "OS-EXT-IMG-SIZE:size": 9197298666, "com.rackspace__1__ui_default_show": "True"},
              "Windows Server 2008 R2 SP1 + SQL Server 2008 R2 SP2 Web":
              {"id": "0942f896-f608-4db0-b4ee-d79c29e653fb", "minRam": 2048, "minDisk": 40,
               "OS-EXT-IMG-SIZE:size": 9233375496, "com.rackspace__1__ui_default_show": "True"},
              "Windows Server 2008 R2 SP1":
              {"id": "d84bffa7-d4d4-4fd3-a7f7-06865e02467d", "minRam": 1024, "minDisk": 40,
               "OS-EXT-IMG-SIZE:size": 5558999671, "com.rackspace__1__ui_default_show": "True"},
              "Windows Server 2012 R2":
              {"id": "76964ffc-26eb-4a83-8301-50e77255b355", "minRam": 1024, "minDisk": 40,
               "OS-EXT-IMG-SIZE:size": 8892515079, "com.rackspace__1__ui_default_show": "True"},
              "Windows Server 2012 + SQL Server 2012 SP1 Web":
              {"id": "7fd9336e-f7fa-41ee-a6d7-7996c29cbfa4", "minRam": 2048, "minDisk": 40,
               "OS-EXT-IMG-SIZE:size": 17788699082, "com.rackspace__1__ui_default_show": "True"},
              "Windows Server 2012 + SQL Server 2012 SP1 Standard":
              {"id": "9b02a4ef-b0ea-4e29-b99f-b505dfe99fec", "minRam": 2048, "minDisk": 40,
               "OS-EXT-IMG-SIZE:size": 17781335222, "com.rackspace__1__ui_default_show": "True"},
              "Windows Server 2012 R2 + SQL Server 2014 Standard":
              {"id": "c91ae969-40a5-421a-8cb1-c32cb6998dd4", "minRam": 2048, "minDisk": 40,
               "OS-EXT-IMG-SIZE:size": 12135414967, "com.rackspace__1__ui_default_show": "True"},
              "Windows Server 2012 R2 + SQL Server 2014 Web":
              {"id": "beb3dfe6-ebb0-4943-bcea-65a3e11bb7bd", "minRam": 2048, "minDisk": 40,
               "OS-EXT-IMG-SIZE:size": 1213905689, "com.rackspace__1__ui_default_show": "True"},
              "Windows Server 2012":
              {"id": "03b70725-29c6-4d88-be2b-c19004b25c28", "minRam": 1024, "minDisk": 40,
               "OS-EXT-IMG-SIZE:size": 11465351762, "com.rackspace__1__ui_default_show": "True"}}

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": "*,!onmetal",
            "image_type": "base",
            "os_type": "windows",
            "status": "active",
            "org.openstack__1__os_distro": "com.microsoft.server"
        }


class RackspaceArchImage(Image):
    """
    A Rackspace Arch image object representation
    """
    images = {"Arch 2015.7 (PVHVM)": {"id": "ade87903-9d82-4584-9cc1-204870011de0",
                                      "minRam": 512, "minDisk": 20, "OS-EXT-IMG-SIZE:size": 1118936253}}

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": "*,!onmetal",
            "image_type": "base",
            "os_type": "linux",
            "status": "active",
            "org.openstack__1__os_distro": "org.archlinux",
            "vm_mode": "hvm",
            "auto_disk_config": "disabled"
        }


class RackspaceCentOSPVHMImage(Image):
    """
    A Rackspace CentOS HVM image object representation
    """
    images = {"CentOS 7 (PVHVM)": {"id": "c25f1ae0-30b3-4012-8ca6-5ecfcf05c965", "minRam": 512,
                                   "minDisk": 20, "OS-EXT-IMG-SIZE:size": 744797869,
                                   "com.rackspace__1__ui_default_show": "True"},
              "CentOS 6 (PVHVM)": {"id": "aa68fd54-2f9a-42c3-9901-4035e2738830", "minRam": 512,
                                   "minDisk": 20, "OS-EXT-IMG-SIZE:size": 412553321,
                                   "com.rackspace__1__ui_default_show": "True"}}

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": "*,!onmetal",
            "image_type": "base",
            "os_type": "linux",
            "status": "active",
            "org.openstack__1__os_distro": "org.centos",
            "vm_mode": "hvm",
            "auto_disk_config": "disabled"
        }


class RackspaceCentOSPVImage(Image):
    """
    A Rackspace CentOS Xen image object representation
    """
    images = {"CentOS 6 (PV)": {"id": "21612eaf-a350-4047-b06f-6bb8a8a7bd99", "minRam": 512,
                                "minDisk": 20, "OS-EXT-IMG-SIZE:size": 391598830},
              "CentOS 5 (PV)": {"id": "d75bc322-b02c-493d-b414-097b3bcce4dd", "minRam": 512,
                                "minDisk": 20, "OS-EXT-IMG-SIZE:size": 386227982}}

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": "*,!io1,!memory1,!compute1,!onmetal",
            "image_type": "base",
            "os_type": "linux",
            "status": "active",
            "org.openstack__1__os_distro": "org.centos",
            "vm_mode": "xen",
            "auto_disk_config": "True"
        }


class RackspaceCoreOSImage(Image):
    """
    A Rackspace CoreOS image object representation
    """
    images = {"CoreOS (Beta)": {"id": "7cf9f618-3dd3-4e3e-bace-e44d857039e2", "minRam": 512,
                                "minDisk": 20, "OS-EXT-IMG-SIZE:size": 223270688},
              "CoreOS (Alpha)": {"id": "6e4f6893-b973-4f91-b7e3-9f442a30a907", "minRam": 512,
                                 "minDisk": 20, "OS-EXT-IMG-SIZE:size": 239270643},
              "CoreOS (Stable)": {"id": "b05a6c75-158a-4fca-b5ad-fe9d644e04b4", "minRam": 512,
                                  "minDisk": 20, "OS-EXT-IMG-SIZE:size": 224241308,
                                  "com.rackspace__1__ui_default_show": "True"}}

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": "*,!onmetal",
            "image_type": "base",
            "os_type": "linux",
            "status": "active",
            "org.openstack__1__os_distro": "org.coreos",
            "vm_mode": "hvm",
            "auto_disk_config": "disabled"
        }


class RackspaceDebianImage(Image):
    """
    A Rackspace Debian image object representation
    """
    images = {"Debian 7 (Wheezy) (PVHVM)": {"id": "c934d497-7b45-4764-ac63-5b67e1458a20", "minRam": 512,
                                            "minDisk": 20, "OS-EXT-IMG-SIZE:size": 439983989,
                                            "com.rackspace__1__ui_default_show": "True"},
              "Debian Unstable (Sid) (PVHVM)": {"id": "498c59a0-3c26-4357-92c0-dd938baca3db",
                                                "minRam": 512, "minDisk": 20,
                                                "OS-EXT-IMG-SIZE:size": 1382255983},
              "Debian Testing (Stretch) (PVHVM)": {"id": "0535b46b-fae2-4813-945f-701949c53c2e",
                                                   "minRam": 512, "minDisk": 20,
                                                   "OS-EXT-IMG-SIZE:size": 959030762},
              "Debian 8 (Jessie) (PVHVM)": {"id": "19149d8b-bd6a-4b0b-a688-657780f9cf6c", "minRam": 512,
                                            "minDisk": 20, "OS-EXT-IMG-SIZE:size": 802692492,
                                            "com.rackspace__1__ui_default_show": "True"}}

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": "*,!onmetal",
            "image_type": "base",
            "os_type": "linux",
            "status": "active",
            "org.openstack__1__os_distro": "org.debian",
            "vm_mode": "hvm",
            "auto_disk_config": "disabled"
        }


class RackspaceFedoraImage(Image):
    """
    A Rackspace Fedora image object representation
    """
    images = {"Fedora 21 (PVHVM)": {"id": "6c21b351-e12a-4ddf-a0a0-a6849c2b0037", "minRam": 512,
                                    "minDisk": 20, "OS-EXT-IMG-SIZE:size": 737450719,
                                    "com.rackspace__1__ui_default_show": "True"},
              "Fedora 22 (PVHVM)": {"id": "2cc5db1b-2fc8-42ae-8afb-d30c68037f02", "minRam": 512,
                                    "minDisk": 20, "OS-EXT-IMG-SIZE:size": 880374707,
                                    "com.rackspace__1__ui_default_show": "True"}}

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": "*,!onmetal",
            "image_type": "base",
            "os_type": "linux",
            "status": "active",
            "org.openstack__1__os_distro": "org.fedoraproject",
            "vm_mode": "hvm",
            "auto_disk_config": "disabled"
        }


class RackspaceFreeBSDImage(Image):
    """
    A Rackspace FreeBSD image object representation
    """
    images = {"FreeBSD 10 (PVHVM)": {"id": "7a1cf8de-7721-4d56-900b-1e65def2ada5", "minRam": 512,
                                     "minDisk": 20, "OS-EXT-IMG-SIZE:size": 1709540218}}

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": "*,!onmetal",
            "image_type": "base",
            "os_type": "linux",
            "status": "active",
            "org.openstack__1__os_distro": "org.freebsd",
            "vm_mode": "hvm",
            "auto_disk_config": "disabled"
        }


class RackspaceGentooImage(Image):
    """
    A Rackspace Gentoo image object representation
    """
    images = {"Gentoo 15.3 (PVHVM)": {"id": "168c1be2-a3b0-423f-a619-f63cce550063", "minRam": 512,
                                      "minDisk": 20, "OS-EXT-IMG-SIZE:size": 1116159799}}

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": "*,!onmetal",
            "image_type": "base",
            "os_type": "linux",
            "org.openstack__1__os_distro": "org.gentoo",
            "vm_mode": "hvm",
            "auto_disk_config": "disabled"
        }


class RackspaceOpenSUSEImage(Image):
    """
    A Rackspace OpenSUSE image object representation
    """
    images = {"OpenSUSE 13.2 (PVHVM)": {"id": "3cdcd2cc-238c-4f42-a9f4-0a80de217f7a", "minRam": 512,
                                        "minDisk": 20, "OS-EXT-IMG-SIZE:size": 437580692}}

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": "*,!onmetal",
            "image_type": "base",
            "os_type": "linux",
            "org.openstack__1__os_distro": "org.opensuse",
            "vm_mode": "hvm",
            "auto_disk_config": "disabled"
        }


class RackspaceRedHatPVHMImage(Image):
    """
    A Rackspace Red Hat image object representation
    """
    images = {"Red Hat Enterprise Linux 7 (PVHVM)": {"id": "bcc314ad-d971-4753-aea4-8b54d6219dfd",
                                                     "minRam": 512, "minDisk": 20,
                                                     "OS-EXT-IMG-SIZE:size": 542059457,
                                                     "com.rackspace__1__ui_default_show": "True"},
              "Red Hat Enterprise Linux 6 (PVHVM)": {"id": "8e3d8c5b-ac07-429f-8304-d2863e1a0636",
                                                     "minRam": 512, "minDisk": 20,
                                                     "OS-EXT-IMG-SIZE:size": 560196835,
                                                     "com.rackspace__1__ui_default_show": "True"}}

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": "*,!onmetal",
            "image_type": "base",
            "os_type": "linux",
            "org.openstack__1__os_distro": "org.redhat",
            "vm_mode": "hvm",
            "auto_disk_config": "disabled"
        }


class RackspaceRedHatPVImage(Image):
    """
    A Rackspace Red Hat image object representation
    """
    images = {"Red Hat Enterprise Linux 6 (PV)": {"id": "783f71f4-d2d8-4d38-b2e1-8c916de79a38",
                                                  "minRam": 512, "minDisk": 20,
                                                  "OS-EXT-IMG-SIZE:size": 558463946},
              "Red Hat Enterprise Linux 5 (PV)": {"id": "05dd965d-84ce-451b-9ca1-83a134e523c3",
                                                  "minRam": 512, "minDisk": 20,
                                                  "OS-EXT-IMG-SIZE:size": 540490883}}

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": "*,!io1,!memory1,!compute1,!onmetal",
            "image_type": "base",
            "os_type": "linux",
            "org.openstack__1__os_distro": "org.redhat",
            "vm_mode": "xen",
            "auto_disk_config": "True"
        }


class RackspaceScientificImage(Image):
    """
    A Rackspace Scientific image object representation
    """
    images = {"Scientific Linux 6 (PVHVM)": {"id": "36076d08-3e8b-4436-9253-7a8868e4f4d7",
                                             "minRam": 512, "minDisk": 20,
                                             "OS-EXT-IMG-SIZE:size": 597289694},
              "Scientific Linux 7 (PVHVM)": {"id": "ab5c119f-50ab-4213-b969-19b1853d41b0",
                                             "minRam": 512, "minDisk": 20,
                                             "OS-EXT-IMG-SIZE:size": 817457670}}

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": "*,!onmetal",
            "image_type": "base",
            "os_type": "linux",
            "org.openstack__1__os_distro": "org.scientificlinux",
            "vm_mode": "hvm",
            "auto_disk_config": "disabled"
        }


class RackspaceUbuntuPVHMImage(Image):
    """
    A Rackspace Ubuntu image object representation
    """
    images = {"Ubuntu 15.04 (Vivid Vervet) (PVHVM)": {"id": "315b2dc-23fc-4d81-9e73-aa620357e1d8",
                                                      "minRam": 512, "minDisk": 20,
                                                      "OS-EXT-IMG-SIZE:size": 784546403,
                                                      "com.rackspace__1__ui_default_show": "True"},
              "Ubuntu 12.04 LTS (Precise Pangolin) (PVHVM)":
                  {"id": "973775ab-0653-4ef8-a571-7a2777787735", "minRam": 512, "minDisk": 20,
                   "OS-EXT-IMG-SIZE:size": 675261892, "com.rackspace__1__ui_default_show": "True"},
              "Ubuntu 14.04 LTS (Trusty Tahr) (PVHVM)": {"id": "09de0a66-3156-48b4-90a5-1cf25a905207",
                                                         "minRam": 512, "minDisk": 20,
                                                         "OS-EXT-IMG-SIZE:size": 752229456,
                                                         "com.rackspace__1__ui_default_show": "True"}}

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": "*,!onmetal",
            "image_type": "base",
            "os_type": "linux",
            "org.openstack__1__os_distro": "org.ubuntu",
            "vm_mode": "hvm",
            "auto_disk_config": "disabled"
        }


class RackspaceUbuntuPVImage(Image):
    """
    A Rackspace Ubuntu image object representation
    """
    images = {"Ubuntu 12.04 LTS (Precise Pangolin) (PV)": {"id": "656e65f7-6441-46e8-978d-0d39beaaf559",
                                                           "minRam": 512, "minDisk": 20,
                                                           "OS-EXT-IMG-SIZE:size": 495724402},
              "Ubuntu 14.04 LTS (Trusty Tahr) (PV)": {"id": "5ed162cc-b4eb-4371-b24a-a0ae73376c73",
                                                      "minRam": 512, "minDisk": 20,
                                                      "OS-EXT-IMG-SIZE:size": 1132769776}}

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": "*,!io1,!memory1,!compute1,!onmetal",
            "image_type": "base",
            "os_type": "linux",
            "org.openstack__1__os_distro": "org.ubuntu",
            "vm_mode": "xen",
            "auto_disk_config": "True"
        }


class RackspaceVyattaImage(Image):
    """
    A Rackspace Vyatta image object representation
    """
    images = {"Vyatta Network OS 6.7R9": {"id": "faad95b7-396d-483e-b4ae-77afec7e7097",
                                          "minRam": 1024, "minDisk": 20,
                                          "OS-EXT-IMG-SIZE:size": 284134170,
                                          "com.rackspace__1__ui_default_show": "True"}}

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": "*,!io1,!memory1,!compute1,!onmetal",
            "image_type": "base",
            "os_type": "linux",
            "org.openstack__1__os_distro": "org.vyatta",
            "vm_mode": "xen",
            "auto_disk_config": "False"
        }


@attributes(['image_id', 'tenant_id', 'name', 'minDisk', 'minRam', 'image_size'])
class OnMetalImage(object):
    """
    A Image object
    """

    is_default = False

    def set_is_default(self):
        """
        Sets image as a default
        """
        self.is_default = True

    def links_json(self, absolutize_url):
        """
        Create a JSON-serializable data structure describing the links to this
        image.
        """
        return [
            {
                "href": absolutize_url("v2/{0}/images/{1}"
                                       .format(self.tenant_id, self.image_id)),
                "rel": "self"
            },
            {
                "href": absolutize_url("{0}/images/{1}"
                                       .format(self.tenant_id, self.image_id)),
                "rel": "bookmark"
            },
            {
                "href": absolutize_url("/images/{0}"
                                       .format(self.image_id)),
                "type": "application/vnd.openstack.image",
                "rel": "alternate"
            }
        ]

    def brief_json(self, absolutize_url):
        """
        Brief JSON-serializable version of this flavor, for the non-details
        list flavors request.
        """
        return {
            "id": self.image_id,
            "links": self.links_json(absolutize_url),
            "name": self.name
        }

    def detailed_json(self, absolutize_url):
        """
        Long-form JSON-serializable object representation of this flavor, as
        returned by either a GET on this individual flavor or a member in the
        list returned by the list-details request.
        """
        template = {}
        template.update({
            "id": self.image_id,
            "links": self.links_json(absolutize_url),
            "name": self.name,
            "minRam": self.minRam,
            "minDisk": self.minDisk,
            "OS-EXT-IMG-SIZE:size": self.image_size,
            "com.rackspace__1__ui_default_show": self.is_default,
            "metadata": self.metadata_json()
        })
        return template


class RackspaceOnMetalCoreOSImage(OnMetalImage):
    """
    A Rackspace OnMetal image object representation
    """
    images = {"OnMetal - CoreOS (Alpha)": {"id": "4005b86a-2acf-4a3f-be41-44fefb87e9ae",
                                           "minRam": 512, "minDisk": 20,
                                           "OS-EXT-IMG-SIZE:size": 243990528},
              "OnMetal - CoreOS (Beta)": {"id": "4c8ddca8-6a94-4151-b090-a89ebc7143b8",
                                          "minRam": 512, "minDisk": 20,
                                          "OS-EXT-IMG-SIZE:size": 225771520},
              "OnMetal - CoreOS (Stable)": {"id": "584b1869-a204-4572-925c-e6aec423f1e4",
                                            "minRam": 512, "minDisk": 20,
                                            "OS-EXT-IMG-SIZE:size": 225837056}}

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": "onmetal",
            "image_type": "base",
            "os_type": "linux",
            "org.openstack__1__os_distro": "org.coreos",
            "vm_mode": "metal",
            "auto_disk_config": "disabled"
        }


class RackspaceOnMetalFedoraImage(OnMetalImage):
    """
    A Rackspace OnMetal image object representation
    """
    images = {"OnMetal - Fedora 22": {"id": "4c361a4a-51b4-4e29-8a35-3b0e25e49ee1",
                                      "minRam": 512, "minDisk": 20,
                                      "OS-EXT-IMG-SIZE:size": 908975616},
              "OnMetal - Fedora 21": {"id": "dfce8398-39f0-40a1-99fe-6323ea3641c8",
                                      "minRam": 512, "minDisk": 20,
                                      "OS-EXT-IMG-SIZE:size": 771769344}}

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": "onmetal",
            "image_type": "base",
            "os_type": "linux",
            "org.openstack__1__os_distro": "org.fedoraproject",
            "vm_mode": "metal",
            "auto_disk_config": "disabled"
        }


class RackspaceOnMetalDebianImage(OnMetalImage):
    """
    A Rackspace OnMetal image object representation
    """
    images = {"OnMetal - Debian Testing (Stretch)": {"id": "7d868900-a87c-423a-8e67-82ff5a9e3c17",
                                                     "minRam": 512, "minDisk": 20,
                                                     "OS-EXT-IMG-SIZE:size": 1005798400},
              "OnMetal - Debian Unstable (Sid)": {"id": "2185df36-658f-4803-b82f-d21195c91e21",
                                                  "minRam": 512, "minDisk": 20,
                                                  "OS-EXT-IMG-SIZE:size": 1294536192},
              "OnMetal - Debian 8 (Jessie)": {"id": "413e3ac5-5d45-4502-a274-ff6a436450fd",
                                              "minRam": 512, "minDisk": 20,
                                              "OS-EXT-IMG-SIZE:size": 894276608},
              "OnMetal - Debian 7 (Wheezy)": {"id": "8390b329-a097-4dc6-87b6-7c48e7157f2a",
                                              "minRam": 512, "minDisk": 20,
                                              "OS-EXT-IMG-SIZE:size": 642673152}}

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": "onmetal",
            "image_type": "base",
            "os_type": "linux",
            "org.openstack__1__os_distro": "org.debian",
            "vm_mode": "metal",
            "auto_disk_config": "disabled"
        }


class RackspaceOnMetalUbuntuImage(OnMetalImage):
    """
    A Rackspace OnMetal image object representation
    """
    images = {"OnMetal - Ubuntu 15.04 (Vivid Vervet)": {"id": "458e08d7-d230-41a7-9aa2-335129d2e49c",
                                                        "minRam": 512, "minDisk": 20,
                                                        "OS-EXT-IMG-SIZE:size": 891264512},
              "OnMetal - Ubuntu 14.04 LTS (Trusty Tahr)": {"id": "fb508530-2500-4a30-a947-038491df2bb5",
                                                           "minRam": 512, "minDisk": 20,
                                                           "OS-EXT-IMG-SIZE:size": 807227392},
              "OnMetal - Ubuntu 12.04 LTS (Precise Pangolin)":
                  {"id": "eb6f98a3-5f5d-4153-a011-99823e076dd7", "minRam": 512, "minDisk": 20,
                   "OS-EXT-IMG-SIZE:size": 727487488}}

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": "onmetal",
            "image_type": "base",
            "os_type": "linux",
            "org.openstack__1__os_distro": "org.ubuntu",
            "vm_mode": "metal",
            "auto_disk_config": "disabled"
        }


class RackspaceOnMetalCentOSImage(OnMetalImage):
    """
    A Rackspace OnMetal image object representation
    """
    images = {"OnMetal - CentOS 6": {"id": "b5960c04-86ae-4824-9f04-1eb32a8989a5",
                                     "minRam": 512, "minDisk": 20,
                                     "OS-EXT-IMG-SIZE:size": 433520640},
              "OnMetal - CentOS 7": {"id": "25c5ed29-698e-4acb-91e7-40abc4ac5ea9",
                                     "minRam": 512, "minDisk": 20,
                                     "OS-EXT-IMG-SIZE:size": 724649984}}

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": "onmetal",
            "image_type": "base",
            "os_type": "linux",
            "org.openstack__1__os_distro": "org.centos",
            "vm_mode": "metal",
            "auto_disk_config": "disabled"
        }
