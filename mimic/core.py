# -*- test-case-name: mimic.test.test_core -*-

"""
Service catalog hub and integration for Mimic application objects.
"""

from __future__ import absolute_import, division, unicode_literals

from twisted.python.urlpath import URLPath
from twisted.plugin import getPlugins
from mimic import plugins

from mimic.imimic import (
    IAPIMock,
    IAPIDomainMock,
    IExternalAPIMock
)
from mimic.session import SessionStore
from mimic.util.helper import random_hex_generator
from mimic.model.mailgun_objects import MessageStore
from mimic.model.customer_objects import ContactsStore
from mimic.model.ironic_objects import IronicNodeStore
from mimic.model.glance_objects import GlanceAdminImageStore
from mimic.model.valkyrie_objects import ValkyrieStore


class MimicCoreException(Exception):
    """
    Parent for all Exceptions related to MimicCore
    """


class ServiceBadInterface(MimicCoreException):
    """
    Service does not implement the required interface.
    """


class ServiceExistenceError(MimicCoreException):
    """
    Exceptions related to Service Existence
    """


class ServiceDoesNotExist(ServiceExistenceError):
    """
    API does not exist
    """


class ServiceExists(ServiceExistenceError):
    """
    API Already Exists
    """


class ServiceIdExists(ServiceExists):
    """
    API with the same ID already exists.
    """


class ServiceNameExists(ServiceExists):
    """
    API with the same name already exists.
    """


class ServiceStateError(MimicCoreException):
    """
    Exceptions related to Service States
    """


class ServiceHasTemplates(ServiceStateError):
    """
    Service still has assigned templates.
    """


class MimicCore(object):
    """
    A MimicCore contains a mapping from URI prefixes to particular service
    mocks.

    :attr _uuid_to_api_internal: dictionary of the internally mocked APIs
        that will show up in the Service Catalog
    :attr _uuid_to_api_external: dictionary of the hosted external APIs
        that will show up in the Service Catalog
    """

    def __init__(self, clock, apis, domains=()):
        """
        Create a MimicCore with an IReactorTime to do any time-based scheduling
        against.

        :param clock: an IReactorTime which will be used for session timeouts
            and determining timestamps.
        :type clock: :obj:`twisted.internet.interfaces.IReactorTime`

        :param apis: an iterable of all :obj:`IAPIMock` and
            :obj:`IAPIExternalAPI` mocks that this MimicCore will expose.

        :param domains: an iterable of all :obj:`IAPIDomainMock`s that this
            MimicCore will expose.
        """
        self._uuid_to_api_internal = {}
        self._uuid_to_api_external = {}
        self.sessions = SessionStore(clock)
        self.message_store = MessageStore()
        self.contacts_store = ContactsStore()
        self.ironic_node_store = IronicNodeStore()
        self.glance_admin_image_store = GlanceAdminImageStore()
        self.valkyrie_store = ValkyrieStore()
        self.domains = list(domains)

        for api in apis:
            self.add_api(api)

    @classmethod
    def fromPlugins(cls, clock):
        """
        Create a :obj:`MimicCore` from all :obj:`IAPIMock` and
        :obj:`IAPIDomainMock` plugins.
        """
        service_catalog_plugins = getPlugins(IAPIMock, plugins)
        domain_plugins = getPlugins(IAPIDomainMock, plugins)
        return cls(clock, service_catalog_plugins, domain_plugins)

    def add_api(self, api):
        """
        Add a new API to the listing.

        :param object api: An object implementing either the
            :obj:`IAPIMock` or :obj:`IExternalAPIMock` interfaces.
        :raises: TypeError if the object does not implement the
            correct interfaces.
        """
        # Gate check the API to make sure it implements one of the
        # supported interfaces
        if IExternalAPIMock.providedBy(api):
            # External APIs need to be able to be easily managed by
            # the same object so long as they have the same uuid
            this_api_id = api.uuid_key

            if this_api_id in self._uuid_to_api_external:
                raise ServiceIdExists(
                    'An Existing API already exists with the given UUID'
                )

            for existing_api in self._uuid_to_api_external.values():
                if existing_api.name_key == api.name_key:
                    raise ServiceNameExists(
                        'An Existing API with UUID ' + existing_api.uuid_key +
                        ' is already using that name'
                    )
            self._uuid_to_api_external[this_api_id] = api
        elif IAPIMock.providedBy(api):
            # Internal APIs can be added easily on the fly since
            # they also provide the resource for implementing the API
            this_api_id = ((api.__class__.__name__) + '-' +
                           random_hex_generator(3))
            self._uuid_to_api_internal[this_api_id] = api
        else:
            raise ServiceBadInterface(
                api.__class__.__module__ + '/' +
                api.__class__.__name__ +
                " does not implement IAPIMock or IExternalAPIMock"
            )

    def remove_external_api(self, api_id):
        """
        Remove an External API from the listing.

        :param text_type api_id: the id of the API instance
            e.g 3845-39583, cloudfiles-mimic
        """
        if api_id in self._uuid_to_api_external:
            api = self._uuid_to_api_external[api_id]

            if len(api.list_templates()) == 0:
                del self._uuid_to_api_external[api_id]
            else:
                raise ServiceHasTemplates("API still has endpoint templates")
        else:
            raise ServiceDoesNotExist(api_id + " is not a valid external API")

    def get_external_apis(self):
        """
        Return the list of external API names

        :returns: iterable of service ids for the external APIs
        """
        return self._uuid_to_api_external.keys()

    def get_external_api(self, api_id):
        """
        Access an API instance for an external API.

        .. note::

            Internally hosted APIs are not modifiable at run-time
            so this only returns access to the Externally hosted API.

        :param text_type api_id: the id of the API instance
        :returns: The :obj:`IExternalAPIMock` instance supporting the
            externally hosted API.
        :raises: IndexError if it is unable to find an API by the given
            name.
        """
        if api_id in self._uuid_to_api_external:
            return self._uuid_to_api_external[api_id]
        else:
            raise ServiceDoesNotExist(
                "Unable to locate an API  the id" + str(api_id)
            )

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
        if service_id in self._uuid_to_api_internal:
            api = self._uuid_to_api_internal[service_id]
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
                   .child(b"mimicking").child(service_id.encode("utf-8"))
                   .child(region.encode("utf-8")).child(b""))

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
        # Return all the external APIs
        for service_id, api in self._uuid_to_api_external.items():
            for entry in api.catalog_entries(tenant_id):
                for endpoint in entry.endpoints:
                    prefix_map[endpoint] = api.uri_for_service(
                        endpoint.region, service_id
                    )
                yield entry

        # Return all the internal APIs
        for service_id, api in self._uuid_to_api_internal.items():
            for entry in api.catalog_entries(tenant_id):
                for endpoint in entry.endpoints:
                    prefix_map[endpoint] = self.uri_for_service(
                        endpoint.region, service_id, base_uri
                    )
                yield entry
