"""
Model objects for the Identity mimic.
"""

from __future__ import absolute_import, division, unicode_literals

import attr

from zope.interface import implementer

from twisted.plugin import IPlugin
from twisted.web.http import (
    BAD_REQUEST,
    CONFLICT,
    NOT_FOUND,
    UNAUTHORIZED,
)

from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.imimic import IExternalAPIMock, IEndpointTemplate
from mimic.model.identity_errors import (
    EndpointTemplateAlreadyExists,
    EndpointTemplateDisabledForTenant,
    EndpointTemplateDoesNotExist,
    InvalidEndpointTemplateId,
    InvalidEndpointTemplateInterface,
    InvalidEndpointTemplateMissingKey,
    InvalidEndpointTemplateServiceType
)


def _identity_error_message(msg_type, message, status_code, request):
    """
    Set the response code on the request, and return a JSON blob representing
    a Identity error body, in the format Identity returns error messages.

    :param str msg_type: What type of error this is - something like
        "badRequest" or "itemNotFound" for Identity.
    :param str message: The message to include in the body.
    :param int status_code: The status code to set
    :param request: the request to set the status code on

    :return: dictionary representing the error body
    """
    request.setResponseCode(status_code)
    return {
        msg_type: {
            "message": message,
            "code": status_code
        }
    }


def bad_request(message, request):
    """
    Return a 400 error body associated with a Identity bad request error.
    Also sets the response code on the request.

    :param str message: The message to include in the bad request body.
    :param request: The request on which to set the response code.

    :return: dictionary representing the error body.
    """
    return _identity_error_message("badRequest", message, BAD_REQUEST, request)


def conflict(message, request):
    """
    Return a 409 error body associated with a Identity bad request error.
    Also sets the response code on the request.

    :param str message: The message to include in the bad request body.
    :param request: The request on which to set the response code.

    :return: dictionary representing the error body.
    """
    return _identity_error_message("conflict", message, CONFLICT, request)


def not_found(message, request):
    """
    Return a 404 error body associated with a Identity not found error.
    Also sets the response code on the request.

    :param str message: The message to include in the bad request body.
    :param request: The request on which to set the response code.

    :return: dictionary representing the error body.
    """
    return _identity_error_message("itemNotFound", message, NOT_FOUND, request)


def unauthorized(message, request):
    """
    Return a 401 error body associated with a Identity unauthoriazed error.
    Also sets the response code on the request.

    :param str message: The message to include in the bad request body.
    :param request: The request on which to set the response code.

    :return: dictionary representing the error body.
    """
    return _identity_error_message("unauthorized", message, UNAUTHORIZED, request)


@attr.s
class MapInfo(object):
    """
    Mapping information for Endpoint Template JSON serialization
    and deserialization capabilities.

    :ivar spec_key: JSON Key in the OpenStack Identity Template Spec
    :ivar attr_key: Attribute Name of the :obj:`EndpointTemplateStore`
    :ivar default_value: optional default values
    """
    spec_key = attr.ib()
    attr_name = attr.ib()
    default_value = attr.ib(default=None)


