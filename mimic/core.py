# -*- test-case-name: mimic.test.test_core -*-

"""
Service catalog hub and integration for Mimic application objects.
"""

from __future__ import unicode_literals

from twisted.python.urlpath import URLPath
from twisted.plugin import getPlugins
from mimic import plugins

from mimic.imimic import IAPIMock
from mimic.session import SessionStore
from mimic.util.helper import random_hex_generator
from mimic.model.mailgun_objects import MessageStore
from mimic.model.customer_objects import ContactsStore
from mimic.model.ironic_objects import IronicNodeStore
from mimic.model.glance_objects import GlanceAdminImageStore
from mimic.model.valkyrie_objects import ValkyrieStore


class MimicCore(object):
    """
    A MimicCore contains a mapping from URI prefixes to particular service
    mocks.
    """

    def __init__(self, clock, apis):
        """
        Create a MimicCore with an IReactorTime to do any time-based scheduling
        against.

        :param clock: an IReactorTime which will be used for session timeouts
            and determining timestamps.
        :type clock: :obj:`twisted.internet.interfaces.IReactorTime`

        :param apis: an iterable of all :obj:`IAPIMock`s that this MimicCore
            will expose.
        """
        self._uuid_to_api = {}
        self.sessions = SessionStore(clock)
        self.message_store = MessageStore()
        self.contacts_store = ContactsStore()
        self.ironic_node_store = IronicNodeStore()
        self.glance_admin_image_store = GlanceAdminImageStore()
        self.valkyrie_store = ValkyrieStore()

        for api in apis:
            this_api_id = ((api.__class__.__name__) + '-' +
                           random_hex_generator(3))
            self._uuid_to_api[this_api_id] = api

    @classmethod
    def fromPlugins(cls, clock):
        """
        Create a :obj:`MimicCore` from all :obj:`IAPIMock` plugins.
        """
        return cls(clock, list(getPlugins(IAPIMock, plugins)))

    def service_with_region(self, region_name, service_id, base_uri):
        """
        Given the name of a region and a mimic internal service ID, get a
        resource for that service.

        :param unicode region_name: the name of the region that the service
            resource exists within.
        :param unicode service_id: the UUID for the service for the
            specified region
        :param str base_uri: the base uri to use instead of the default -
            most likely comes from a request URI

        :return: A resource.
        :rtype: :obj:`twisted.web.iweb.IResource`
        """
        if service_id in self._uuid_to_api:
            api = self._uuid_to_api[service_id]
            return api.resource_for_region(
                region_name,
                self.uri_for_service(region_name, service_id, base_uri),
                self.sessions,
            )

    def uri_for_service(self, region, service_id, base_uri):
        """
        Generate a URI prefix for a given region and service ID.

        Each plugin loaded into mimic generates a list of catalog entries; each
        catalog entry has a list of endpoints.  Each endpoint has a URI
        associated with it, which we call a "URI prefix", because the endpoint
        will have numerous other URIs beneath it in the hierarchy, generally
        starting with a version number and tenant ID.  The URI prefixes
        generated for this function point to the top of the endpoint's
        hierarchy, not including any tenant information.

        :param unicode region: the name of the region that the service resource
            exists within.
        :param unicode service_id: the UUID for the service for the specified
            region
        :param str base_uri: the base uri to use instead of the default - most
            likely comes from a request URI

        :return: The full URI locating the service for that region
        :rtype: ``str``
        """
        return str(URLPath.fromString(base_uri)
                   .child("mimicking").child(service_id).child(region).child(""))

    def entries_for_tenant(self, tenant_id, prefix_map, base_uri):
        """
        Get all the :obj:`mimic.catalog.Entry` objects for the given tenant ID,
        populating a mapping of :obj:`mimic.catalog.Entry` to URI prefixes (as
        described by :pyobj:`MimicCore.uri_for_service`) for that entry.

        :param unicode tenant_id: A fictional tenant ID.
        :param dict prefix_map: a mapping of entries to uris
        :param str base_uri: the base uri to use instead of the default - most
            likely comes from a request URI

        :return: The full URI locating the service for that region
        """
        for service_id, api in self._uuid_to_api.items():
            for entry in api.catalog_entries(tenant_id):
                for endpoint in entry.endpoints:
                    prefix_map[endpoint] = self.uri_for_service(
                        endpoint.region, service_id, base_uri
                    )
                yield entry
