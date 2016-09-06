"""
Errors for the Identity Models
"""


class EndpointTemplateException(Exception):
    """
    Parent for all Identity Endpoint Template Exceptions
    """


class InvalidEndpointTemplateException(EndpointTemplateException):
    """
    Parent for all Endpoint Template Validation Exceptions.
    """


class InvalidEndpointTemplateInterface(InvalidEndpointTemplateException):
    """
    :obj: does not implement the required interface, :obj:IEndpointTemplate.
    """


class InvalidEndpointTemplateMissingKey(InvalidEndpointTemplateException):
    """
    :obj: is missing a required field.
    """


class InvalidEndpointTemplateId(InvalidEndpointTemplateException):
    """
    :obj: has an invalid endpoint template id value.
    """


class InvalidEndpointTemplateServiceType(InvalidEndpointTemplateException):
    """
    :obj: has an invalid service type or the service type does not match
    the API it is being submitted for.
    """


class EndpointTemplateDisabledForTenant(EndpointTemplateException):
    """
    Specified endpoint template is disabled for the tenant.
    """


class EndpointTemplateExistenceException(EndpointTemplateException):
    """
    Parent of template existence exceptions.
    """


class EndpointTemplateAlreadyExists(EndpointTemplateExistenceException):
    """
    Endpoint Template already exists.
    """


class EndpointTemplateDoesNotExist(EndpointTemplateExistenceException):
    """
    Endpoint Template does not exist.
    """