@implementer(IEndpointTemplate, IPlugin)
@attr.s
class EndpointTemplateStore(object):
    """
    A :obj"`EndpointTemplateStore` is an internal representation of the
    OSKS-Catalog Extension's Endpoint Template.

    :cvar list required_mapping: list of entries in the template that are
        required to be present for a valid template
    :cvar list optional_mapping: list of entries in the template that are
        optionally present in a valid template, along with a default value.
    :cvar list tenant_mapping: list of entries in the template that are
        required to be present for a valid template for a specific
        tenant


    .. note:: The OpenStack documentation[0] does not specify any required
        parameters. For this implementation, the `id`, `region`, `type`,
        and `name` fields are required. The `name` and `type` fields
        are used for creating an instance of the :obj:`ExternalApiStore`
        that will enable the listing to be put into the Service Catalog;
        the `id` and `region` fields are used by the :obj:`ExternalApiStore`
        for managing the templates.

    `The OpenStack documentation <http://developer.openstack.org/api-ref-identity-v2-ext.html>`
    """

    required_mapping = [
        MapInfo(*value) for value in [
            ('id', 'id_key'),
            ('region', 'region_key'),
            ('type', 'type_key'),
            ('name', 'name_key'),
        ]
    ]

    optional_mapping = [
        MapInfo(*value) for value in [
            ('enabled', 'enabled_key', False),
            ('publicURL', 'public_url', u""),
            ('internalURL', 'internal_url', u""),
            ('adminURL', 'admin_url', u""),
            ('RAX-AUTH:tenantAlias', 'tenant_alias', "%tenant_id%"),
            ('versionId', 'version_id', u""),
            ('versionInfo', 'version_info', u""),
            ('versionList', 'version_list', u"")
        ]
    ]

    tenant_mapping = [
        MapInfo(*value) for value in [
            ('id', 'id_key'),
            ('region', 'region_key'),
            ('type', 'type_key'),
            ('publicURL', 'public_url'),
            ('internalURL', 'internal_url'),
            ('adminURL', 'admin_url'),
        ]
    ]

    _template_data = attr.ib(default=None)
    id_key = attr.ib(default=None)
    region_key = attr.ib(default=None)
    type_key = attr.ib(default=None)
    name_key = attr.ib(default=None)
    enabled_key = attr.ib(default=None)
    public_url = attr.ib(default=None)
    internal_url = attr.ib(default=None)
    admin_url = attr.ib(default=None)
    tenant_alias = attr.ib(default=None)
    version_id = attr.ib(default=None)
    version_info = attr.ib(default=None)
    version_list = attr.ib(default=None)

    def get_url(self, url, tenant_id):
        """
        Apply the tenant_id replacement to the URL.

        :param text_type url: the URL to do the replacement on.
        :param text_type tenant_id: the tenant-id to insert into the URL.
        """
        value_to_replace = self.tenant_alias
        if value_to_replace is None:
            value_to_replace = '%tenant_id%'

        return url.replace(value_to_replace, tenant_id)

    def serialize(self, tenant_id=None):
        """
        Serialize the endpoint template to a dictionary.

        :param text_type tenant_id: an optional parameter to limit the
            serialization to only values to a subset for tenant-specific
            template information.
        """
        data = {}
        if tenant_id is None:
            for m in self.required_mapping:
                data[m.spec_key] = getattr(self, m.attr_name)

            for m in self.optional_mapping:
                value = getattr(self, m.attr_name)
                if value is not None:
                    data[m.spec_key] = value
            return data
        else:
            data['tenantId'] = tenant_id
            for m in self.tenant_mapping:
                value = getattr(self, m.attr_name)
                if value is not None:
                    data[m.spec_key] = value
            return data

    @classmethod
    def deserialize(cls, data):
        """
        Deserialize the endpoint template from a dictionary.

        :param dict data: a dictionary of values to import the template data
            from.
        :rtype: EndpointTemplateStore
        :returns: instance of :obj:`EndpointTemplateStore` with the
            instantiated against the template data
        """
        epts = cls()
        epts._template_data = data
        for m in cls.required_mapping:
            if m.spec_key not in data:
                raise InvalidEndpointTemplateMissingKey(
                    'Missing required value ' + m.spec_key)

            setattr(epts, m.attr_name, data[m.spec_key])

        for m in cls.optional_mapping:
            value = m.default_value
            if m.spec_key in data:
                value = data[m.spec_key]
            setattr(epts, m.attr_name, value)

        return epts


