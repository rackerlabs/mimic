"""
Glance images
"""

images = {
    "images":
        [{
            "com.rackspace__1__options": "0",
            "container_format": "ovf",
            "min_ram": 512,
            "updated_at": "2015-03-09T20:33:01Z",
            "owner": "657197",
            "file": "/v2/images/fed66ee7-fb4b-4464-b8c6-609c1fde218f/file",
            "flavor_classes": "*,!io1,!memory1,!compute1,!onmetal",
            "vm_mode": "xen",
            "com.rackspace__1__release_id": "1007",
            "com.rackspace__1__build_core": "1",
            "id": "fed66ee7-fb4b-4464-b8c6-609c1fde218f",
            "size": 1091261957,
            "os_distro": "ubuntu",
            "com.rackspace__1__release_version": "11",
            "image_type": "base",
            "self": "/v2/images/fed66ee7-fb4b-4464-b8c6-609c1fde218f",
            "disk_format": "vhd",
            "com.rackspace__1__platform_target": "PublicCloud",
            "com.rackspace__1__build_managed": "1",
            "org.openstack__1__architecture": "x64",
            "schema": "/v2/schemas/image",
            "status": "active",
            "com.rackspace__1__visible_core": "1",
            "tags": [],
            "com.rackspace__1__release_build_date": "2015-03-05_17-43-17",
            "visibility": "public",
            "auto_disk_config": "True",
            "min_disk": 20,
            "org.openstack__1__os_distro": "com.ubuntu",
            "com.rackspace__1__visible_managed": "1",
            "com.rackspace__1__source": "kickstart",
            "name": "Ubuntu 14.04 LTS (Trusty Tahr) (PV)",
            "com.rackspace__1__build_rackconnect": "1",
            "checksum": "29f8698b79091e8dc524381e562524eb",
            "created_at": "2015-03-05T18:29:51Z",
            "cache_in_nova": "True",
            "protected": "false",
            "com.rackspace__1__visible_rackconnect": "1",
            "os_type": "linux",
            "org.openstack__1__os_version": "14.04"
        }],
    "schema": "/v2/schemas/images",
    "first": "/v2/images?limit=1000"
}


image_schema = {
    "additionalProperties": {
        "type": "string"
    },
    "name": "image",
    "links": [
        {
            "href": "{self}",
            "rel": "self"
        },
        {
            "href": "{file}",
            "rel": "enclosure"
        },
        {
            "href": "{schema}",
            "rel": "describedby"
        }
    ],
    "properties": {
        "status": {
            "enum": [
                "queued",
                "saving",
                "active",
                "killed",
                "deleted",
                "pending_delete"
            ],
            "type": "string",
            "description": "Status of the image (READ-ONLY)"
        },
        "schema": {
            "type": "string",
            "description": "(READ-ONLY)"
        },
        "file": {
            "type": "string",
            "description": "(READ-ONLY)"
        },
        "direct_url": {
            "type": "string",
            "description": "URL to access the image file kept in external store (READ-ONLY)"
        },
        "name": {
            "type": ["null",
                     "string"],
            "description": "Descriptive name for the image",
            "maxLength": 255},
        "tags": {
            "items": {
                "type": "string",
                "maxLength": 255},
            "type": "array",
            "description": "List of strings related to the image"
        },
        "locations": {
            "items": {
                "required": ["url",
                             "metadata"],
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "maxLength": 255},
                    "metadata": {
                        "type": "object"
                    }}},
            "type": "array",
            "description": "A set of URLs to access the image file kept in external store"
        },
        "checksum": {
            "type": [
                "null",
                "string"
            ],
            "description": "md5 hash of image contents. (READ-ONLY)",
            "maxLength": 32
        },
        "created_at": {
            "type": "string",
            "description": "Date and time of image registration (READ-ONLY)"
        },
        "disk_format": {
            "enum": [
                None,
                "ami",
                "ari",
                "aki",
                "vhd",
                "vmdk",
                "raw",
                "qcow2",
                "vdi",
                "iso"
            ],
            "type": [
                "null",
                "string"
            ],
            "description": "Format of the disk"
        },
        "updated_at": {
            "type": "string",
            "description": "Date and time of the last image modification (READ-ONLY)"
        },
        "visibility": {
            "enum": [
                "public",
                "private"
            ],
            "type": "string",
            "description": "Scope of image accessibility"
        },
        "self": {
            "type": "string",
            "description": "(READ-ONLY)"
        },
        "min_disk": {
            "type": "integer",
            "description": "Amount of disk space (in GB) required to boot image."
        },
        "protected": {
            "type": "boolean",
            "description": "If true, image will not be deletable."
        },
        "min_ram": {
            "type": "integer",
            "description": "Amount of ram (in MB) required to boot image."
        },
        "container_format": {
            "enum": [
                None,
                "ami",
                "ari",
                "aki",
                "bare",
                "ovf",
                "ova"
            ],
            "type": [
                "null",
                "string"
            ],
            "description": "Format of the container"
        },
        "owner": {
            "type": ["null",
                     "string"],
            "description": "Owner of the image",
            "maxLength": 255},
        "virtual_size": {
            "type": ["null",
                     "integer"],
            "description": "Virtual size of image in bytes (READ-ONLY)"
        },
        "id": {
            "pattern": "^([0-9a-fA-F]){8}-([0-9a-fA-F]){4}-([0-9a-fA-F]){4}-([0-9a-fA-F])" +
                       "{4}-([0-9a-fA-F]){12}$",
            "type": "string",
            "description": "An identifier for the image"
        },
        "size": {
            "type": [
                "null",
                "integer"
            ],
            "description": "Size of image file in bytes (READ-ONLY)"
        }}}
