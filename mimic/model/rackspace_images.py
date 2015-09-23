"""
Model objects for mimic images.
"""

from characteristic import attributes
import uuid


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

    @classmethod
    def image_id(cls):
        """
        Create a unique id for an image
        """
        return str(uuid.uuid4())

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
        template = {}
        template.update({
            "id": self.image_id,
            "links": self.links_json(absolutize_url),
            "name": self.name
        })
        return template

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
              {"minRam": 2048, "minDisk": 40, "OS-EXT-IMG-SIZE:size": 9197298666, "id": Image.image_id(),
               "com.rackspace__1__ui_default_show": "True"},
              "Windows Server 2008 R2 SP1 + SQL Server 2008 R2 SP2 Web":
              {"minRam": 2048, "minDisk": 40, "id": Image.image_id(),
               "OS-EXT-IMG-SIZE:size": 9233375496, "com.rackspace__1__ui_default_show": "True"},
              "Windows Server 2008 R2 SP1":
              {"minRam": 1024, "minDisk": 40, "id": Image.image_id(),
               "OS-EXT-IMG-SIZE:size": 5558999671, "com.rackspace__1__ui_default_show": "True"},
              "Windows Server 2012 R2":
              {"minRam": 1024, "minDisk": 40, "id": Image.image_id(),
               "OS-EXT-IMG-SIZE:size": 8892515079, "com.rackspace__1__ui_default_show": "True"},
              "Windows Server 2012 + SQL Server 2012 SP1 Web":
              {"minRam": 2048, "minDisk": 40, "id": Image.image_id(),
               "OS-EXT-IMG-SIZE:size": 17788699082, "com.rackspace__1__ui_default_show": "True"},
              "Windows Server 2012 + SQL Server 2012 SP1 Standard":
              {"minRam": 2048, "minDisk": 40, "id": Image.image_id(),
               "OS-EXT-IMG-SIZE:size": 17781335222, "com.rackspace__1__ui_default_show": "True"},
              "Windows Server 2012 R2 + SQL Server 2014 Standard":
              {"minRam": 2048, "minDisk": 40, "id": Image.image_id(),
               "OS-EXT-IMG-SIZE:size": 12135414967, "com.rackspace__1__ui_default_show": "True"},
              "Windows Server 2012 R2 + SQL Server 2014 Web":
              {"minRam": 2048, "minDisk": 40, "id": Image.image_id(),
               "OS-EXT-IMG-SIZE:size": 12139059689, "com.rackspace__1__ui_default_show": "True"},
              "Windows Server 2012":
              {"minRam": 1024, "minDisk": 40, "id": Image.image_id(),
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
    images = {"Arch 2015.7 (PVHVM)": {"minRam": 512, "minDisk": 20, "OS-EXT-IMG-SIZE:size": 1118936253,
                                      "id": Image.image_id()}}

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
    images = {"CentOS 7 (PVHVM)": {"minRam": 512, "minDisk": 20, "OS-EXT-IMG-SIZE:size": 744797869,
                                   "com.rackspace__1__ui_default_show": "True", "id": Image.image_id()},
              "CentOS 6 (PVHVM)": {"minRam": 512, "minDisk": 20, "OS-EXT-IMG-SIZE:size": 412553321,
                                   "com.rackspace__1__ui_default_show": "True", "id": Image.image_id()}}

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
    images = {"CentOS 6 (PV)": {"minRam": 512, "minDisk": 20, "OS-EXT-IMG-SIZE:size": 391598830,
                                "id": Image.image_id()},
              "CentOS 5 (PV)": {"minRam": 512, "minDisk": 20, "OS-EXT-IMG-SIZE:size": 386227982,
                                "id": Image.image_id()}}

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
    images = {"CoreOS (Beta)": {"minRam": 512, "minDisk": 20, "OS-EXT-IMG-SIZE:size": 217868501,
                                "id": Image.image_id()},
              "CoreOS (Alpha)": {"minRam": 512, "minDisk": 20, "OS-EXT-IMG-SIZE:size": 239664114,
                                 "id": Image.image_id()},
              "CoreOS (Stable)": {"minRam": 512, "minDisk": 20, "OS-EXT-IMG-SIZE:size": 224241308,
                                  "com.rackspace__1__ui_default_show": "True", "id": Image.image_id()}}

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
    images = {"Debian 7 (Wheezy) (PVHVM)": {"minRam": 512, "minDisk": 20, "id": Image.image_id(),
                                            "OS-EXT-IMG-SIZE:size": 439983989,
                                            "com.rackspace__1__ui_default_show": "True"},
              "Debian Unstable (Sid) (PVHVM)": {"minRam": 512, "minDisk": 20, "id": Image.image_id(),
                                                "OS-EXT-IMG-SIZE:size": 1382255983},
              "Debian Testing (Stretch) (PVHVM)": {"minRam": 512, "minDisk": 20, "id": Image.image_id(),
                                                   "OS-EXT-IMG-SIZE:size": 959030762},
              "Debian 8 (Jessie) (PVHVM)": {"minRam": 512, "minDisk": 20, "id": Image.image_id(),
                                            "OS-EXT-IMG-SIZE:size": 802692492,
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
    images = {"Fedora 21 (PVHVM)": {"minRam": 512, "minDisk": 20, "OS-EXT-IMG-SIZE:size": 737450719,
                                    "com.rackspace__1__ui_default_show": "True",
                                    "id": Image.image_id()},
              "Fedora 22 (PVHVM)": {"minRam": 512, "minDisk": 20, "OS-EXT-IMG-SIZE:size": 880374707,
                                    "com.rackspace__1__ui_default_show": "True",
                                    "id": Image.image_id()}}

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
    images = {"FreeBSD 10 (PVHVM)": {"minRam": 512, "minDisk": 20, "OS-EXT-IMG-SIZE:size": 1709540218,
                                     "id": Image.image_id()}}

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
    images = {"Gentoo 15.3 (PVHVM)": {"minRam": 512, "minDisk": 20, "OS-EXT-IMG-SIZE:size": 1116159799,
                                      "id": Image.image_id()}}

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
    images = {"OpenSUSE 13.2 (PVHVM)": {"minRam": 512, "minDisk": 20, "OS-EXT-IMG-SIZE:size": 437580692,
                                        "id": Image.image_id()}}

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
    images = {"Red Hat Enterprise Linux 7 (PVHVM)": {"minRam": 512, "minDisk": 20,
                                                     "OS-EXT-IMG-SIZE:size": 542059457,
                                                     "com.rackspace__1__ui_default_show": "True",
                                                     "id": Image.image_id()},
              "Red Hat Enterprise Linux 6 (PVHVM)": {"minRam": 512, "minDisk": 20,
                                                     "OS-EXT-IMG-SIZE:size": 560196835,
                                                     "com.rackspace__1__ui_default_show": "True",
                                                     "id": Image.image_id()}}

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
    images = {"Red Hat Enterprise Linux 6 (PV)": {"minRam": 512, "minDisk": 20, "id": Image.image_id(),
                                                  "OS-EXT-IMG-SIZE:size": 558463946},
              "Red Hat Enterprise Linux 5 (PV)": {"minRam": 512, "minDisk": 20, "id": Image.image_id(),
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
    images = {"Scientific Linux 6 (PVHVM)": {"minRam": 512, "minDisk": 20, "id": Image.image_id(),
                                             "OS-EXT-IMG-SIZE:size": 597289694},
              "Scientific Linux 7 (PVHVM)": {"minRam": 512, "minDisk": 20, "id": Image.image_id(),
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
    images = {"Ubuntu 15.04 (Vivid Vervet) (PVHVM)": {"minRam": 512, "minDisk": 20,
                                                      "id": Image.image_id(),
                                                      "OS-EXT-IMG-SIZE:size": 784546403,
                                                      "com.rackspace__1__ui_default_show": "True"},
              "Ubuntu 12.04 LTS (Precise Pangolin) (PVHVM)":
                  {"minRam": 512, "minDisk": 20, "OS-EXT-IMG-SIZE:size": 675261892,
                   "id": Image.image_id(), "com.rackspace__1__ui_default_show": "True"},
              "Ubuntu 14.04 LTS (Trusty Tahr) (PVHVM)": {"minRam": 512, "minDisk": 20,
                                                         "OS-EXT-IMG-SIZE:size": 752229456,
                                                         "id": Image.image_id(),
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
    images = {"Ubuntu 12.04 LTS (Precise Pangolin) (PV)": {"minRam": 512, "minDisk": 20,
                                                           "id": Image.image_id(),
                                                           "OS-EXT-IMG-SIZE:size": 495724402},
              "Ubuntu 14.04 LTS (Trusty Tahr) (PV)": {"minRam": 512, "minDisk": 20,
                                                      "id": Image.image_id(),
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
    images = {"Vyatta Network OS 6.7R9": {"minRam": 1024, "minDisk": 20, "id": Image.image_id(),
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
    images = {"OnMetal - CoreOS (Alpha)": {"minRam": 512, "minDisk": 20, "id": Image.image_id(),
                                           "OS-EXT-IMG-SIZE:size": 244187136},
              "OnMetal - CoreOS (Beta)": {"minRam": 512, "minDisk": 20, "id": Image.image_id(),
                                          "OS-EXT-IMG-SIZE:size": 220463104},
              "OnMetal - CoreOS (Stable)": {"minRam": 512, "minDisk": 20, "id": Image.image_id(),
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
    images = {"OnMetal - Fedora 22": {"minRam": 512, "minDisk": 20, "id": Image.image_id(),
                                      "OS-EXT-IMG-SIZE:size": 908975616},
              "OnMetal - Fedora 21": {"minRam": 512, "minDisk": 20, "id": Image.image_id(),
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
    images = {"OnMetal - Debian Testing (Stretch)": {"minRam": 512, "minDisk": 20,
                                                     "id": Image.image_id(),
                                                     "OS-EXT-IMG-SIZE:size": 1005798400},
              "OnMetal - Debian Unstable (Sid)": {"minRam": 512, "minDisk": 20,
                                                  "id": Image.image_id(),
                                                  "OS-EXT-IMG-SIZE:size": 1294536192},
              "OnMetal - Debian 8 (Jessie)": {"minRam": 512, "minDisk": 20,
                                              "id": Image.image_id(),
                                              "OS-EXT-IMG-SIZE:size": 894276608},
              "OnMetal - Debian 7 (Wheezy)": {"minRam": 512, "minDisk": 20,
                                              "id": Image.image_id(),
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
    images = {"OnMetal - Ubuntu 15.04 (Vivid Vervet)": {"minRam": 512, "minDisk": 20,
                                                        "id": Image.image_id(),
                                                        "OS-EXT-IMG-SIZE:size": 891264512},
              "OnMetal - Ubuntu 14.04 LTS (Trusty Tahr)": {"minRam": 512, "minDisk": 20,
                                                           "id": Image.image_id(),
                                                           "OS-EXT-IMG-SIZE:size": 807227392},
              "OnMetal - Ubuntu 12.04 LTS (Precise Pangolin)": {"minRam": 512, "minDisk": 20,
                                                                "id": Image.image_id(),
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
    images = {"OnMetal - CentOS 6": {"minRam": 512, "minDisk": 20, "id": Image.image_id(),
                                     "OS-EXT-IMG-SIZE:size": 433520640},
              "OnMetal - CentOS 7": {"minRam": 512, "minDisk": 20, "id": Image.image_id(),
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


class ImageStore(object):
    """
    A store for images to share between nova_api and glance_api
    """
    _images_store = []

    @classmethod
    def create_image_store(cls, tenant_id):
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
        if len(cls._images_store) < 1:
            for image_class in image_classes:
                for image, image_spec in image_class.images.iteritems():
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
                    cls._images_store.append(image)
        return cls._images_store
