"""
Model objects for the Glance mimic.
"""

from __future__ import absolute_import, division, unicode_literals

from json import dumps
from uuid import uuid4

import attr
from mimic.util.helper import json_from_request
from six import text_type

random_image_list = [
    {"id": text_type(uuid4()), "name": "OnMetal - CentOS 6", "distro": "linux"},
    {"id": text_type(uuid4()), "name": "OnMetal - CentOS 7", "distro": "linux"},
    {"id": text_type(uuid4()), "name": "OnMetal - CoreOS (Alpha)", "distro": "linux"},
    {"id": text_type(uuid4()), "name": "OnMetal - CoreOS (Beta)", "distro": "linux"},
    {"id": text_type(uuid4()), "name": "OnMetal - Debian 7 (Wheezy)", "distro": "linux"},
    {"id": text_type(uuid4()), "name": "OnMetal - Debian 8 (Jessie)", "distro": "linux"},
    {"id": text_type(uuid4()), "name": "OnMetal - Fedora 21", "distro": "linux"},
    {"id": text_type(uuid4()), "name": "OnMetal - Fedora 22", "distro": "linux"},
    {"id": text_type(uuid4()), "name": "OnMetal - Ubuntu 14.04 LTS (Trusty Tahr)", "distro": "linux"},
    {"id": text_type(uuid4()), "name": "OnMetal - CoreOS (Stable)", "distro": "linux"},
    {"id": text_type(uuid4()), "name": "OnMetal - Ubuntu 12.04 LTS (Precise Pangolin)",
     "distro": "linux"},
    {"id": text_type(uuid4()), "name": "Ubuntu 14.04 LTS (Trusty Tahr)", "distro": "linux"},
    {"id": text_type(uuid4()), "name": "Ubuntu 15.04 (Vivid Vervet)", "distro": "linux"},
    {"id": text_type(uuid4()), "name": "Windows Server 2012 R2", "distro": "windows"}
]


@attr.s
class Image(object):
    """
    A Image object
    """

    image_id = attr.ib(validator=attr.validators.instance_of(text_type))
    name = attr.ib(validator=attr.validators.instance_of(text_type))
    distro = attr.ib(validator=attr.validators.instance_of(text_type))
    tenant_id = attr.ib(
        validator=attr.validators.optional(
            attr.validators.instance_of(text_type)),
        default=None
    )
    status = attr.ib(validator=attr.validators.instance_of(text_type),
                     default='active')

    static_server_image_defaults = {
        "minRam": 256,
        "minDisk": 00,
    }

    static_glance_defaults = {
        "flavor_classes": "*",
        "min_ram": 256,
        "min_disk": 00,
        "container_format": None,
        "owner": "00000",
        "size": 10000,
        "tags": [],
        "visibility": "public",
        "checksum": "0000",
        "protected": False,
        "disk_format": None,
        "ssh_user": "mimic",
        "schema": "/v2/schemas/image",
        "auto_disk_config": "disabled",
        "virtual_size": None,
        "visibility": "public"
    }

    static_metadata = {
        "com.rackspace__1__build_rackconnect": "1",
        "com.rackspace__1__options": "0",
        "com.rackspace__1__release_id": "000",
        "com.rackspace__1__build_core": "1",
        "image_type": "base",
        "org.openstack__1__os_version": "0.1",
        "com.rackspace__1__platform_target": "MimicCloud",
        "com.rackspace__1__build_managed": "1",
        "org.openstack__1__architecture": "x64",
        "com.rackspace__1__visible_core": "1",
        "com.rackspace__1__release_build_date": "1972-01-01_15-59-11",
        "com.rackspace__1__visible_rackconnect": "1",
        "com.rackspace__1__release_version": "1",
        "com.rackspace__1__visible_managed": "1",
        "cache_in_nova": "True",
        "com.rackspace__1__build_config_options": "mimic",
        "auto_disk_config": "True",
        "com.rackspace__1__source": "kickstart",
        "com.rackspace__1__ui_default_show": "True"
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
                "href": absolutize_url("/images/{0}".format(self.image_id)),
                "rel": "alternate",
                "type": "application/vnd.openstack.image"
            }
        ]

    def get_server_image_details_json(self, absolutize_url):
        """
        JSON-serializable object representation of this image, as
        returned by either a GET on this individual image through the
        servers api.
        """
        template = self.static_server_image_defaults.copy()
        template.update({
            "id": self.image_id,
            "name": self.name,
            "status": self.status.upper(),
            "links": self.links_json(absolutize_url),
            "progress": 100,
            "OS-DCF:diskConfig": "AUTO",
            "OS-EXT-IMG-SIZE:size": 100000,
            "metadata": self.static_metadata,
            "created": "1972-01-01_15-59-11",
            "updated": "1972-01-01_15-59-11"
        })
        if self.distro != "windows":
            template["metadata"]["os_distro"] = self.distro
        return template

    def brief_json(self, absolutize_url):
        """
        Brief JSON-serializable version of this image.
        """
        return {
            "name": self.name,
            "id": self.image_id,
            "links": self.links_json(absolutize_url)
        }

    def get_glance_admin_image_json(self):
        """
        JSON-serializable object representation of this image, as
        returned by either a GET on this individual image or a member in the
        list returned by the list-details request.
        """
        template = self.static_glance_defaults.copy()
        template.update(self.static_metadata)
        template.update({
            "id": self.image_id,
            "name": self.name,
            "status": self.status,
            "created_at": "1972-01-01_15-59-11",
            "updated_at": "1972-01-01_15-59-11",
            "file": "/v2/images/{0}/file".format(self.image_id),
            "self": "/v2/images/" + self.image_id,
            "org.openstack__1__os_distro": "mimic." + self.distro,
            "os_type": self.distro,
            "vm_mode": "onmetal"
        })
        if self.distro != "windows":
            template.update({
                "os_distro": self.distro
            })
        if "OnMetal" in self.name:
            template.update({
                "vm_mode": "metal",
                "flavor_classes": "onmetal"
            })
        return template


