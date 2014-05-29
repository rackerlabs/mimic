
from uuid import uuid4

class Endpoint(object):
    """
    An endpoint represents a portion of a service catalog.

    :ivar str tenant_id: A tenant ID for this endpoint.
    :ivar str region: The region name for this endpoint.
    :ivar str endpoint_id: The endpoint ID; used only in some auth responses,
        not the basic service catalog.
    """
    def __init__(self, tenant_id, region, endpoint_id):
        self.tenant_id = tenant_id
        self.region = region
        self.endpoint_id = endpoint_id

    def url_with_prefix(self, uri_prefix):
        if self.tenant_id is None:
            postfix = ''
        else:
            postfix = self.tenant_id
        return "/".join([uri_prefix.rstrip("/"), postfix])



class Entry(object):
    """
    An :obj:`Entry` is an entry in a service catalog.

    :ivar str tenant_id: A tenant ID for this entry.
    :ivar str name: A name for this entry.
    :ivar iterable endpoints: Iterable of :obj:`Endpoint` objects.
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
            Endpoint(tenant_id, region, str(uuid4()))
            for region in regions
        ])



__all__ = [
    "Endpoint",
    "Entry",
]
