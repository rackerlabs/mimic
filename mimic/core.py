
from mimic.rest.nova_api import NovaApi
from mimic.rest.loadbalancer_api import LoadBalancerApi

from uuid import uuid4

class MimicCore(object):
    """
    A MimicCore contains a mapping from URI prefixes to particular service
    mocks.
    """

    def __init__(self):
        apis = [
            NovaApi(),
            LoadBalancerApi(),
        ]
        self.uri_prefixes = {
            # map of (region, service_id) to (somewhat ad-hoc interface) "Api"
            # object.
        }
        for api in apis:
            entries = api.catalog_entries(tenant_id=None)
            for entry in entries:
                for endpoint in entry.endpoints:
                    self.uri_prefixes[(endpoint.region, str(uuid4()))] = api


    def service_with_region(self, region_name, service_id):
        """
        Given the name of a region and a mimic internal service ID, get a
        resource for that service.

        :param unicode region_name: the name of the region that the service
            resource exists within.

        :return: A resource.
        :rtype: :obj:`twisted.web.iweb.IResource`
        """
        return self.uri_prefixes.get((region_name, service_id)).app.resource()


