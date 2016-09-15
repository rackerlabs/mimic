"""
Utility Decorators for RESTful APIs
"""

from functools import wraps
import inspect
import json

from mimic.model.identity_objects import unauthorized


def require_auth_token(func):
    """
    Decorator to require the presence of a valid Auth Token
    via the X-Auth-Token header field in a request.

    .. note:: Expects to be called on an object's method for handling
        a request.
    .. note:: A request handler can use the keyword parameter `auth_token`
        to receive the Auth Token extracted from the headers.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        request = args[1]

        x_auth_token = request.getHeader(b"x-auth-token")
        if x_auth_token is None:
            return json.dumps(unauthorized("Authentication required", request))

        # function may optionally want the auth token, check its parameters
        # to see if it is in the arg spec
        handler_parameters = inspect.getargspec(func)
        handler_kwargs = handler_parameters[0]
        if 'auth_token' in handler_kwargs:
            kwargs['auth_token'] = x_auth_token.decode('utf-8')

        return func(*args, **kwargs)

    return wrapper
