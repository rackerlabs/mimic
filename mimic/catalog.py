"""
Classes which represent the objects within the service catalog.
"""

from __future__ import absolute_import, division, unicode_literals

__all__ = ("Endpoint", "Entry")


class Endpoint(object):
    """
    An endpoint represents a portion of a service catalog.

    :ivar unicode tenant_id: A tenant ID for this endpoint.
    :ivar unicode region: The region name for this endpoint.
    :ivar unicode endpoint_id: The endpoint ID; used only in some auth
        responses, not the basic service catalog.
    :ivar unicode prefix: A prefix, usually a version number, for this
        endpoint.
    :ivar boolean external: whether or not the Endpoint is external
        to Mimic.
    :ivar unicode complete_url: the full URL for the Endpoint if it
        is external to Mimic.
    """
    def __init__(self, tenant_id, region, endpoint_id, prefix=None,
                 external=False, complete_url=None, internal_url=None):
        """
        Create an endpoint for a service catalog entry.
        """
        self.tenant_id = tenant_id
        self.region = region
        self.endpoint_id = endpoint_id
        self.prefix = prefix
        self.external = external
        self.complete_url = complete_url
        if internal_url is None:
            self.internal_url = complete_url
        else:
            self.internal_url = internal_url

        # Gate Check complete_url
        if self.external and self.complete_url is None:
            raise ValueError(
                'complete_url must be specified when API is external'
            )

    def url_with_prefix(self, uri_prefix, internal_url=False):
        """
        Generate a URL to this endpoint, given the URI prefix for the service.

        :param text_type uri_prefix: prefix to start the URL with, e.g the
            Request's Base URL
        :param boolean internal_url: whether or not to provide the Internal or
            Public URL. If True, provide the internal URL.

        .. note::

            internal_url is only honored by External APIs, e.g `external` is
            set to `True`. For internally hosted APIs the internal_url and
            public_url should be the same.

        :rtype: unicode
        """
        if self.external and self.complete_url is not None:
            if internal_url:
                return self.internal_url
            else:
                return self.complete_url
        else:
            # internal_url is ignored as anything hosted internally in
            # mimic will always use the same URL.
            postfix = self.tenant_id
            segments = [uri_prefix.rstrip(u"/")]
            if self.prefix is not None:
                segments.append(self.prefix)
            segments.append(postfix)
            return u"/".join(segments)


class Entry(object):
    """
    An :obj:`Entry` is an entry in a service catalog.

    :ivar str tenant_id: A tenant ID for this entry.
    :ivar str name: A name for this entry.
    :ivar iterable endpoints: Iterable of :obj:`Endpoint` objects.
    """
    def __init__(self, tenant_id, type, name, endpoints):
        """
        Create a service catalog entry with the given tenant ID, service type,
        service name and list of endpoints (represented as :obj:`Endpoint`
        instances).
        """
        self.type = type
        self.tenant_id = tenant_id
        self.name = name
        self.endpoints = endpoints
