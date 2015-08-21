"""
Model objects for mimic flavors.
"""

from characteristic import attributes


@attributes(['flavor_id', 'name', 'ram', 'tenant_id'])
class Flavor(object):
    """
    A Flavor object
    """

    static_defaults = {
        "vcpus": 20,
        "swap": "",
        "rxtx_factor": 10000.0,
        "OS-FLV-EXT-DATA:ephemeral": 0,
        "disk": 800
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
            "class": "mimic",
            "policy_class": "mimic_flavor"
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
            "OS-FLV-WITH-EXT-SPECS:extra_specs": self.extra_specs_json()
        })
        return template
