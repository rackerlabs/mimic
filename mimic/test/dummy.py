"""
Dummy classes that can be shared across test cases
"""

from __future__ import absolute_import, division, unicode_literals

import uuid

from six import text_type

from zope.interface import implementer

from twisted.plugin import IPlugin
from twisted.web.resource import Resource

from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.imimic import IAPIMock, IAPIDomainMock
from mimic.model.identity_objects import (
    ExternalApiStore,
    EndpointTemplateStore
)


class ExampleResource(Resource):
    """
    Simple resource that returns a string as the response
    """
    isLeaf = True

    def __init__(self, response_message):
        """
        Has a response message to return when rendered
        """
        self.response_message = response_message

    def render_GET(self, request):
        """
        Render whatever message was passed in
        """
        return self.response_message


@implementer(IAPIMock, IPlugin)
class ExampleAPI(object):
    """
    Example API that returns NoResource
    """
    def __init__(self, response_message="default message", regions_and_versions=[('ORD', 'v1')]):
        """
        Has a dictionary to store information from calls, for testing
        purposes
        """
        self.store = {}
        self.regions_and_versions = regions_and_versions
        self.response_message = response_message

    def catalog_entries(self, tenant_id):
        """
        List catalog entries for the Nova API.
        """
        endpoints = [Endpoint(tenant_id, each[0], 'uuid', each[1]) for each in self.regions_and_versions]
        return [Entry(tenant_id, "serviceType", "serviceName", endpoints)]

    def resource_for_region(self, region, uri_prefix, session_store):
        """
        Return no resource.
        """
        self.store['uri_prefix'] = uri_prefix
        return ExampleResource(self.response_message)


@implementer(IAPIDomainMock, IPlugin)
class ExampleDomainAPI(object):
    """
    Example domain API the return nothing.
    """

    def __init__(self, domain=u"api.example.com", response=b'"test-value"'):
        """
        Create an :obj:`ExampleDomainAPI`.

        :param text_type domain: the domain to respond with
        :param bytes response: the HTTP response body for all contained
            resources
        """
        self._domain = domain
        self._response = response

    def domain(self):
        """
        The domain for the ExampleDomainAPI.
        """
        return self._domain

    def resource(self):
        """
        The resource for the ExampleDomainAPI.
        """
        example_resource = ExampleResource(self._response)
        return example_resource


def exampleEndpointTemplate(name=u"example", region="EXTERNAL", version="v1",
                            url="https://api.external.example.com:8080",
                            public_url=None, internal_url=None, admin_url=None,
                            version_info_url=None, version_list_url=None,
                            type_id=u"example", enabled=False,
                            endpoint_uuid=None,
                            tenantid_alias="%tenant_id%"):
    """
    Create an instance of the :obj:`EndpointTemplateStore` in a usable form for
    testing.

    :param text_type name: name of the service provided, e.g Cloud Files.
    :param text_type region: region the service is provided in, e.g ORD.
    :param text_type version: version of the service, e.g v1.
    :param text_type url: basic URL of the service in the region.
    :param text_type public_url: public URL of the service in the region.
    :param text_type internal_url: internal URL of the service in
        the region.
    :param text_type admin_url: administrative URL for the service in
        the region.
    :param text_type version_info_url: URL to get the version information
        of the service.
    :param text_type version_list_url: URL to get the list of supported
        versions by the service.
    :param text_type type_id: service type, e.g object-store
    :param boolean enabled: whether or not the service is enabled
        for all users. Services can be disabled for all tenants but still
        be enabled on a per-tenant basis.
    :param text_type endpoint_uuid: unique ID for the endpoint within the
        service.
    :param text_type tenantid_alias: by default the system uses the text
        '%tenant_id%' for what to replace in the URLs with the tenantid.
        This value allows the service adminstrator to use a different
        textual value. Note: This is not presently used by Mimic which
        just appends the tenant-id for internally hosted services, and
        simply uses the URLs as is for externally hosted services.
    :rtype: :obj:`EndpointTemplateStore`
    """
    return EndpointTemplateStore(
        id_key=(endpoint_uuid
                if endpoint_uuid is not None
                else text_type(uuid.uuid4())),
        region_key=region,
        type_key=type_id,
        name_key=name,
        enabled_key=enabled,
        public_url=public_url if public_url is not None else url,
        internal_url=internal_url if internal_url is not None else url,
        admin_url=admin_url if admin_url is not None else url,
        tenant_alias=tenantid_alias,
        version_id=version,
        version_info=(version_info_url
                      if version_info_url is not None
                      else url + '/versionInfo'),
        version_list=(version_list_url
                      if version_list_url is not None
                      else url + '/versions'))


def make_example_internal_api(case, response_message="default message",
                              regions_and_versions=None):
    """
    Intialize an :obj:`ExampleAPI`.
    """
    if regions_and_versions is None:
        regions_and_versions = [('ORD', 'v1')]

    iapi = ExampleAPI(
        response_message=response_message,
        regions_and_versions=regions_and_versions
    )
    case.assertIsNotNone(iapi)
    return iapi


def make_example_external_api(case, name=u"example",
                              endpoint_templates=None,
                              set_enabled=None,
                              service_type=None):
    """
    Initialize an :obj:`ExternalApiStore` for a given name.

    :param text_type name: user-visible name of the service.
    :param list endpoint_templates: list of endpoint templates to
        initialize the API store with.
    :param boolean or None set_enabled: If none, the endpoint templates
        are used AS-IS. If a boolean type, then it sets all the templates
        to have the same default accessibility for all tenants.
    :param text_type service_type: type of the service. If none, the type
        is extracted from the first entry in the endpoint_template list.

    .. note:: The service-type of the first endpoint template is used as the
        service type for the entire :obj:`ExternalApiStore`, and is enforced
        that all endpoint templates have the same service-type.

    :returns: an instance of :obj:`ExternalApiStore`.
    :raises: ValueError if the service-type does not match between all the
        endpoint templates.
    """
    if endpoint_templates is None:
        endpoint_templates = [exampleEndpointTemplate()]
        # if service type was specified then set it in order
        # to satisfy the check in the loop below
        if service_type is not None:
            endpoint_templates[0].type_key = service_type

    if service_type is None:
        # default parameter value, take the template type from the first
        # endpoint template in the list
        service_type = endpoint_templates[0].type_key

    # Validate that the provided templates will be usable by the
    # :obj:`ExternalApiStore` being created.
    for ept in endpoint_templates:
        # the name is in the parameter, so just set it
        ept.name_key = name

        # validate that the service type matches
        if ept.type_key != service_type:
            raise ValueError(
                'Service Types do not match. {0} != {1}'.format(
                    ept.type_key,
                    service_type
                )
            )

        if set_enabled is not None and isinstance(set_enabled, bool):
            ept.enabled_key = set_enabled

    eeapi = ExternalApiStore(
        "uuid-" + name,
        name,
        service_type,
        endpoint_templates
    )
    case.assertIsNotNone(eeapi)
    return eeapi
