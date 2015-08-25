"""
Model objects for mimic flavors.
"""

from characteristic import attributes


class Flavor(object):
    """
    A Flavor object
    """

    static_defaults = {
        "swap": "",
        "OS-FLV-EXT-DATA:ephemeral": 0,
    }

    def links_json(self, absolutize_url):
        """
        Create a JSON-serializable data structure describing the links to this
        flavor.
        """
        return [
            {
                "href": absolutize_url("v2/{0}/flavors/{1}"
                                       .format(self.tenant_id, self.flavor_id)),
                "rel": "self"
            },
            {
                "href": absolutize_url("{0}/flavors/{1}"
                                       .format(self.tenant_id, self.flavor_id)),
                "rel": "bookmark"
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
            "id": self.flavor_id,
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
            "vcups": self.vcpus,
            "rxtx_factor": self.rxtx,
            "disk": self.disk,
            "OS-FLV-WITH-EXT-SPECS:extra_specs": self.extra_specs_json()
        })
        return template


@attributes(['flavor_id', 'tenant_id', 'name', 'ram', 'vcpus', 'rxtx', 'disk'])
class StandardFlavor(Flavor):

    flavors = {"512 MB Standard Instance": {"ram": 512, "vcpus": 1, "rxtx_factor": 80, "disk": 20},
               "1 GB Standard Instance": {"ram": 1024, "vcpus": 1, "rxtx_factor": 120, "disk": 40},
               "2 GB Standard Instance": {"ram": 2048, "vcpus": 2, "rxtx_factor": 240, "disk": 80},
               "4 GB Standard Instance": {"ram": 4096, "vcpus": 2, "rxtx_factor": 400, "disk": 160},
               "8 GB Standard Instance": {"ram": 8192, "vcpus": 4, "rxtx_factor": 600, "disk": 320},
               "15 GB Standard Instance": {"ram": 15360, "vcpus": 6, "rxtx_factor": 800, "disk": 620},
               "30 GB Standard Instance": {"ram": 30720, "vcpus": 8, "rxtx_factor": 1200, "disk": 1200}}

    def extra_specs_json(self):
        """
        Create a JSON-serializable data structure describing
        ``OS-FLV-WITH-EXT-SPECS:extra_specs`` for a standard flavor.
        """
        return {
            "class": "standard1",
            "policy_class": "standard_flavor"
        }


@attributes(['flavor_id', 'tenant_id', 'name', 'ram', 'vcpus', 'rxtx', 'disk'])
class ComputeFlavor(Flavor):

    flavors = {"3.75 GB Compute v1": {"ram": 3840, "vcpus": 2, "rxtx_factor": 312.5, "disk": 0},
               "7.5 GB Compute v1": {"ram": 7680, "vcpus": 4, "rxtx_factor": 625, "disk": 0},
               "15 GB Compute v1": {"ram": 15360, "vcpus": 8, "rxtx_factor": 1250, "disk": 0},
               "30 GB Compute v1": {"ram": 30720, "vcpus": 16, "rxtx_factor": 2500, "disk": 0},
               "60 GB Compute v1": {"ram": 61440, "vcpus": 32, "rxtx_factor": 5000, "disk": 0}}

    def extra_specs_json(self):
        """
        Create a JSON-serializable data structure describing
        ``OS-FLV-WITH-EXT-SPECS:extra_specs`` for a compute flavor.
        """
        return {
            "class": "compute1",
            "policy_class": "compute_flavor"
        }

@attributes(['flavor_id', 'tenant_id', 'name', 'ram', 'vcpus', 'rxtx', 'disk'])
class GeneralFlavor(Flavor):

    flavors = {"1 GB General Purpose v1": {"ram": 1024, "vcpus": 1, "rxtx_factor": 200, "disk": 20},
               "2 GB General Purpose v1": {"ram": 2048, "vcpus": 2, "rxtx_factor": 400, "disk": 40},
               "4 GB General Purpose v1": {"ram": 4096, "vcpus": 4, "rxtx_factor": 800, "disk": 80},
               "8 GB General Purpose v1": {"ram": 8192, "vcpus": 8, "rxtx_factor": 1600, "disk": 160}}

    def extra_specs_json(self):
        """
        Create a JSON-serializable data structure describing
        ``OS-FLV-WITH-EXT-SPECS:extra_specs`` for a general purpose flavor.
        """
        return {
            "class": "general1",
            "policy_class": "general_flavor"
        }

