"""
Model objects for mimic images.
"""

from characteristic import attributes


@attributes(['image_id', 'tenant_id', 'name'])
class Image(object):
    """
    A Image object
    """

    static_defaults = {
        "swap": "",
        "OS-FLV-EXT-DATA:ephemeral": 0,
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

    def extra_specs_json(self):
        """
        Create a JSON-serializable data structure describing
        ``OS-FLV-WITH-EXT-SPECS:extra_specs`` for a flavor.
        """
        return {
            "quota_resources": "instances=mimic-instances,ram=mimic-ram",
            }

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
        template = self.static_defaults.copy()
        template.update({
            "id": self.flavor_id,
            "links": self.links_json(absolutize_url),
            "name": self.name,
            "ram": self.ram,
            "vcpus": self.vcpus,
            "rxtx_factor": self.rxtx,
            "disk": self.disk,
            "OS-FLV-WITH-EXT-SPECS:extra_specs": self.extra_specs_json()
        })
        return template


class RackspaceWindowsImage(Flavor):
    """
    A Rackspace window image object representation
    """
    flavors = {"Windows Server 2008 R2 SP1 + SQL Server 2008 R2 SP2 Standard":
                    {"id": "a3b09eeb-e517-44d1-9d2e-85d77e989b95", "minRam": 2048, "minDisk": 40},
               "Windows Server 2008 R2 SP1 + SQL Server 2008 R2 SP2 Web":
                    {"id": "0942f896-f608-4db0-b4ee-d79c29e653fb", "minRam": 2048, "minDisk": 40},
               "Windows Server 2008 R2 SP1":
                    {"id": "d84bffa7-d4d4-4fd3-a7f7-06865e02467d", "minRam": 1024, "minDisk": 40},
               "Windows Server 2012 R2":
                    {"id": "76964ffc-26eb-4a83-8301-50e77255b355", "minRam": 1024, "minDisk": 40},
               "Windows Server 2012 + SQL Server 2012 SP1 Web":
                    {"id": "7fd9336e-f7fa-41ee-a6d7-7996c29cbfa4", "minRam": 2048, "minDisk": 40},
               "Windows Server 2012 + SQL Server 2012 SP1 Standard":
                    {"id": "9b02a4ef-b0ea-4e29-b99f-b505dfe99fec", "minRam": 2048, "minDisk": 40},
               "Windows Server 2012 R2 + SQL Server 2014 Standard":
                    {"id": "c91ae969-40a5-421a-8cb1-c32cb6998dd4", "minRam": 2048, "minDisk": 40},
               "Windows Server 2012 R2 + SQL Server 2014 Web":
                    {"id": "beb3dfe6-ebb0-4943-bcea-65a3e11bb7bd", "minRam": 2048, "minDisk": 40},
               "Windows Server 2012":
                    {"id": "03b70725-29c6-4d88-be2b-c19004b25c28", "minRam": 1024, "minDisk": 40}}

    def extra_specs_json(self):
        """
        Create a JSON-serializable data structure describing
        ``OS-FLV-WITH-EXT-SPECS:extra_specs`` for a standard flavor.
        """
        return {"metadata": {
            "flavor_classes": "*,!onmetal",
            "image_type": "base",
            "os_type": "windows",
        }}


class RackspaceComputeFlavor(Flavor):
    """
    A Rackspace compute flavor object representatione
    """
    flavors = {"3.75 GB Compute v1": {"id": "compute1-8", "ram": 3840, "vcpus": 2, "rxtx_factor": 312.5,
                                      "disk": 0},
               "7.5 GB Compute v1": {"id": "compute1-4", "ram": 7680, "vcpus": 4, "rxtx_factor": 625,
                                     "disk": 0},
               "15 GB Compute v1": {"id": "compute1-15", "ram": 15360, "vcpus": 8, "rxtx_factor": 1250,
                                    "disk": 0},
               "30 GB Compute v1": {"id": "compute1-30", "ram": 30720, "vcpus": 16, "rxtx_factor": 2500,
                                    "disk": 0},
               "60 GB Compute v1": {"id": "compute1-60", "ram": 61440, "vcpus": 32, "rxtx_factor": 5000,
                                    "disk": 0}}

    def extra_specs_json(self):
        """
        Create a JSON-serializable data structure describing
        ``OS-FLV-WITH-EXT-SPECS:extra_specs`` for a compute flavor.
        """
        return {
            "class": "compute1",
            "policy_class": "compute_flavor"
        }


class RackspaceGeneralFlavor(Flavor):
    """
    A Rackspace general flavor object representation
    """
    flavors = {"1 GB General Purpose v1": {"id": "general1-1", "ram": 1024, "vcpus": 1,
                                           "rxtx_factor": 200, "disk": 20},
               "2 GB General Purpose v1": {"id": "general1-2", "ram": 2048, "vcpus": 2,
                                           "rxtx_factor": 400, "disk": 40},
               "4 GB General Purpose v1": {"id": "general1-4", "ram": 4096, "vcpus": 4,
                                           "rxtx_factor": 800, "disk": 80},
               "8 GB General Purpose v1": {"id": "general1-8", "ram": 8192, "vcpus": 8,
                                           "rxtx_factor": 1600, "disk": 160}}

    def extra_specs_json(self):
        """
        Create a JSON-serializable data structure describing
        ``OS-FLV-WITH-EXT-SPECS:extra_specs`` for a general purpose flavor.
        """
        return {
            "class": "general1",
            "policy_class": "general_flavor"
        }


class RackspaceIOFlavor(Flavor):
    """
    A Rackspace IO flavor object representation
    """
    flavors = {"15 GB I/0 v1": {"id": "io1-15", "ram": 15360, "vcpus": 4, "rxtx_factor": 1250,
                                "disk": 40},
               "30 GB I/0 v1": {"id": "io1-30", "ram": 30720, "vcpus": 8, "rxtx_factor": 2500,
                                "disk": 40},
               "60 GB I/0 v1": {"id": "io1-60", "ram": 61440, "vcpus": 16, "rxtx_factor": 5000,
                                "disk": 40},
               "90 GB I/0 v1": {"id": "io1-90", "ram": 92160, "vcpus": 24, "rxtx_factor": 7500,
                                "disk": 40},
               "120 GB I/0 v1": {"id": "io1-120", "ram": 122880, "vcpus": 32, "rxtx_factor": 10000,
                                 "disk": 40}}

    def extra_specs_json(self):
        """
        Create a JSON-serializable data structure describing
        ``OS-FLV-WITH-EXT-SPECS:extra_specs`` for a memory flavor.
        """
        return {
            "class": "io1",
            "policy_class": "io_flavor"
        }


class RackspaceMemoryFlavor(Flavor):
    """
    A Rackspace memory flavor object representation
    """
    flavors = {"15 GB Memory v1": {"id": "memory1-15", "ram": 15360, "vcpus": 2, "rxtx_factor": 625,
                                   "disk": 0},
               "30 GB Memory v1": {"id": "memory1-30", "ram": 30720, "vcpus": 4, "rxtx_factor": 1250,
                                   "disk": 0},
               "60 GB Memory v1": {"id": "memory1-60", "ram": 61440, "vcpus": 8, "rxtx_factor": 2500,
                                   "disk": 0},
               "120 GB Memory v1": {"id": "memory1-120", "ram": 122880, "vcpus": 16, "rxtx_factor": 5000,
                                    "disk": 0},
               "240 GB Memory v1": {"id": "memory1-240", "ram": 245760, "vcpus": 32,
                                    "rxtx_factor": 10000, "disk": 0}}

    def extra_specs_json(self):
        """
        Create a JSON-serializable data structure describing
        ``OS-FLV-WITH-EXT-SPECS:extra_specs`` for a flavor.
        """
        return {
            "class": "memory1",
            "policy_class": "memory_flavor"
        }


class RackspaceOnMetalFlavor(Flavor):
    """
    A Rackspace onMetal flavor object representation
    """
    flavors = {"OnMetal Compute v1": {"id": "onmetal-compute1", "ram": 32768, "vcpus": 20,
                                      "rxtx_factor": 10000, "disk": 32},
               "OnMetal IO v1": {"id": "onmetal-io1", "ram": 131072, "vcpus": 40,
                                 "rxtx_factor": 10000, "disk": 32},
               "OnMetal Memory v1": {"id": "onmetal-memory1", "ram": 524288, "vcpus": 24,
                                     "rxtx_factor": 10000, "disk": 32}}

    def extra_specs_json(self):
        """
        Create a JSON-serializable data structure describing
        ``OS-FLV-WITH-EXT-SPECS:extra_specs`` for an onMetal flavor.
        """
        return {
            "quota_resources": "instances=onmetal-compute-v1-instances,ram=onmetal-compute-v1-ram",
            "class": "onmetal",
            "policy_class": "onmetal_flavor"
        }


class RackspacePerformance1Flavor(Flavor):
    """
    A Rackspace perfomance flavor object representation
    """
    flavors = {"1 GB Performance": {"id": "performance1-1", "ram": 1024, "vcpus": 1, "rxtx_factor": 200,
                                    "disk": 20},
               "2 GB Performance": {"id": "performance1-2", "ram": 2048, "vcpus": 2, "rxtx_factor": 400,
                                    "disk": 40},
               "4 GB Performance": {"id": "performance1-4", "ram": 4096, "vcpus": 4, "rxtx_factor": 800,
                                    "disk": 40},
               "8 GB Performance": {"id": "performance1-8", "ram": 8192, "vcpus": 8, "rxtx_factor": 1600,
                                    "disk": 40}}

    def extra_specs_json(self):
        """
        Create a JSON-serializable data structure describing
        ``OS-FLV-WITH-EXT-SPECS:extra_specs`` for a performance1 flavor.
        """
        return {
            "class": "performance1",
            "policy_class": "performance_flavor"
        }


class RackspacePerformance2Flavor(Flavor):
    """
    A Rackspace performance flavor object representation
    """
    flavors = {"15 GB Performance": {"id": "performance2-15", "ram": 15360, "vcpus": 4,
                                     "rxtx_factor": 1250, "disk": 40},
               "30 GB Performance": {"id": "performance2-30", "ram": 30720, "vcpus": 8,
                                     "rxtx_factor": 2500, "disk": 40},
               "60 GB Performance": {"id": "performance2-60", "ram": 61440, "vcpus": 16,
                                     "rxtx_factor": 5000, "disk": 40},
               "90 GB Performance": {"id": "performance2-90", "ram": 92160, "vcpus": 24,
                                     "rxtx_factor": 7500, "disk": 40},
               "120 GB Performance": {"id": "performance2-120", "ram": 122880, "vcpus": 32,
                                      "rxtx_factor": 10000, "disk": 40}}

    def extra_specs_json(self):
        """
        Create a JSON-serializable data structure describing
        ``OS-FLV-WITH-EXT-SPECS:extra_specs`` for a performance 2 flavor.
        """
        return {
            "class": "performance2",
            "policy_class": "performance_flavor"
        }
