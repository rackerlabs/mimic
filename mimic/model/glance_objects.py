"""
Model objects for the Glance mimic.
"""
from characteristic import attributes, Attribute


@attributes(["image_id", "name", "distro", "tenant_id",
             Attribute("status", default_value='ACTIVE')])
class Image(object):
    """
    A Image object
    """
    common_static_defaults = {
        "min_ram": 256,
        "flavor_classes": "*",
        "disk_format": "mimic",
        "ssh_user": "mimic",
        "schema": "/v2/schemas/image",
        "auto_disk_config": "disabled",
        "min_disk": 00,
        "virtual_size": None,
        "created": "1972-01-01_15-59-11",
        "updated": "1972-01-01_15-59-11"
    }

    static_metadata = {
        "com.rackspace__1__build_rackconnect": "1",
        "com.rackspace__1__options": "0",
        "flavor_classes": "*",
        "vm_mode": "xen",
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
        template = self.common_static_defaults.copy()
        template.update({
            "id": self.image_id,
            "name": self.name,
            "status": self.status,
            "links": self.links_json(absolutize_url),
            "progress": 100,
            "OS-DCF:diskConfig": "AUTO",
            "OS-EXT-IMG-SIZE:size": 100000,
            "metadata": self.static_metadata
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
