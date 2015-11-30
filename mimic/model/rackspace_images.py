"""
Model objects for mimic images.
"""

from __future__ import absolute_import, division, unicode_literals

from characteristic import attributes, Attribute
import uuid
import random


def new_random_image_id():
    """
    Create a unique id for an image
    """
    return str(uuid.uuid4())


def random_image_size():
    """
    Generate a random size for images
    """
    return random.randint(250000, 80000000000)


@attributes([
    # Prior to refactor; no default value
    'image_id', 'tenant_id', 'name', 'minDisk', 'minRam', 'image_size',
    # Post-refactor; all have default values, but these should be slowly
    # removed.
    Attribute('flavor_classes', default_value="*"),
    Attribute('image_type', default_value="base"),
    Attribute('os_type', default_value="linux"),
    Attribute('os_distro', default_value=""),
    Attribute('vm_mode', default_value="hvm"),
    Attribute('auto_disk_config', default_value="disabled"),
])
class Image(object):
    """
    A Image object

    :ivar str flavor_classes: rackspace-specific metadata; a string describing
        the flavor classes which apply to this image; this is (probably?)
    :ivar str image_type: a string describing the type of image, possible
        values are "base" meaning a public cloud image created by the cloud
        provider, and "snapshot", which is created from a running server.
    :ivar str os_type: rackspace-specific metadata; the operating system name,
        such as "linux" or "windows"
    :ivar str os_distro: an identifier for the the distribution vendor of the
        operating system, such as "org.archlinux".
    :ivar str vm_mode: the virtualization mode used with this image; possible
        values: "hvm", "xen" or "metal" (for OnMetal).
    :ivar str auto_disk_config: whether automatic disk configuration is used
        with this image; possible values: "True", "disabled", and "False".
        (TODO: what does "False" mean?)
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
        template = {}
        template.update({
            "id": self.image_id,
            "links": self.links_json(absolutize_url),
            "name": self.name
        })
        return template

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": self.flavor_classes,
            "image_type": self.image_type,
            "os_type": self.os_type,
            "org.openstack__1__os_distro": self.os_distro,
            "vm_mode": self.vm_mode,
            "auto_disk_config": self.auto_disk_config
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
            "created": "1972-01-01_15-59-11",
            "updated": "1972-01-01_15-59-11",
            "progress": 100,
            "status": "ACTIVE",
            "metadata": self.metadata_json()
        })
        return template


@attributes(['image_id', 'tenant_id', 'name', 'minDisk', 'minRam', 'image_size', 'server_id', 'links',
             'flavor_classes', 'os_type', 'os_distro', 'vm_mode', 'disk_config'])
class RackspaceSavedImage(object):
    """
    A Rackspace saved image object representation
    """
    is_default = False

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "image_type": "snapshot",
            "flavor_classes": self.flavor_classes,
            "os_type": self.os_type,
            "org.openstack__1__os_distro": self.os_distro,
            "vm_mode": self.vm_mode,
            "auto_disk_config": self.disk_config
        }

    def server_json(self):
        """
        Create a JSON-serializable data structure describing ``server`` info for a saved image
        """
        return {
            "id": self.server_id,
            "links": self.links
        }

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

    def detailed_json(self, absolutize_url):
        """
        Long-form JSON-serializable object representation of this flavor, as
        returned by either a GET on this individual flavor or a member in the
        list returned by the list-details request.
        """
        template = {}
        template.update({
            "id": self.image_id,
            "status": "ACTIVE",
            "links": self.links_json(absolutize_url),
            "name": self.name,
            "minRam": self.minRam,
            "minDisk": self.minDisk,
            "OS-EXT-IMG-SIZE:size": self.image_size,
            "com.rackspace__1__ui_default_show": self.is_default,
            "server": self.server_json(),
            "metadata": self.metadata_json()
        })
        return template


class RackspaceWindowsImage(Image):
    """
    A Rackspace window image object representation
    """
    images = {"Windows Server 2008 R2 SP1 + SQL Server 2008 R2 SP2 Standard":
              {"minRam": 2048, "minDisk": 40, "OS-EXT-IMG-SIZE:size": random_image_size(),
               "id": new_random_image_id(), "com.rackspace__1__ui_default_show": "True"},
              "Windows Server 2008 R2 SP1 + SQL Server 2008 R2 SP2 Web":
              {"minRam": 2048, "minDisk": 40, "id": new_random_image_id(),
               "OS-EXT-IMG-SIZE:size": random_image_size(), "com.rackspace__1__ui_default_show": "True"},
              "Windows Server 2008 R2 SP1":
              {"minRam": 1024, "minDisk": 40, "id": new_random_image_id(),
               "OS-EXT-IMG-SIZE:size": random_image_size(), "com.rackspace__1__ui_default_show": "True"},
              "Windows Server 2012 R2":
              {"minRam": 1024, "minDisk": 40, "id": new_random_image_id(),
               "OS-EXT-IMG-SIZE:size": random_image_size(), "com.rackspace__1__ui_default_show": "True"},
              "Windows Server 2012 + SQL Server 2012 SP1 Web":
              {"minRam": 2048, "minDisk": 40, "id": new_random_image_id(),
               "OS-EXT-IMG-SIZE:size": random_image_size(), "com.rackspace__1__ui_default_show": "True"},
              "Windows Server 2012 + SQL Server 2012 SP1 Standard":
              {"minRam": 2048, "minDisk": 40, "id": new_random_image_id(),
               "OS-EXT-IMG-SIZE:size": random_image_size(), "com.rackspace__1__ui_default_show": "True"},
              "Windows Server 2012 R2 + SQL Server 2014 Standard":
              {"minRam": 2048, "minDisk": 40, "id": new_random_image_id(),
               "OS-EXT-IMG-SIZE:size": random_image_size(), "com.rackspace__1__ui_default_show": "True"},
              "Windows Server 2012 R2 + SQL Server 2014 Web":
              {"minRam": 2048, "minDisk": 40, "id": new_random_image_id(),
               "OS-EXT-IMG-SIZE:size": random_image_size(), "com.rackspace__1__ui_default_show": "True"},
              "Windows Server 2012":
              {"minRam": 1024, "minDisk": 40, "id": new_random_image_id(),
               "OS-EXT-IMG-SIZE:size": random_image_size(), "com.rackspace__1__ui_default_show": "True"}}

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": "*,!onmetal",
            "image_type": "base",
            "os_type": "windows",
            "vm_mode": "",
            "auto_disk_config": "disabled",
            "org.openstack__1__os_distro": "com.microsoft.server"
        }


def create_rackspace_images(tenant_id):
    """
    Create :obj:`Image` instances as they would appear in the rackspace public
    cloud.
    """
    return [
        Image(
            tenant_id=tenant_id,
            name="Arch 2015.7 (PVHVM)",
            image_id=new_random_image_id(),
            image_size=random_image_size(),
            minRam=512, minDisk=20,
            flavor_classes="*,!onmetal",
            os_type="linux",
            os_distro="org.archlinux",
            vm_mode="hvm",
            auto_disk_config="disabled",
        )
    ]


class RackspaceCentOSPVHMImage(Image):
    """
    A Rackspace CentOS HVM image object representation
    """
    images = {"CentOS 7 (PVHVM)": {"minRam": 512, "minDisk": 20,
                                   "OS-EXT-IMG-SIZE:size": random_image_size(),
                                   "com.rackspace__1__ui_default_show": "True",
                                   "id": new_random_image_id()},
              "CentOS 6 (PVHVM)": {"minRam": 512, "minDisk": 20,
                                   "OS-EXT-IMG-SIZE:size": random_image_size(),
                                   "com.rackspace__1__ui_default_show": "True",
                                   "id": new_random_image_id()}}

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": "*,!onmetal",
            "image_type": "base",
            "os_type": "linux",
            "org.openstack__1__os_distro": "org.centos",
            "vm_mode": "hvm",
            "auto_disk_config": "disabled"
        }


class RackspaceCentOSPVImage(Image):
    """
    A Rackspace CentOS Xen image object representation
    """
    images = {"CentOS 6 (PV)": {"minRam": 512, "minDisk": 20,
                                "OS-EXT-IMG-SIZE:size": random_image_size(),
                                "id": new_random_image_id()},
              "CentOS 5 (PV)": {"minRam": 512, "minDisk": 20,
                                "OS-EXT-IMG-SIZE:size": random_image_size(),
                                "id": new_random_image_id()}}

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": "*,!io1,!memory1,!compute1,!onmetal",
            "image_type": "base",
            "os_type": "linux",
            "org.openstack__1__os_distro": "org.centos",
            "vm_mode": "xen",
            "auto_disk_config": "True"
        }


class RackspaceCoreOSImage(Image):
    """
    A Rackspace CoreOS image object representation
    """
    images = {"CoreOS (Beta)": {"minRam": 512, "minDisk": 20,
                                "OS-EXT-IMG-SIZE:size": random_image_size(),
                                "id": new_random_image_id()},
              "CoreOS (Alpha)": {"minRam": 512, "minDisk": 20,
                                 "OS-EXT-IMG-SIZE:size": random_image_size(),
                                 "id": new_random_image_id()},
              "CoreOS (Stable)": {"minRam": 512, "minDisk": 20,
                                  "OS-EXT-IMG-SIZE:size": random_image_size(),
                                  "com.rackspace__1__ui_default_show": "True",
                                  "id": new_random_image_id()}}

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": "*,!onmetal",
            "image_type": "base",
            "os_type": "linux",
            "org.openstack__1__os_distro": "org.coreos",
            "vm_mode": "hvm",
            "auto_disk_config": "disabled"
        }


class RackspaceDebianImage(Image):
    """
    A Rackspace Debian image object representation
    """
    images = {"Debian 7 (Wheezy) (PVHVM)": {"minRam": 512, "minDisk": 20, "id": new_random_image_id(),
                                            "OS-EXT-IMG-SIZE:size": random_image_size(),
                                            "com.rackspace__1__ui_default_show": "True"},
              "Debian Unstable (Sid) (PVHVM)": {"minRam": 512, "minDisk": 20,
                                                "id": new_random_image_id(),
                                                "OS-EXT-IMG-SIZE:size": random_image_size()},
              "Debian Testing (Stretch) (PVHVM)": {"minRam": 512, "minDisk": 20,
                                                   "id": new_random_image_id(),
                                                   "OS-EXT-IMG-SIZE:size": random_image_size()},
              "Debian 8 (Jessie) (PVHVM)": {"minRam": 512, "minDisk": 20, "id": new_random_image_id(),
                                            "OS-EXT-IMG-SIZE:size": random_image_size(),
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
            "org.openstack__1__os_distro": "org.debian",
            "vm_mode": "hvm",
            "auto_disk_config": "disabled"
        }


class RackspaceFedoraImage(Image):
    """
    A Rackspace Fedora image object representation
    """
    images = {"Fedora 21 (PVHVM)": {"minRam": 512, "minDisk": 20,
                                    "OS-EXT-IMG-SIZE:size": random_image_size(),
                                    "com.rackspace__1__ui_default_show": "True",
                                    "id": new_random_image_id()},
              "Fedora 22 (PVHVM)": {"minRam": 512, "minDisk": 20,
                                    "OS-EXT-IMG-SIZE:size": random_image_size(),
                                    "com.rackspace__1__ui_default_show": "True",
                                    "id": new_random_image_id()}}

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": "*,!onmetal",
            "image_type": "base",
            "os_type": "linux",
            "org.openstack__1__os_distro": "org.fedoraproject",
            "vm_mode": "hvm",
            "auto_disk_config": "disabled"
        }


class RackspaceFreeBSDImage(Image):
    """
    A Rackspace FreeBSD image object representation
    """
    images = {"FreeBSD 10 (PVHVM)": {"minRam": 512, "minDisk": 20,
                                     "OS-EXT-IMG-SIZE:size": random_image_size(),
                                     "id": new_random_image_id()}}

    def metadata_json(self):
        """
        Create a JSON-serializable data structure describing
        ``metadata`` for an image.
        """
        return {
            "flavor_classes": "*,!onmetal",
            "image_type": "base",
            "os_type": "linux",
            "org.openstack__1__os_distro": "org.freebsd",
            "vm_mode": "hvm",
            "auto_disk_config": "disabled"
        }


class RackspaceGentooImage(Image):
    """
    A Rackspace Gentoo image object representation
    """
    images = {"Gentoo 15.3 (PVHVM)": {"minRam": 512, "minDisk": 20,
                                      "OS-EXT-IMG-SIZE:size": random_image_size(),
                                      "id": new_random_image_id()}}

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
    images = {"OpenSUSE 13.2 (PVHVM)": {"minRam": 512, "minDisk": 20,
                                        "OS-EXT-IMG-SIZE:size": random_image_size(),
                                        "id": new_random_image_id()}}

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
                                                     "OS-EXT-IMG-SIZE:size": random_image_size(),
                                                     "com.rackspace__1__ui_default_show": "True",
                                                     "id": new_random_image_id()},
              "Red Hat Enterprise Linux 6 (PVHVM)": {"minRam": 512, "minDisk": 20,
                                                     "OS-EXT-IMG-SIZE:size": random_image_size(),
                                                     "com.rackspace__1__ui_default_show": "True",
                                                     "id": new_random_image_id()}}

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
    images = {"Red Hat Enterprise Linux 6 (PV)": {"minRam": 512, "minDisk": 20,
                                                  "id": new_random_image_id(),
                                                  "OS-EXT-IMG-SIZE:size": random_image_size()},
              "Red Hat Enterprise Linux 5 (PV)": {"minRam": 512, "minDisk": 20,
                                                  "id": new_random_image_id(),
                                                  "OS-EXT-IMG-SIZE:size": random_image_size()}}

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
    images = {"Scientific Linux 6 (PVHVM)": {"minRam": 512, "minDisk": 20, "id": new_random_image_id(),
                                             "OS-EXT-IMG-SIZE:size": random_image_size()},
              "Scientific Linux 7 (PVHVM)": {"minRam": 512, "minDisk": 20, "id": new_random_image_id(),
                                             "OS-EXT-IMG-SIZE:size": random_image_size()}}

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
                                                      "id": new_random_image_id(),
                                                      "OS-EXT-IMG-SIZE:size": random_image_size(),
                                                      "com.rackspace__1__ui_default_show": "True"},
              "Ubuntu 12.04 LTS (Precise Pangolin) (PVHVM)":
                  {"minRam": 512, "minDisk": 20, "OS-EXT-IMG-SIZE:size": random_image_size(),
                   "id": new_random_image_id(), "com.rackspace__1__ui_default_show": "True"},
              "Ubuntu 14.04 LTS (Trusty Tahr) (PVHVM)": {"minRam": 512, "minDisk": 20,
                                                         "OS-EXT-IMG-SIZE:size": random_image_size(),
                                                         "id": new_random_image_id(),
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
                                                           "id": new_random_image_id(),
                                                           "OS-EXT-IMG-SIZE:size": random_image_size()},
              "Ubuntu 14.04 LTS (Trusty Tahr) (PV)": {"minRam": 512, "minDisk": 20,
                                                      "id": new_random_image_id(),
                                                      "OS-EXT-IMG-SIZE:size": random_image_size()}}

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
    images = {"Vyatta Network OS 6.7R9": {"minRam": 1024, "minDisk": 20, "id": new_random_image_id(),
                                          "OS-EXT-IMG-SIZE:size": random_image_size(),
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
            "created": "1972-01-01_15-59-11",
            "updated": "1972-01-01_15-59-11",
            "status": "ACTIVE",
            "progress": 100,
            "metadata": self.metadata_json()
        })
        return template


class RackspaceOnMetalCoreOSImage(OnMetalImage):
    """
    A Rackspace OnMetal image object representation
    """
    images = {"OnMetal - CoreOS (Alpha)": {"minRam": 512, "minDisk": 20, "id": new_random_image_id(),
                                           "OS-EXT-IMG-SIZE:size": random_image_size()},
              "OnMetal - CoreOS (Beta)": {"minRam": 512, "minDisk": 20, "id": new_random_image_id(),
                                          "OS-EXT-IMG-SIZE:size": random_image_size()},
              "OnMetal - CoreOS (Stable)": {"minRam": 512, "minDisk": 20, "id": new_random_image_id(),
                                            "OS-EXT-IMG-SIZE:size": random_image_size()}}

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
    images = {"OnMetal - Fedora 22": {"minRam": 512, "minDisk": 20, "id": new_random_image_id(),
                                      "OS-EXT-IMG-SIZE:size": random_image_size()},
              "OnMetal - Fedora 21": {"minRam": 512, "minDisk": 20, "id": new_random_image_id(),
                                      "OS-EXT-IMG-SIZE:size": random_image_size()}}

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
                                                     "id": new_random_image_id(),
                                                     "OS-EXT-IMG-SIZE:size": random_image_size()},
              "OnMetal - Debian Unstable (Sid)": {"minRam": 512, "minDisk": 20,
                                                  "id": new_random_image_id(),
                                                  "OS-EXT-IMG-SIZE:size": random_image_size()},
              "OnMetal - Debian 8 (Jessie)": {"minRam": 512, "minDisk": 20,
                                              "id": new_random_image_id(),
                                              "OS-EXT-IMG-SIZE:size": random_image_size()},
              "OnMetal - Debian 7 (Wheezy)": {"minRam": 512, "minDisk": 20,
                                              "id": new_random_image_id(),
                                              "OS-EXT-IMG-SIZE:size": random_image_size()}}

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
                                                        "id": new_random_image_id(),
                                                        "OS-EXT-IMG-SIZE:size": random_image_size()},
              "OnMetal - Ubuntu 14.04 LTS (Trusty Tahr)": {"minRam": 512, "minDisk": 20,
                                                           "id": new_random_image_id(),
                                                           "OS-EXT-IMG-SIZE:size": random_image_size()},
              "OnMetal - Ubuntu 12.04 LTS (Precise Pangolin)":
                  {"minRam": 512, "minDisk": 20, "id": new_random_image_id(),
                   "OS-EXT-IMG-SIZE:size": random_image_size()}}

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
    images = {"OnMetal - CentOS 6": {"minRam": 512, "minDisk": 20, "id": new_random_image_id(),
                                     "OS-EXT-IMG-SIZE:size": random_image_size()},
              "OnMetal - CentOS 7": {"minRam": 512, "minDisk": 20, "id": new_random_image_id(),
                                     "OS-EXT-IMG-SIZE:size": random_image_size()}}

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
