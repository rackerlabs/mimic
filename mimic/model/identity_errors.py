"""
Errors for the Identity Models
"""


class EndpointTemplateException(Exception):
    """
    Parent for all Identity Endpoint Template Exceptions
    """
    pass


class InvalidEndpointTemplateException(EndpointTemplateException):
    """
    Parent for all Endpoint Template Validation Exceptions.
    """
    pass


class InvalidEndpointTemplateInterface(InvalidEndpointTemplateException):
    """
    :obj: does not implement the required interface, :obj:IEndpointTemplate.
    """
    pass


class InvalidEndpointTemplateMissingKey(InvalidEndpointTemplateException):
    """
    :obj: is missing a required field.
    """
    pass


class InvalidEndpointTemplateId(InvalidEndpointTemplateException):
    """
    :obj: has an invalid endpoint template id value.
    """
    pass


class InvalidEndpointTemplateServiceType(InvalidEndpointTemplateException):
    """
    :obj: has an invalid service type or the service type does not match
    the API it is being submitted for.
    """
    pass


class EndpointTemplateDisabledForTenant(EndpointTemplateException):
    """
    Specified endpoint template is disabled for the tenant.
    """
    pass


class EndpointTemplateExistenceException(EndpointTemplateException):
    """
    Parent of template existence exceptions.
    """
    pass


class EndpointTemplateAlreadyExists(EndpointTemplateExistenceException):
    """
    Endpoint Template already exists.
    """
    pass


class EndpointTemplateDoesNotExist(EndpointTemplateExistenceException):
    """
    Endpoint Template does not exist.
    """
    pass
