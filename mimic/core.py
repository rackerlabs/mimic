# -*- test-case-name: mimic.test.test_core -*-

"""
Service catalog hub and integration for Mimic application objects.
"""

from __future__ import absolute_import, division, unicode_literals

from twisted.python.urlpath import URLPath
from twisted.plugin import getPlugins
from mimic import plugins

from mimic.imimic import IAPIMock, IAPIDomainMock
from mimic.session import SessionStore
from mimic.util.helper import random_hex_generator
from mimic.model.mailgun_objects import MessageStore
from mimic.model.customer_objects import ContactsStore
from mimic.model.ironic_objects import IronicNodeStore
from mimic.model.glance_objects import GlanceAdminImageStore
from mimic.model.valkyrie_objects import ValkyrieStore


class _MimicCoreApiWrapperEntry(object):
    """
    Wrap an API entry to be able to distinguish between internally
    hosted implemented as :obj:`IAPIMock` and externally hosted APIs
    that do not live within Mimic.
    """

    def __init__(self, api, external):
        """
        Create a wrapped :obj:`IAPIMock` entry

        :param api: the :obj:`IAPIMock` instance to wrap
        :param external: boolean value of whether the :obj:`IAPIMock`
            is internally or externally hosted.
        """
        self.api = api
        self.base_uri = None
        self.external = external
        self.api_uuid = ((api.__class__.__name__) + '-' +
                         random_hex_generator(3))

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
            likely comes from a request URI. If the API is external to Mimic
            and it's base_uri is set, then that value will override the
            provided parameter.

        :return: The full URI locating the service for that region
        :rtype: ``str``
        """
        if self.external and self.base_uri is not None:
            base_uri = self.base_uri

        return str(URLPath.fromString(base_uri)
                   .child(b"mimicking").child(service_id.encode("utf-8"))
                   .child(region.encode("utf-8")).child(b""))


class _MimicCoreApiContainer(dict):
    """
    Specialized Dict for managing the wrapped APIs such that the rest
    of the system should not necessarily need to know about the
    wrapper.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a new dict-like object and store any provided entries
        """
        super(_MimicCoreApiContainer, self).__init__()
        self.update(*args, **kwargs)

    def __getitem__(self, key):
        """
        Retrieve the API instead of the Wrapped API object

        :param key: the dictionary key used to access the API

        :returns: the :obj:`IAPIMock` instance
        """
        item = super(_MimicCoreApiContainer, self).__getitem__(key)
        return item.api if item is not None else None

    def __setitem__(self, key, val):
        """
        Add a new entry into the dictionary. If the entry is not
        already an object wrapped by :obj:`MimicCoreApiWrapperEntry`
        then wrap it and specify that it is not hosted externally. Callers
        can use `get_wrapper()` if this needs to be changed.

        Note: _MimicCoreApiWrapperEntry provides the key generation
        mechanism. The specified key will be ignored in favor of the
        value returned by the wrapper.

        :param key: ignored in favor of
            :obj:`_MimicCoreApiWrapperEntry`'s `api_uuid` attribute.
        :param val: API instance to stored. If the instance is already
            wrapped by :obj:`MimicCoreApiWrapperEntry` then it uses
            it as is; otherwise it wraps it.
        """
        if not isinstance(val, _MimicCoreApiWrapperEntry):
            val = _MimicCoreApiWrapperEntry(val, False)

        key = val.api_uuid
        super(_MimicCoreApiContainer, self).__setitem__(key, val)

    def __repr__(self):
        """
        Generate a representation of the instance
        """
        return '%s(%s)'.format(
            type(self),
            super(_MimicCoreApiContainer, self).__repr__()
        )

    def update(self, *args, **kwargs):
        """
        Update the entire dictionary contents but force use of
        `__setitem__()` so that everything is wrapped properly
        """
        source = dict(*args, **kwargs)
        for k in source.keys():
            self[k] = source[k]

    def set(self, key, val):
        """
        Add a new entry to the dictionary, see `__setitem__()` for
        details.
        """
        self.__setitem__(key, val)

    def get(self, key):
        """
        Retrieve an existing entry from the dictionary. See
        `__getitem__()` for details.
        """
        return self.__getitem__(key)

    def get_wrapper(self, key):
        """
        Retrieve the :obj:`_MimicCoreApiWrapperEntry` instance for
        the API in order to update or modify it.
        """
        return super(_MimicCoreApiContainer, self).__getitem__(key)

    def values_unwrapped(self):
        return [v.api for v in self.values()]


class MimicCore(object):
    """
    A MimicCore contains a mapping from URI prefixes to particular service
    mocks.
    """

    def __init__(self, clock, apis, domains=()):
        """
        Create a MimicCore with an IReactorTime to do any time-based scheduling
        against.

        :param clock: an IReactorTime which will be used for session timeouts
            and determining timestamps.
        :type clock: :obj:`twisted.internet.interfaces.IReactorTime`

        :param apis: an iterable of all :obj:`IAPIMock`s that this MimicCore
            will expose.

        :param domains: an iterable of all :obj:`IAPIDomainMock`s that this
            MimicCore will expose.
        """
        self._uuid_to_api = _MimicCoreApiContainer()
        self.sessions = SessionStore(clock)
        self.message_store = MessageStore()
        self.contacts_store = ContactsStore()
        self.ironic_node_store = IronicNodeStore()
        self.glance_admin_image_store = GlanceAdminImageStore()
        self.valkyrie_store = ValkyrieStore()
        self.domains = list(domains)

        for api in apis:
            wrapped_api = _MimicCoreApiWrapperEntry(api, False)
            self._uuid_to_api[wrapped_api.api_uuid] = wrapped_api

    @classmethod
    def fromPlugins(cls, clock):
        """
        Create a :obj:`MimicCore` from all :obj:`IAPIMock` and
        :obj:`IAPIDomainMock` plugins.
        """
        service_catalog_plugins = getPlugins(IAPIMock, plugins)
        domain_plugins = getPlugins(IAPIDomainMock, plugins)
        return cls(clock, service_catalog_plugins, domain_plugins)

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
            api = self._uuid_to_api.get_wrapper(service_id)
            return api.api.resource_for_region(
                region_name,
                api.uri_for_service(region_name, service_id, base_uri),
                self.sessions,
            )

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
            for entry in api.api.catalog_entries(tenant_id):
                for endpoint in entry.endpoints:
                    prefix_map[endpoint] = api.uri_for_service(
                        endpoint.region, service_id, base_uri
                    )
                yield entry