@attr.s
class GlanceAdminImageStore(object):
    """
    A collection of :obj:`Image`.
    """

    glance_admin_image_store = attr.ib(default=attr.Factory(list))

    def image_by_id(self, image_id):
        """
        Retrieve a :obj:`Image` object by its ID.
        """
        for image in self.glance_admin_image_store:
            if image.image_id == image_id:
                return image

    def add_to_glance_admin_image_store(self, **attributes):
        """
        Create a new Image object and add it to the
        :obj: `glance_admin_image_store`
        """
        image = Image(**{str(k): attributes[k] for k in attributes})
        self.glance_admin_image_store.append(image)
        return image

    def list_images(self):
        """
        List all the images for the Glance Admin API.
        """
        if not self.glance_admin_image_store:
            for each_image in random_image_list:
                self.add_to_glance_admin_image_store(
                    image_id=each_image['id'],
                    name=each_image['name'],
                    distro=each_image['distro'])
        return {"images": [image.get_glance_admin_image_json()
                           for image in self.glance_admin_image_store]}

    def get_image(self, http_request, image_id):
        """
        get image with image_id for the Glance Admin API.
        """
        image = self.image_by_id(image_id)
        if image:
            return image.get_glance_admin_image_json()
        http_request.setResponseCode(404)
        return ''

    def create_image(self, http_create_request):
        """
        Creates a new image with the given request json and returns the image.

        Note: This is more like a control plane API as I dint find seem
        to find documentation for add image under the Glance admin API.
        """
        try:
            content = json_from_request(http_create_request)
            image_name = content.get('name')
            if image_name is None:
                raise KeyError("no name supplied")
            image_distro = content.get('distro')
            if image_distro is None:
                raise KeyError("no distro supplied")
        except Exception as e:
            http_create_request.setResponseCode(400)
            return dumps({"Error": text_type(e)})
        image_id = text_type(uuid4())
        new_image = self.add_to_glance_admin_image_store(
            image_id=image_id,
            name=image_name,
            distro=image_distro)
        http_create_request.setResponseCode(201)
        return new_image.get_glance_admin_image_json()

    def delete_image(self, http_request, image_id):
        """
        Deletes the image and returns 204.
        If image does not exit, returns 404.
        Docs: http://bit.ly/1Obujvd
        """
        image = self.image_by_id(image_id)
        if image:
            self.glance_admin_image_store.remove(image)
            http_request.setResponseCode(204)
            return b''
        http_request.setResponseCode(404)
        return b''
