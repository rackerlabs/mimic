
from uuid import uuid4

class Endpoint(object):
    """
    
    """
    def __init__(self, tenant_id, region, endpoint_id):
        self.tenant_id = tenant_id
        self.region = region
        self.endpoint_id = endpoint_id

    def url_with_prefix(self, uri_prefix):
        return uri_prefix + "/v2/" + self.tenant_id



class Entry(object):
    """
    An :obj:`Entry` is an entry in a service catalog.

    :ivar tenant_id: A tenant ID for this entry.
    :ivar name: A name for this entry.
    :ivar endpoints: 
    """
    def __init__(self, tenant_id, type, name, endpoints):
        self.type = type
        self.tenant_id = tenant_id
        self.name = name
        self.endpoints = endpoints


    @classmethod
    def with_regions(self, tenant_id, type, name, regions):
        """
        Constructor for a catalog entry with multiple regions.

        Endpoint IDs will be random UUIDs.
        """
        return Entry(tenant_id, type, name, [
            Endpoint(self.tenant_id, region, str(uuid4()))
            for region in regions
        ])



__all__ = [
    "Endpoint",
    "Entry",
]