@attributes(['flavor_id', 'tenant_id', 'name', 'ram', 'vcpus', 'rxtx', 'disk'])
class IOFlavor(Flavor):

    flavors = {"15 GB I/0 v1": {"ram": 15360, "vcpus": 4, "rxtx_factor": 1250, "disk": 40},
               "30 GB I/0 v1": {"ram": 30720, "vcpus": 8, "rxtx_factor": 2500, "disk": 40},
               "60 GB I/0 v1": {"ram": 61440, "vcpus": 16, "rxtx_factor": 5000, "disk": 40},
               "90 GB I/0 v1": {"ram": 92160, "vcpus": 24, "rxtx_factor": 7500, "disk": 40},
               "120 GB I/0 v1": {"ram": 122880, "vcpus": 32, "rxtx_factor": 10000, "disk": 40}}

    def extra_specs_json(self):
        """
        Create a JSON-serializable data structure describing
        ``OS-FLV-WITH-EXT-SPECS:extra_specs`` for a memory flavor.
        """
        return {
            "class": "io1",
            "policy_class": "io_flavor"
        }

@attributes(['flavor_id', 'tenant_id', 'name', 'ram', 'vcpus', 'rxtx', 'disk'])
class MemoryFlavor(Flavor):

    flavors = {"15 GB Memory v1": {"ram": 15360, "vcpus": 2, "rxtx_factor": 625, "disk": 0},
               "30 GB Memory v1": {"ram": 30720, "vcpus": 4, "rxtx_factor": 1250, "disk": 0},
               "60 GB Memory v1": {"ram": 61440, "vcpus": 8, "rxtx_factor": 2500, "disk": 0},
               "120 GB Memory v1": {"ram": 122880, "vcpus": 16, "rxtx_factor": 5000, "disk": 0},
               "240 GB Memory v1": {"ram": 245760, "vcpus": 32, "rxtx_factor": 10000, "disk": 0}}

    def extra_specs_json(self):
        """
        Create a JSON-serializable data structure describing
        ``OS-FLV-WITH-EXT-SPECS:extra_specs`` for a flavor.
        """
        return {
            "class": "memory1",
            "policy_class": "memory_flavor"
        }


@attributes(['flavor_id', 'tenant_id', 'name', 'ram', 'vcpus', 'rxtx', 'disk'])
class OnMetalFlavor(Flavor):

    flavors = {"OnMetal Compute v1": {"ram": 32768, "vcpus": 20, "rxtx_factor": 10000, "disk": 32},
               "OnMetal IO v1": {"ram": 131072, "vcpus": 40, "rxtx_factor": 10000, "disk": 32},
               "OnMetal Memory v1": {"ram": 524288, "vcpus": 24, "rxtx_factor": 10000, "disk": 32}}

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


@attributes(['flavor_id', 'tenant_id', 'name', 'ram', 'vcpus', 'rxtx', 'disk'])
class Performance1Flavor(Flavor):

    flavors = {"1 GB Performance": {"ram": 1024, "vcpus": 1, "rxtx_factor": 200, "disk": 20},
               "2 GB Performance": {"ram": 2048, "vcpus": 2, "rxtx_factor": 400, "disk": 40},
               "4 GB Performance": {"ram": 4096, "vcpus": 4, "rxtx_factor": 800, "disk": 40},
               "8 GB Performance": {"ram": 8192, "vcpus": 8, "rxtx_factor": 1600, "disk": 40}}


    def extra_specs_json(self):
        """
        Create a JSON-serializable data structure describing
        ``OS-FLV-WITH-EXT-SPECS:extra_specs`` for a performance1 flavor.
        """
        return {
            "class": "performance1",
            "policy_class": "performance_flavor"
        }

@attributes(['flavor_id', 'tenant_id', 'name', 'ram', 'vcpus', 'rxtx', 'disk'])
class Performance2Flavor(Flavor):

    flavors = {"15 GB Performance": {"ram": 15360, "vcpus": 4, "rxtx_factor": 1250, "disk": 40},
               "30 GB Performance": {"ram": 30720, "vcpus": 8, "rxtx_factor": 2500, "disk": 40},
               "60 GB Performance": {"ram": 61440, "vcpus": 16, "rxtx_factor": 5000, "disk": 40},
               "90 GB Performance": {"ram": 92160, "vcpus": 24, "rxtx_factor": 7500, "disk": 40},
               "120 GB Performance": {"ram": 122880, "vcpus": 32, "rxtx_factor": 10000, "disk": 40}}


    def extra_specs_json(self):
        """
        Create a JSON-serializable data structure describing
        ``OS-FLV-WITH-EXT-SPECS:extra_specs`` for a performance 2 flavor.
        """
        return {
            "class": "performance2",
            "policy_class": "performance_flavor"
        }