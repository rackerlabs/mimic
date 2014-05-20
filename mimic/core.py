
from uuid import uuid4

class MimicCore(object):
    """
    A MimicCore contains a mapping from URI prefixes to particular service
    mocks.
    """

    def __init__(self):
        """
        
        """
        apis = [
            nova_api.NovaApi(),
            loadbalancer_api.LoadBalancerApi(),
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
        """
        return self.uri_prefixes.get((region_name, service_id)).app.resource()