@implementer(IExternalAPIMock, IPlugin)
class ExternalApiStore(object):
    """
    A :obj:`ExternalApiStore` provides management of APIs External to Mimic
    through the use of endpoint templates per the Identity v2 OS-KSCATALOG
    extension. Each template can be enabled globally or per tenant. Enabled
    templates show up in the Service Catalog; disabled Templates only show
    up in the OS-KSCATALOG administrative functionality and do not otherwise
    impact users. Each :obj:`ExternalApiStore` instance manages a specific
    service (e.g Cloud Files, Cloud Servers, etc); there may be several
    services of the same service type (e.g object-store) but with different
    service names (e.g Cloud Files, OpenStack Swift).

    .. note:: An endpoint template typically maps to a region.

    Work-In-Progress: Implementation is unstable and subject to change.
    """

    def __init__(self, service_uuid, service_name, service_type,
                 api_templates=[], description="External API"):
        """
        Initialize an :obj:`ExternalApiStore` for a given service.

        :param six.text_type service_uuid: unique identifier for the API
        :param six.text_type service_name: name of the service being provided,
            f.e Cloud Files, Identity
        :param six.text_type service_type: type of the service being provided,
            f.e object-store, auth
        :param iterable api_templates: iterable of templates to add during
            initialization
        """
        self.name_key = service_name
        self.type_key = service_type
        self.uuid_key = service_uuid
        self.description = description

        # Listing of tenant-specific endpoints
        # tenant-id is the key
        self.endpoints_for_tenants = {}

        # Listing of the global endpoint templates
        # id_key is the key
        self.endpoint_templates = {}

        # Add the APIs
        for api_template in api_templates:
            self.add_template(api_template)

    def list_tenant_endpoints(self, tenant_id):
        """
        List the tenant specific endpoints.

        :param six.text_type tenant_id: tenant id to operate on
        :returns: an iterable of the endpoints available for the specified
            tenant id
        :rtype: iterable
        """
        # List of template IDs that should be provided for a template
        # regardless of the enabled/disabled status of the template itself
        tenant_specific_templates = []
        if tenant_id in self.endpoints_for_tenants:
            for template_id in self.endpoints_for_tenants[tenant_id]:
                tenant_specific_templates.append(template_id)

        # provide an Endpoint Entry for every template that is either
        # (a) enabled or (b) in the list of endpoints specifically
        # enabled for the tenant
        endpoints = []
        for _, endpoint_template in self.endpoint_templates.items():
            if (endpoint_template.enabled_key or
                    endpoint_template.id_key in tenant_specific_templates):
                endpoints.append(
                    Endpoint(
                        tenant_id,
                        endpoint_template.region_key,
                        endpoint_template.id_key,
                        endpoint_template.version_id,
                        external=True,
                        complete_url=endpoint_template.get_url(
                            endpoint_template.public_url,
                            tenant_id
                        ),
                        internal_url=endpoint_template.get_url(
                            endpoint_template.internal_url,
                            tenant_id
                        )
                    )
                )
        return endpoints

    def list_tenant_templates(self, tenant_id):
        """
        List the tenant specific endpoints.

        :param text_type tenant_id: tenant id to operate on
        :returns: an iterable of the endpoint templates available for the
            specified tenant id
        """
        # List of template IDs that should be provided for a template
        # regardless of the enabled/disabled status of the template itself
        tenant_specific_templates = []
        if tenant_id in self.endpoints_for_tenants:
            for template_id in self.endpoints_for_tenants[tenant_id]:
                tenant_specific_templates.append(template_id)

        # provide an Endpoint Entry for every template that is either
        # (a) enabled or (b) in the list of endpoints specifically
        # enabled for the tenant
        for _, endpoint_template in self.endpoint_templates.items():
            if (endpoint_template.enabled_key or
                    endpoint_template.id_key in tenant_specific_templates):
                yield endpoint_template

    def enable_endpoint_for_tenant(self, tenant_id, template_id):
        """
        Enable an endpoint for a specific tenant.

        :param six.text_type tenant_id: tenant id to operate on
        :param six.text_type template_id: endpoint template id to enable
        :raises: ValueError if the template id is not found
        """
        if tenant_id not in self.endpoints_for_tenants:
            self.endpoints_for_tenants[tenant_id] = []

        for key, endpoint_template in self.endpoint_templates.items():
            if endpoint_template.id_key == template_id:
                self.endpoints_for_tenants[tenant_id].append(template_id)
                return

        raise InvalidEndpointTemplateId(template_id + " is not valid")

    def disable_endpoint_for_tenant(self, tenant_id, template_id):
        """
        Disable an endpoint for a specific tenant.

        :param six.text_type tenant_id: tenant id to operate on
        :param six.text_type template_id: endpoint template id to disable
        :raises: ValueError if template is not enabled for the tenant
        """
        if tenant_id in self.endpoints_for_tenants:
            if template_id in self.endpoints_for_tenants[tenant_id]:
                self.endpoints_for_tenants[tenant_id].remove(template_id)
                return

        # Tell the caller if the template did not exist in case the caller
        # needs to generate error messages
        raise EndpointTemplateDisabledForTenant(
            "template (" + template_id + ") not enabled for tenant id ("
            + tenant_id + ")"
        )

    def list_templates(self):
        """
        List the available templates.

        :returns: an iterable of the endpoint templates
        :rtype: iterable
        """
        return self.endpoint_templates.values()

    def add_template(self, endpoint_template):
        """
        Add a new template for the external API.

        :param six.text_type endpoint_template: a :obj:`IEndpointTemplate` to add to the
            :obj:`IExternalAPIMock` instance
        :raises: ValueError if the endpoint template has already been added
        :raises: TypeError if the endpoint template does not implement
            the expected interface (IEndpointTempalte)
        """
        if IEndpointTemplate.providedBy(endpoint_template):
            key = endpoint_template.id_key

            if key in self.endpoint_templates:
                raise EndpointTemplateAlreadyExists(
                    key + " already exists. Please call update.")

            if endpoint_template.type_key != self.type_key:
                raise InvalidEndpointTemplateServiceType(
                    "template does not match the service type.")

            self.endpoint_templates[key] = endpoint_template
        else:
            raise InvalidEndpointTemplateInterface(
                endpoint_template.__class__.__module__ + "/" +
                endpoint_template.__class__.__name__ +
                " does not implement IEndpointTemplate"
            )

    def update_template(self, endpoint_template):
        """
        Update an existing template for the external API.

        :param six.text_type endpoint_template: a :obj:`IEndpointTemplate` to add to the
            :obj:`IExternalAPIMock` instance
        :raises: IndexError if the endpoint template does not already exist
        :raises: TypeError if the endpoint template does not implement
            the expected interface (IEndpointTempalte)
        """
        if IEndpointTemplate.providedBy(endpoint_template):
            key = endpoint_template.id_key

            if key not in self.endpoint_templates:
                raise EndpointTemplateDoesNotExist(
                    "Endpoint template does not exist. Unable to update. The "
                    "template must first be added before it can be updated"
                )

            if endpoint_template.type_key != self.type_key:
                raise InvalidEndpointTemplateServiceType(
                    "template does not match the service type.")

            if self.endpoint_templates[key].id_key != endpoint_template.id_key:
                raise InvalidEndpointTemplateId(
                    "template id must match the id of the template it is "
                    "updating"
                )

            self.endpoint_templates[key] = endpoint_template

        else:
            raise InvalidEndpointTemplateInterface(
                endpoint_template.__class__.__module__ + "/" +
                endpoint_template.__class__.__name__ +
                " does not implement IEndpointTemplate"
            )

    def has_template(self, template_id):
        """
        Determine whether or not this :obj:`ExternalApiStore` instance owns a
        template with the id `template_id`.
        """
        if template_id in self.endpoint_templates:
            return True

        return False

    def remove_template(self, template_id):
        """
        Remove the template for the external API.

        :param six.text_type template_id: the unique id of the endpoint template
            to be removed.
        :raises: IndexError if the template does not exist
        """
        # Disable (remove) the templates for all tenants
        for tenant_id in self.endpoints_for_tenants.keys():
            try:
                self.disable_endpoint_for_tenant(tenant_id, template_id)
            except EndpointTemplateDisabledForTenant:
                # Ignore if the template is not available for the tenant
                pass

        # Remove the template
        if template_id in self.endpoint_templates:
            del self.endpoint_templates[template_id]
            return

        # Tell the caller if the template did not exist in case the caller
        # needs to generate error messages
        raise InvalidEndpointTemplateId(
            "template (" + template_id + ") does not exist"
        )

    def catalog_entries(self, tenant_id):
        """
        List catalog entries for the Example API.

        :param six.text_type tenant_id: the semi-internal tenant ID generated
            by Mimic.
        :returns: list of Service Catalog Entry objects
        :rtype: list
        """
        return [
            Entry(
                tenant_id,
                self.type_key,
                self.name_key,
                self.list_tenant_endpoints(tenant_id))
        ]

    def uri_for_service(self, region, service_id):
        """
        Return the URI for the service in the given region.

        .. note:: This only returns the public URL at present to match
            the rest of Mimic's implementation. Supporting multiple
            URL types (public vs snet vs admin) is left for another
            feature addition.

        :param six.text_type service_id: the ID of the service.
        :returns: URL to use if it exists, otherwise an empty string
        :rtype: six.text_type
        """
        # key doesn't matter, region is the only interesting thing
        for _, endpoint_template in self.endpoint_templates.items():
            if endpoint_template.region_key == region or region == '':
                # since Mimic only utilizes the public URL
                return endpoint_template.public_url

        raise IndexError(
            "region '" + region + "' is not supported as an external API"
        )
