"""
Model objects for the flavors.
"""

from characteristic import attributes, Attribute
from json import dumps
from mimic.model.flavors import (
    RackspaceStandardFlavor, RackspaceComputeFlavor, RackspaceMemoryFlavor,
    RackspaceOnMetalFlavor, RackspaceIOFlavor, RackspaceGeneralFlavor,
    RackspacePerformance1Flavor, RackspacePerformance2Flavor)

from mimic.model.nova_objects import not_found


@attributes(
    ["tenant_id", "region_name", "clock",
     Attribute("flavors_store", default_factory=list)]
)
class RegionalFlavorCollection(object):
    """
    A collection of flavors, in a given region, for a given tenant.
    """
    def flavor_by_id(self, flavor_id):
        """
        Retrieve a :obj:`Flavor` object by its ID.
        """
        self._create_flavors_list()
        for flavor in self.flavors_store:
            if flavor.flavor_id == flavor_id:
                return flavor

    def _create_flavors_list(self):
        """
        Generates the data for each flavor in each flavor class
        """
        rackspace_flavors = [RackspaceStandardFlavor, RackspaceComputeFlavor,
                             RackspacePerformance1Flavor, RackspaceOnMetalFlavor,
                             RackspacePerformance2Flavor, RackspaceMemoryFlavor,
                             RackspaceIOFlavor, RackspaceGeneralFlavor]

        if len(self.flavors_store) < 1:
            for flavor_class in rackspace_flavors:
                for flavor, flavor_spec in flavor_class.flavors.iteritems():
                    flavor_name = flavor
                    flavor_id = flavor_spec['id']
                    ram = flavor_spec['ram']
                    vcpus = flavor_spec['vcpus']
                    network = flavor_spec['rxtx_factor']
                    disk = flavor_spec['disk']
                    tenant_id = self.tenant_id
                    flavor = flavor_class(flavor_id=flavor_id, tenant_id=tenant_id,
                                          name=flavor_name, ram=ram, vcpus=vcpus,
                                          rxtx=network, disk=disk)
                    self.flavors_store.append(flavor)

    def list_flavors(self, include_details, absolutize_url):
        """
        Return a list of flavors with details.
        """
        self._create_flavors_list()
        flavors = []
        for flavor in self.flavors_store:
            if self.region_name != "IAD" and isinstance(flavor, RackspaceOnMetalFlavor):
                continue
            if include_details:
                flavors.append(flavor.detailed_json(absolutize_url))
            else:
                flavors.append(flavor.brief_json(absolutize_url))
        result = {"flavors": flavors}

        return dumps(result)

    def get_flavor(self, http_get_request, flavor_id, absolutize_url):
        """
        Return a flavor object if one exists from the list `/flavors` api,
        If the `flavor_id` is not found in the flavor store,
        then will return 404.
        """
        flavor = self.flavor_by_id(flavor_id)
        if flavor is None:
            return dumps(not_found("The resource could not be found.",
                                   http_get_request))
        return dumps({"flavor": flavor.detailed_json(absolutize_url)})


@attributes(["tenant_id", "clock",
             Attribute("regional_collections", default_factory=dict)])
class GlobalFlavorCollection(object):
    """
    A :obj:`GlobalFlavorCollection` is a set of all the
    :obj:`RegionalFlavorCollection` objects owned by a given tenant.  In other
    words, all the flavor objects that a single tenant owns globally.
    """

    def collection_for_region(self, region_name):
        """
        Get a :obj:`RegionalFlavorCollection` for the region identified by the
        given name.
        """
        if region_name not in self.regional_collections:
            self.regional_collections[region_name] = (
                RegionalFlavorCollection(tenant_id=self.tenant_id, region_name=region_name,
                                         clock=self.clock))
        return self.regional_collections[region_name]
