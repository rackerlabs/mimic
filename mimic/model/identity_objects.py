"""
Model objects for the Identity mimic.
"""

from __future__ import absolute_import, division, unicode_literals

from zope.interface import implementer

from twisted.plugin import IPlugin
from twisted.web.http import BAD_REQUEST, FORBIDDEN, NOT_FOUND

from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.imimic import IExternalAPIMock, IEndpointTemplate


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


def not_found(message, request):
    """
    Return a 404 error body associated with a Identity not found error.
    Also sets the response code on the request.

    :param str message: The message to include in the bad request body.
    :param request: The request on which to set the response code.

    :return: dictionary representing the error body.
    """
    return _identity_error_message("itemNotFound", message, NOT_FOUND, request)


def forbidden(message, request):
    """
    Return a 403 error body associated with a Identity forbidden error.
    Also sets the response code on the request.

    :param str message: The message to include in the bad request body.
    :param request: The request on which to set the response code.

    :return: dictionary representing the error body.
    """
    return _identity_error_message("forbidden", message, FORBIDDEN, request)


@implementer(IExternalAPIMock, IPlugin)
class ExternalApiStore(object):
    """
    A :obj:`ExternalApiStore` is an object which provides the functionality to list
    an API that is external to Mimic in the service catalog provided by Mimic.
    """

    def __init__(self, service_uuid, service_name, service_type, api_templates=[]):
        """
        Initialize an :obj:`ExternalApiStore` for a given service.

        :param text_type service_uuid: unique identifier for the API
        :param text_type service_name: name of the service being provided,
            f.e Cloud Files, Identity
        :param text_type service_type: type of the service being provided,
            f.e object-store, auth
        :param iterable api_templates: iterable of templates to add during
            initialization
        """
        self.name_key = service_name
        self.type_key = service_type
        self.uuid_key = service_uuid

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

        :param text_type tenant_id: tenant id to operate on
        :returns: an iterable of the endpoints available for the specified
            tenant id
        """
        # List of template IDs that should be provided for a template
        # regardless of the enabled/disabled status of the template itself
        tenant_specific_templates = []
        if tenant_id in self.endpoints_for_tenants:
            for template_id in self.endpoints_for_tenants[tenant_id]:
                tenant_specific_templates.append(template_id)

        # provide an End-point Entry for every template that is either
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
                        endpoint_template.versionId,
                        external=True,
                        complete_url=endpoint_template.publicURL
                    )
                )
        return endpoints

    def enable_endpoint_for_tenant(self, tenant_id, template_id):
        """
        Enable an endpoint for a specific tenant.

        :param text_type tenant_id: tenant id to operate on
        :param text_type template_id: endpoint template id to enable
        :raises: ValueError if the template id is not found
        """
        if tenant_id not in self.endpoints_for_tenants:
            self.endpoints_for_tenants[tenant_id] = []

        for key, endpoint_template in self.endpoint_templates.items():
            if endpoint_template.id_key == template_id:
                self.endpoints_for_tenants[tenant_id].append(template_id)
                return

        raise ValueError(template_id + " is not valid")

    def disable_endpoint_for_tenant(self, tenant_id, template_id):
        """
        Disable an endpoint for a specific tenant.

        :param text_type tenant_id: tenant id to operate on
        :param text_type template_id: endpoint template id to disable
        :raises: ValueError if template is not enabled for the tenant
        """
        if tenant_id in self.endpoints_for_tenants:
            if template_id in self.endpoints_for_tenants[tenant_id]:
                self.endpoints_for_tenants[tenant_id].remove(template_id)
                return

        # Tell the caller if the template did not exist in case the caller
        # needs to generate error messages
        raise ValueError(
            "template (" + template_id + ") not enabled for tenant id ("
            + tenant_id + ")"
        )

    def list_templates(self):
        """
        List the available templates.

        :returns: an iterable of the endpoint templates
        """
        return self.endpoint_templates.values()

    def add_template(self, endpoint_template):
        """
        Add a new template for the external API.

        :param unicode templates: a :obj:`IEndpointTemplate` to add to the
            :obj:`IExternalAPIMock` instance
        :raises: ValueError if the endpoint template has already been added
        :raises: TypeError if the endpoint template does not implement
            the expected interface (IEndpointTempalte)
        """
        if IEndpointTemplate.providedBy(endpoint_template):
            key = endpoint_template.id_key

            if key in self.endpoint_templates:
                raise ValueError(key + " already exists. Please call update.")

            self.endpoint_templates[key] = endpoint_template
        else:
            raise TypeError(
                endpoint_template.__class__.__module__ + "/" +
                endpoint_template.__class__.__name__ +
                " does not implement IEndpointTemplate"
            )

    def update_template(self, endpoint_template):
        """
        Update an existing template for the external API.

        :param unicode templates: a :obj:`IEndpointTemplate` to add to the
            :obj:`IExternalAPIMock` instance
        :raises: IndexError if the endpoint template does not already exist
        :raises: TypeError if the endpoint template does not implement
            the expected interface (IEndpointTempalte)
        """
        if IEndpointTemplate.providedBy(endpoint_template):
            key = endpoint_template.id_key

            if key not in self.endpoint_templates:
                raise IndexError(
                    "End-point template does not exist. Unable to update. The "
                    "template must first be added before it can be updated"
                )

            self.endpoint_templates[key] = endpoint_template

        else:
            raise TypeError(
                endpoint_template.__class__.__module__ + "/" +
                endpoint_template.__class__.__name__ +
                " does not implement IEndpointTemplate"
            )

    def remove_template(self, template_id):
        """
        Remove the template for the external API.

        :param unicode template_id: the unique id of the endpoint template
            to be removed.
        :raises: IndexError if the template does not exist
        """
        # Disable (remove) the templates for all tenants
        for tenant_id in self.endpoints_for_tenants.keys():
            try:
                self.disable_endpoint_for_tenant(tenant_id, template_id)
            except ValueError:
                # Ignore if the template is not available for the tenant
                pass

        # Remove the template
        if template_id in self.endpoint_templates:
            del self.endpoint_templates[template_id]
            return

        # Tell the caller if the template did not exist in case the caller
        # needs to generate error messages
        raise IndexError(
            "template (" + template_id + ") does not exist"
        )

    def catalog_entries(self, tenant_id):
        """
        List catalog entries for the Example API.

        :returns: list of Service Catalog Entry objects
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

        Note: This only returns the publicURL at present to match
            the rest of Mimic's implementation. Supporting multiple
            URL types (public vs snet vs admin) is left for another
            feature addition.

        :returns: URL to use if it exists, otherwise an empty string
        """
        # key doesn't matter, region is the only interesting thing
        for _, endpoint_template in self.endpoint_templates.items():
            if endpoint_template.region_key == region or region == '':
                # since Mimic only utilizes the public URL
                return endpoint_template.publicURL

        raise IndexError(
            "region '" + region + "' is not supported as an external API"
        )
