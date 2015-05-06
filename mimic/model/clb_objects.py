"""
Model objects for the CLB mimic.
"""

from characteristic import attributes, Attribute


class RegionalCLBCollection(object):
    """
    A collection of CloudLoadBalancers, in a given region, for a given tenant.
    """
    def __init__(self):
        """
        There are two stores - the lb info, and the metadata info
        """
        self.lbs = {}
        self.meta = {}


@attributes(["tenant_id", "clock",
             Attribute("regional_collections", default_factory=dict)])
class GlobalCLBCollections(object):
    """
    A :obj:`GlobalCLBCollections` is a set of all the
    :obj:`RegionalCLBCollection` objects owned by a given tenant.  In other
    words, all the objects that a single tenant owns globally in a
    cloud load balancer service.
    """

    def collection_for_region(self, region_name):
        """
        Get a :obj:`RegionalCLBCollection` for the region identified by the
        given name.
        """
        if region_name not in self.regional_collections:
            self.regional_collections[region_name] = (
                RegionalCLBCollection()
            )
        return self.regional_collections[region_name]
